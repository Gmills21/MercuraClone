
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.n8n_service import N8nService
from app.routes.erp_export import send_quote_to_erp_webhook
from app.routes.webhooks import process_email_webhook
from app.models import WebhookPayload, InboundEmail
from datetime import datetime

# Mock settings
@pytest.fixture
def mock_settings():
    with patch("app.services.n8n_service.settings") as mock:
        mock.n8n_enabled = True
        mock.n8n_webhook_url = "http://fake-n8n.com/webhook"
        mock.n8n_api_key = "fake-key"
        yield mock

# Test N8nService
@pytest.mark.asyncio
async def test_n8n_service_trigger(mock_settings):
    service = N8nService()
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        
        success = await service.trigger_webhook("test_event", {"foo": "bar"})
        
        assert success is True
        mock_post.assert_awaited_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "http://fake-n8n.com/webhook"
        assert kwargs["json"] == {"foo": "bar"}
        assert kwargs["headers"]["X-Event-Type"] == "test_event"
        assert kwargs["headers"]["X-API-Key"] == "fake-key"

# Test ERP Export Logic
@pytest.mark.asyncio
async def test_erp_export_calls_n8n():
    with patch("app.routes.erp_export.settings") as mock_settings:
        mock_settings.n8n_enabled = True
        
        with patch("app.routes.erp_export.n8n_service.trigger_webhook", new_callable=AsyncMock) as mock_trigger, \
             patch("app.routes.erp_export.get_erp_exporter") as mock_exporter, \
             patch("app.routes.erp_export.capture_event") as mock_capture:
            
            # Mock exporter return
            mock_exporter.return_value.export_quote.return_value = {"id": "q1", "total": 100}
            mock_trigger.return_value = True
            
            response = await send_quote_to_erp_webhook("q1", "generic")
            
            assert response["status"] == "success"
            mock_trigger.assert_awaited_once()
            call_args = mock_trigger.call_args
            assert call_args[1]["event_type"] == "erp_export"
            assert call_args[1]["payload"]["quote_id"] == "q1"

# Test Webhook Forwarding Logic
@pytest.mark.asyncio
async def test_webhook_forwarding():
    # Mock settings in webhooks.py
    with patch("app.routes.webhooks.settings") as mock_settings:
        mock_settings.n8n_enabled = True
        
        with patch("app.routes.webhooks.n8n_service.trigger_webhook", new_callable=AsyncMock) as mock_trigger, \
             patch("app.routes.webhooks.db.get_user_by_email", new_callable=AsyncMock) as mock_get_user:
             
            # Setup authorized user
            mock_get_user.return_value = {
                "id": "user1", 
                "is_active": True, 
                "emails_processed_today": 0, 
                "email_quota_per_day": 100
            }
            mock_trigger.return_value = True
            
            payload = WebhookPayload(
                provider="sendgrid",
                sender="test@example.com",
                recipient="me@mercura.io",
                subject="Test RFQ",
                body_plain="Please quote attached",
                attachments=[],
                message_id="msg123"
            )
            
            result = await process_email_webhook(payload)
            
            assert result["status"] == "forwarded_to_n8n"
            mock_trigger.assert_awaited_once()
            call_args = mock_trigger.call_args
            assert call_args[0][0] == "inbound_email"
            assert call_args[0][1]["sender"] == "test@example.com"
