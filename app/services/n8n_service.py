
"""
Service for interacting with n8n workflows.
"""
import httpx
import logging
from typing import Dict, Any, Optional
from app.config import settings
from app.utils.resilience import (
    CircuitBreaker,
    with_retry,
    RetryConfig,
    CircuitBreakerOpen
)
from app.errors import (
    AppError,
    ErrorCategory,
    ErrorSeverity,
    MercuraException,
    classify_exception
)

logger = logging.getLogger(__name__)

# Retry configuration for n8n webhooks
N8N_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=2.0,
    max_delay=30.0,
    retryable_exceptions=[
        httpx.TimeoutException,
        httpx.ConnectError,
        httpx.NetworkError,
        httpx.HTTPStatusError
    ]
)

class N8nService:
    def __init__(self):
        self.webhook_url = settings.n8n_webhook_url
        self.api_key = settings.n8n_api_key
        self.enabled = settings.n8n_enabled
        self.circuit_breaker = CircuitBreaker("n8n")
        self.timeout_seconds = 30.0

    async def trigger_webhook(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """
        Trigger an n8n webhook with the given payload.
        
        Args:
            event_type: Type of event (e.g., "erp_export", "quote_sent", "quote_completed")
            payload: Data to send
            
        Returns:
            bool: True if successful
            
        Raises:
            MercuraException: If the webhook call fails
        """
        # Check configuration
        if not self.enabled:
             # If intentionally disabled, we might want to just return False or raise a specific error.
             # Given erp_export checks enabled status separately, if we reach here, it might be unexpected.
             # But for robustness, we'll log and return False if specifically disabled, 
             # preventing an error if called accidentally.
             logger.warning("n8n integration is disabled")
             return False

        if not self.webhook_url:
            raise MercuraException(
                AppError(
                    category=ErrorCategory.CONFIGURATION_ERROR,
                    code="N8N_NOT_CONFIGURED",
                    message="n8n Integration is enabled but Webhook URL is missing.",
                    severity=ErrorSeverity.ERROR,
                    http_status=500,
                    retryable=False,
                    suggested_action="Configure N8N_WEBHOOK_URL in settings."
                )
            )
        
        # Check circuit breaker
        if self.circuit_breaker.is_open:
            raise MercuraException(
                AppError(
                    category=ErrorCategory.INTERNAL_ERROR,
                    code="N8N_SERVICE_UNAVAILABLE",
                    message="n8n service is temporarily unavailable (Circuit Breaker Open).",
                    severity=ErrorSeverity.WARNING,
                    http_status=503,
                    retryable=True
                )
            )

        headers = {
            "Content-Type": "application/json",
            "X-Event-Type": event_type
        }
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        @self.circuit_breaker.protect
        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                logger.info(f"Successfully triggered n8n webhook for event: {event_type}")
                return True
        
        try:
            # We wrap the protected call in with_retry
            return await with_retry(
                _make_request, 
                config=N8N_RETRY_CONFIG
            )
        except CircuitBreakerOpen as e:
            raise MercuraException(
                AppError(
                    category=ErrorCategory.INTERNAL_ERROR,
                    code="N8N_CIRCUIT_OPEN",
                    message="n8n service is unavailable due to repeated failures.",
                    severity=ErrorSeverity.WARNING,
                    http_status=503,
                    retryable=True
                ),
                original_exception=e
            )
        except Exception as e:
            logger.error(f"Failed to trigger n8n webhook after retries: {e}")
            # Classify and wrapping
            app_error = classify_exception(e)
            app_error.category = ErrorCategory.INTERNAL_ERROR # Force category for n8n to be generic internal/external error
            app_error.message = f"Failed to trigger n8n webhook: {str(e)}"
            raise MercuraException(app_error, original_exception=e)

n8n_service = N8nService()
