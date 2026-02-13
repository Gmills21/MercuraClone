"""
Email Service for sending quotes and notifications.
Simple, zero-config setup that "just works".
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import base64

# Try to import email libraries
try:
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

from app.config import settings
from app.database_sqlite import get_quote_with_items, get_organization


@dataclass
class EmailAttachment:
    """Email attachment data."""
    filename: str
    content: bytes
    content_type: str = "application/pdf"


@dataclass
class EmailMessage:
    """Email message data."""
    to_email: str
    to_name: Optional[str] = None
    subject: str = ""
    body_text: str = ""
    body_html: Optional[str] = None
    attachments: Optional[List[EmailAttachment]] = None
    from_name: Optional[str] = None
    from_email: Optional[str] = None


class EmailService:
    """
    Service for sending emails with quotes and notifications.
    
    Supports:
    - SMTP (any provider: Gmail, Outlook, SendGrid, etc.)
    - Simple template system
    - PDF attachments
    """
    
    def __init__(self):
        if not EMAIL_AVAILABLE:
            raise RuntimeError("Email service requires Python email libraries")
        
        # Get SMTP config from settings or env
        self.smtp_host = getattr(settings, 'smtp_host', None) or "smtp.gmail.com"
        self.smtp_port = getattr(settings, 'smtp_port', None) or 587
        self.smtp_username = getattr(settings, 'smtp_username', None) or ""
        self.smtp_password = getattr(settings, 'smtp_password', None) or ""
        self.default_from = getattr(settings, 'smtp_from', None) or self.smtp_username
        self.default_from_name = getattr(settings, 'smtp_from_name', None) or "Mercura"
        
        self.enabled = all([self.smtp_host, self.smtp_username, self.smtp_password])
    
    def send_email(self, message: EmailMessage) -> Dict[str, Any]:
        """
        Send an email with optional attachments.
        
        Args:
            message: EmailMessage with all email data
            
        Returns:
            Dict with success status and message
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "Email not configured. Set SMTP credentials in settings."
            }
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = message.subject
            msg['From'] = f"{message.from_name or self.default_from_name} <{message.from_email or self.default_from}>"
            msg['To'] = f"{message.to_name or ''} <{message.to_email}>".strip()
            
            # Add body parts
            if message.body_text:
                msg.attach(MIMEText(message.body_text, 'plain'))
            
            if message.body_html:
                msg.attach(MIMEText(message.body_html, 'html'))
            
            # Add attachments
            if message.attachments:
                for attachment in message.attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.content)
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{attachment.filename}"'
                    )
                    msg.attach(part)
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return {
                "success": True,
                "message": f"Email sent to {message.to_email}",
                "sent_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_quote(
        self,
        quote_id: str,
        to_email: str,
        to_name: Optional[str] = None,
        message: Optional[str] = None,
        pdf_bytes: Optional[bytes] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a quote email with PDF attachment.
        
        Args:
            quote_id: Quote ID to send
            to_email: Recipient email
            to_name: Recipient name
            message: Custom message (optional)
            pdf_bytes: Pre-generated PDF (optional)
            organization_id: For org-specific branding
            
        Returns:
            Dict with success status
        """
        # Fetch quote data
        quote = get_quote_with_items(quote_id, organization_id)
        if not quote:
            return {"success": False, "error": "Quote not found"}
        
        # Get org info
        org_name = self.default_from_name
        if organization_id:
            org = get_organization(organization_id)
            if org:
                org_name = org.get('name', org_name)
        
        quote_number = quote.get('quote_number', 'N/A')
        customer = quote.get('customers', {})
        customer_name = to_name or customer.get('name') or customer.get('company_name') or 'Valued Customer'
        
        # Build email content
        subject = f"Quote #{quote_number} from {org_name}"
        
        # Plain text body
        text_body = self._build_quote_text(
            quote_number=quote_number,
            customer_name=customer_name,
            message=message,
            org_name=org_name,
            quote_total=quote.get('total', 0)
        )
        
        # HTML body
        html_body = self._build_quote_html(
            quote_number=quote_number,
            customer_name=customer_name,
            message=message,
            org_name=org_name,
            quote_total=quote.get('total', 0),
            quote=quote
        )
        
        # Prepare attachments
        attachments = []
        if pdf_bytes:
            attachments.append(EmailAttachment(
                filename=f"Quote_{quote_number}.pdf",
                content=pdf_bytes,
                content_type="application/pdf"
            ))
        
        # Send email
        email_msg = EmailMessage(
            to_email=to_email,
            to_name=customer_name,
            subject=subject,
            body_text=text_body,
            body_html=html_body,
            attachments=attachments,
            from_name=org_name
        )
        
        return self.send_email(email_msg)
    
    def _build_quote_text(
        self,
        quote_number: str,
        customer_name: str,
        message: Optional[str],
        org_name: str,
        quote_total: float
    ) -> str:
        """Build plain text email body for quote."""
        lines = [
            f"Hi {customer_name},",
            "",
            f"Thank you for your interest in {org_name}. Please find your quote attached.",
            "",
            f"Quote Number: {quote_number}",
            f"Total Amount: ${float(quote_total):,.2f}",
            "",
        ]
        
        if message:
            lines.extend([message, ""])
        
        lines.extend([
            "If you have any questions or would like to proceed with this quote, please reply to this email.",
            "",
            "Best regards,",
            f"The {org_name} Team"
        ])
        
        return "\n".join(lines)
    
    def _build_quote_html(
        self,
        quote_number: str,
        customer_name: str,
        message: Optional[str],
        org_name: str,
        quote_total: float,
        quote: Dict[str, Any]
    ) -> str:
        """Build HTML email body for quote."""
        items_html = ""
        for item in quote.get('items', [])[:5]:  # Show first 5 items
            desc = item.get('description') or item.get('product_name') or 'Item'
            qty = item.get('quantity', 1)
            price = float(item.get('unit_price', 0))
            items_html += f"<li>{desc} (Qty: {qty}) - ${price:,.2f} each</li>"
        
        if len(quote.get('items', [])) > 5:
            items_html += f"<li><em>... and {len(quote['items']) - 5} more items</em></li>"
        
        message_html = f"<p style='color: #374151;'>{message}</p>" if message else ""
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f3f4f6;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 40px 20px;">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #2563eb, #1d4ed8); padding: 30px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">{org_name}</h1>
                                    <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 14px;">Quote #{quote_number}</p>
                                </td>
                            </tr>
                            
                            <!-- Body -->
                            <tr>
                                <td style="padding: 40px 30px;">
                                    <p style="color: #111827; font-size: 16px; margin: 0 0 20px 0;">Hi {customer_name},</p>
                                    
                                    <p style="color: #374151; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                                        Thank you for your interest in working with us. Please find your detailed quote attached to this email.
                                    </p>
                                    
                                    {message_html}
                                    
                                    <!-- Quote Summary -->
                                    <div style="background-color: #f9fafb; border-radius: 6px; padding: 20px; margin: 25px 0;">
                                        <h3 style="color: #111827; font-size: 14px; margin: 0 0 15px 0; text-transform: uppercase; letter-spacing: 0.5px;">Quote Summary</h3>
                                        <ul style="color: #374151; font-size: 14px; line-height: 1.6; margin: 0; padding-left: 20px;">
                                            {items_html}
                                        </ul>
                                        <div style="border-top: 2px solid #e5e7eb; margin-top: 15px; padding-top: 15px;">
                                            <p style="color: #111827; font-size: 18px; font-weight: 600; margin: 0; text-align: right;">
                                                Total: ${float(quote_total):,.2f}
                                            </p>
                                        </div>
                                    </div>
                                    
                                    <!-- CTA -->
                                    <div style="text-align: center; margin: 30px 0;">
                                        <a href="mailto:{self.default_from}?subject=RE: Quote #{quote_number}" style="display: inline-block; background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 6px; font-size: 15px; font-weight: 500;">
                                            Reply to Accept Quote
                                        </a>
                                    </div>
                                    
                                    <p style="color: #6b7280; font-size: 14px; line-height: 1.5; margin: 20px 0 0 0;">
                                        If you have any questions about this quote, simply reply to this email and our team will be happy to help.
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #f9fafb; padding: 20px 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                                    <p style="color: #6b7280; font-size: 13px; margin: 0;">
                                        Sent with ❤️ from {org_name}
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
    
    def get_status(self) -> Dict[str, Any]:
        """Get email service status."""
        return {
            "enabled": self.enabled,
            "configured": self.enabled,
            "smtp_host": self.smtp_host if self.enabled else None,
            "from_email": self.default_from if self.enabled else None,
            "message": "Email ready" if self.enabled else "SMTP not configured"
        }


# Global instance
email_service: Optional[EmailService] = None
if EMAIL_AVAILABLE:
    try:
        email_service = EmailService()
    except Exception as e:
        print(f"Failed to initialize email service: {e}")
