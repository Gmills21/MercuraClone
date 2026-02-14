"""
Paddle Integration Service for B2B Subscription Management.
Handles subscription creation, updates, webhooks, and billing portal.
"""

import os
import logging
import hmac
import hashlib
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import httpx
from app.config import settings
from app.utils.resilience import (
    CircuitBreaker,
    with_retry,
    RetryConfig,
    with_timeout,
    TimeoutError,
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

# Retry configuration for Paddle API calls
PADDLE_RETRY_CONFIG = RetryConfig(
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


class PaddleService:
    """Service for interacting with Paddle API."""
    
    def __init__(self):
        """Initialize Paddle service with API credentials."""
        self.vendor_id = settings.paddle_vendor_id or os.getenv("PADDLE_VENDOR_ID")
        self.vendor_auth_code = settings.paddle_api_key or os.getenv("PADDLE_API_KEY")
        self.webhook_secret = settings.paddle_webhook_secret or os.getenv("PADDLE_WEBHOOK_SECRET")
        self.sandbox = settings.paddle_sandbox or os.getenv("PADDLE_SANDBOX", "true").lower() == "true"
        
        # Paddle API endpoints
        if self.sandbox:
            self.api_url = "https://sandbox-api.paddle.com"
            self.checkout_url = "https://sandbox-checkout.paddle.com"
        else:
            self.api_url = "https://api.paddle.com"
            self.checkout_url = "https://checkout.paddle.com"
        
        self.enabled = bool(self.vendor_id and self.vendor_auth_code)
        if not self.enabled:
            logger.warning("Paddle credentials not configured. Billing features will be disabled.")
        
        # Initialize circuit breaker for resilience
        self.circuit_breaker = CircuitBreaker("paddle")
        self.timeout_seconds = 30.0

    
    async def create_checkout_session(
        self,
        plan_id: str,
        seats: int,
        customer_email: str,
        customer_name: Optional[str] = None,
        success_url: str = "",
        cancel_url: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a Paddle checkout session for subscription.
        
        Args:
            plan_id: Paddle product/plan ID
            seats: Number of seats to purchase
            customer_email: Customer email
            customer_name: Customer name (optional)
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if checkout is canceled
            metadata: Additional metadata to attach
            
        Returns:
            Dict with checkout_url and session_id
        """
        if not self.enabled:
            raise MercuraException(
                AppError(
                    category=ErrorCategory.BILLING_ERROR,
                    code="BILLING_NOT_CONFIGURED",
                    message="Billing service is not configured. Please contact support to enable billing.",
                    severity=ErrorSeverity.ERROR,
                    http_status=400,
                    retryable=False,
                    suggested_action="Contact your administrator to configure Paddle billing integration."
                )
            )
        
        # Check circuit breaker
        if self.circuit_breaker.is_open:
            raise CircuitBreakerOpen("paddle", 300)
        
        @self.circuit_breaker.protect
        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                payload = {
                    "vendor_id": self.vendor_id,
                    "vendor_auth_code": self.vendor_auth_code,
                    "product_id": plan_id,
                    "quantity": seats,
                    "customer_email": customer_email,
                    "passthrough": json.dumps(metadata or {}),
                    "success_url": success_url,
                    "cancel_url": cancel_url,
                }
                
                if customer_name:
                    payload["customer_name"] = customer_name
                
                response = await client.post(
                    f"{self.api_url}/2.0/product/generate_pay_link",
                    data=payload
                )
                response.raise_for_status()
                
                data = response.json()
                if not data.get("success"):
                    raise ValueError(f"Paddle API error: {data.get('error', {}).get('message')}")
                
                return {
                    "checkout_url": data["response"]["url"],
                    "session_id": data["response"].get("id", "")
                }
        
        try:
            return await with_retry(_make_request, config=PADDLE_RETRY_CONFIG)
        except CircuitBreakerOpen as e:
            logger.error(f"Paddle circuit breaker open: {e}")
            raise MercuraException(
                AppError(
                    category=ErrorCategory.BILLING_ERROR,
                    code="BILLING_SERVICE_UNAVAILABLE",
                    message="Billing service is temporarily unavailable. Please try again in a few minutes.",
                    severity=ErrorSeverity.WARNING,
                    http_status=503,
                    retryable=True,
                    retry_after_seconds=300,
                    suggested_action="Wait a few minutes and try again. If the issue persists, contact support."
                ),
                original_exception=e
            )
        except Exception as e:
            logger.error(f"Error creating Paddle checkout session: {e}")
            app_error = classify_exception(e)
            app_error.category = ErrorCategory.BILLING_ERROR
            raise MercuraException(app_error, original_exception=e)
    
    async def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """
        Get subscription details from Paddle.
        
        Args:
            subscription_id: Paddle subscription ID
            
        Returns:
            Subscription data or None
        """
        if not self.enabled:
            return None
        
        if self.circuit_breaker.is_open:
            logger.warning("Paddle circuit breaker open, skipping get_subscription")
            return None
        
        @self.circuit_breaker.protect
        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.api_url}/2.0/subscription/users",
                    data={
                        "vendor_id": self.vendor_id,
                        "vendor_auth_code": self.vendor_auth_code,
                        "subscription_id": subscription_id
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                if data.get("success") and data.get("response"):
                    return data["response"][0] if data["response"] else None
                return None
        
        try:
            return await with_retry(_make_request, config=PADDLE_RETRY_CONFIG)
        except Exception as e:
            logger.error(f"Error fetching Paddle subscription: {e}")
            return None
    
    async def update_subscription(
        self,
        subscription_id: str,
        quantity: Optional[int] = None,
        plan_id: Optional[str] = None,
        pause: Optional[bool] = None
    ) -> bool:
        """
        Update a Paddle subscription.
        
        Args:
            subscription_id: Paddle subscription ID
            quantity: New quantity (seats)
            plan_id: New plan ID
            pause: Whether to pause the subscription
            
        Returns:
            True if successful
        """
        if not self.enabled:
            return False
        
        if self.circuit_breaker.is_open:
            logger.warning("Paddle circuit breaker open, skipping update_subscription")
            return False
        
        @self.circuit_breaker.protect
        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                payload = {
                    "vendor_id": self.vendor_id,
                    "vendor_auth_code": self.vendor_auth_code,
                    "subscription_id": subscription_id
                }
                
                if quantity is not None:
                    payload["quantity"] = quantity
                if plan_id is not None:
                    payload["plan_id"] = plan_id
                if pause is not None:
                    payload["pause"] = pause
                
                response = await client.post(
                    f"{self.api_url}/2.0/subscription/users/update",
                    data=payload
                )
                response.raise_for_status()
                
                data = response.json()
                return data.get("success", False)
        
        try:
            return await with_retry(_make_request, config=PADDLE_RETRY_CONFIG)
        except Exception as e:
            logger.error(f"Error updating Paddle subscription: {e}")
            return False
    
    async def cancel_subscription(self, subscription_id: str) -> bool:
        """
        Cancel a Paddle subscription.
        
        Args:
            subscription_id: Paddle subscription ID
            
        Returns:
            True if successful
        """
        if not self.enabled:
            return False
        
        if self.circuit_breaker.is_open:
            logger.warning("Paddle circuit breaker open, skipping cancel_subscription")
            return False
        
        @self.circuit_breaker.protect
        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.api_url}/2.0/subscription/users_cancel",
                    data={
                        "vendor_id": self.vendor_id,
                        "vendor_auth_code": self.vendor_auth_code,
                        "subscription_id": subscription_id
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                return data.get("success", False)
        
        try:
            return await with_retry(_make_request, config=PADDLE_RETRY_CONFIG)
        except Exception as e:
            logger.error(f"Error canceling Paddle subscription: {e}")
            return False
    
    async def get_invoices(self, subscription_id: str) -> List[Dict[str, Any]]:
        """
        Get invoices for a subscription.
        
        Args:
            subscription_id: Paddle subscription ID
            
        Returns:
            List of invoice data
        """
        if not self.enabled:
            return []
        
        if self.circuit_breaker.is_open:
            logger.warning("Paddle circuit breaker open, skipping get_invoices")
            return []
        
        @self.circuit_breaker.protect
        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.api_url}/2.0/subscription/payments",
                    data={
                        "vendor_id": self.vendor_id,
                        "vendor_auth_code": self.vendor_auth_code,
                        "subscription_id": subscription_id
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                if data.get("success"):
                    return data.get("response", [])
                return []
        
        try:
            return await with_retry(_make_request, config=PADDLE_RETRY_CONFIG)
        except Exception as e:
            logger.error(f"Error fetching Paddle invoices: {e}")
            return []
    
    def verify_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
        """
        Verify Paddle webhook signature.
        
        Args:
            payload: Webhook payload
            signature: Signature from Paddle
            
        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            logger.warning("Paddle webhook secret not configured")
            return False
        
        try:
            # Sort payload keys
            sorted_payload = dict(sorted(payload.items()))
            
            # Serialize to string
            serialized = ""
            for key, value in sorted_payload.items():
                if key != "p_signature":
                    serialized += f"{key}={value}"
            
            # Calculate HMAC
            calculated_signature = hmac.new(
                self.webhook_secret.encode(),
                serialized.encode(),
                hashlib.sha1
            ).hexdigest()
            
            return hmac.compare_digest(calculated_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying Paddle webhook: {e}")
            return False
    
    async def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Paddle webhook event.
        
        Args:
            payload: Webhook payload
            
        Returns:
            Processed event data
        """
        alert_name = payload.get("alert_name")
        
        event_data = {
            "type": alert_name,
            "subscription_id": payload.get("subscription_id"),
            "customer_id": payload.get("user_id"),
            "status": payload.get("status"),
            "quantity": payload.get("quantity"),
            "next_bill_date": payload.get("next_bill_date"),
            "cancellation_effective_date": payload.get("cancellation_effective_date"),
            "passthrough": json.loads(payload.get("passthrough", "{}")),
            "raw_payload": payload
        }
        
        # Handle different event types
        if alert_name == "subscription_created":
            event_data["action"] = "created"
        elif alert_name == "subscription_updated":
            event_data["action"] = "updated"
        elif alert_name == "subscription_cancelled":
            event_data["action"] = "cancelled"
        elif alert_name == "subscription_payment_succeeded":
            event_data["action"] = "payment_succeeded"
            event_data["amount"] = payload.get("sale_gross")
            event_data["currency"] = payload.get("currency")
            event_data["receipt_url"] = payload.get("receipt_url")
        elif alert_name == "subscription_payment_failed":
            event_data["action"] = "payment_failed"
        
        return event_data
    
    async def create_billing_portal_session(
        self,
        customer_id: str,
        return_url: str
    ) -> Optional[str]:
        """
        Create a billing portal session for customer to manage subscription.
        Note: Paddle doesn't have a built-in portal like Stripe.
        You'll need to build your own UI or use Paddle's update/cancel endpoints.
        
        Args:
            customer_id: Paddle customer ID
            return_url: URL to return to after managing subscription
            
        Returns:
            Portal URL (custom implementation needed)
        """
        # Paddle doesn't have a hosted billing portal
        # Return your custom billing page URL
        return f"{return_url}?customer_id={customer_id}"


# Global instance
paddle_service = PaddleService()
