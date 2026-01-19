"""
Email service for sending outbound emails.
Currently supports SendGrid via API.
"""

import logging
import base64
import httpx
from typing import List, Dict, Optional, Any
from app.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails."""

    def __init__(self):
        self.api_key = settings.sendgrid_api_key
        # Default sender, should be verified in SendGrid
        # Ideally this comes from settings
        self.from_email = "quotes@mercura.ai" 

    async def send_email(
        self,
        to_email: str,
        subject: str,
        content: str,
        content_type: str = "text/plain",
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Send an email via SendGrid API.
        
        attachments format:
        [
            {
                "content": "base64_encoded_content",
                "filename": "filename.ext",
                "type": "application/pdf", # or application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
                "disposition": "attachment"
            }
        ]
        """
        if not self.api_key:
            logger.warning("SendGrid API key not configured. Skipping email send.")
            # In dev, we might want to pretend it worked
            if settings.app_env == "development":
                logger.info(f"[DEV] Mock email sent to {to_email} with subject '{subject}'")
                return True
            return False

        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "personalizations": [
                {
                    "to": [{"email": to_email}]
                }
            ],
            "from": {"email": self.from_email},
            "subject": subject,
            "content": [
                {
                    "type": content_type,
                    "value": content
                }
            ]
        }

        if attachments:
            data["attachments"] = attachments

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=data)
                
            if response.status_code in (200, 201, 202):
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

email_service = EmailService()
