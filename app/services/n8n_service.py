
"""
Service for interacting with n8n workflows.
"""
import httpx
import logging
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class N8nService:
    def __init__(self):
        self.webhook_url = settings.n8n_webhook_url
        self.api_key = settings.n8n_api_key
        self.enabled = settings.n8n_enabled

    async def trigger_webhook(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """
        Trigger an n8n webhook with the given payload.
        
        Args:
            event_type: Type of event (e.g., "erp_export", "quote_sent", "quote_completed")
            payload: Data to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled or not self.webhook_url:
            logger.warning("n8n integration is disabled or not configured")
            return False

        headers = {
            "Content-Type": "application/json",
            "X-Event-Type": event_type
        }
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info(f"Successfully triggered n8n webhook for event: {event_type}")
                return True
        except Exception as e:
            logger.error(f"Failed to trigger n8n webhook: {e}")
            return False

n8n_service = N8nService()
