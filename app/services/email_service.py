"""
Email Service for sending quotes and notifications.
Supports organization-specific SMTP configuration with production-grade error handling.

Features:
- User-friendly error messages for SMTP issues
- Retry logic for transient failures
- Graceful degradation when email is unavailable
- Queue for failed sends (future enhancement)
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import base64
import socket
import ssl

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

from loguru import logger

from app.config import settings
from app.database_sqlite import get_quote_with_items, get_organization, get_email_settings
from app.errors import AppError, ErrorCategory, ErrorSeverity
from app.utils.resilience import with_retry, RetryConfig


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


@dataclass
class EmailResult:
    """Result of email send operation."""
    success: bool
    message: str
    error_code: Optional[str] = None
    retryable: bool = False
    retry_after: Optional[int] = None
    suggested_action: Optional[str] = None
    message_id: Optional[str] = None
    sent_at: Optional[datetime] = None


# Retry configuration for email sends
EMAIL_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    base_delay=2.0,
    max_delay=30.0,
    retryable_exceptions=[
        socket.timeout,
        socket.error,
        smtplib.SMTPServerDisconnected,
        smtplib.SMTPConnectError,
    ]
)


class EmailService:
    """
    Service for sending emails with quotes and notifications.
    
    Features:
    - SMTP (any provider: Gmail, Outlook, SendGrid, etc.)
    - Organization-specific configuration
    - Simple template system
    - PDF attachments
    - User-friendly error messages
    - Retry logic for transient failures
    """
    
    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_username: str = "",
        smtp_password: str = "",
        default_from: str = "",
        default_from_name: str = "Mercura",
        use_tls: bool = True
    ):
        if not EMAIL_AVAILABLE:
            raise RuntimeError("Email service requires Python email libraries")
        
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.default_from = default_from or smtp_username
        self.default_from_name = default_from_name
        self.use_tls = use_tls
        
        self.enabled = all([self.smtp_host, self.smtp_username, self.smtp_password])
        
        if not self.enabled:
            logger.warning("Email service not fully configured - some features disabled")
    
    @classmethod
    def from_organization(cls, organization_id: str) -> Optional["EmailService"]:
        """
        Create an EmailService configured for a specific organization.
        
        Args:
            organization_id: The organization ID to load settings for
            
        Returns:
            EmailService instance or None if not configured
        """
        email_settings = get_email_settings(organization_id)
        
        if not email_settings:
            return None
        
        if not email_settings.get("is_enabled"):
            return None
        
        try:
            return cls(
                smtp_host=email_settings.get("smtp_host", "smtp.gmail.com"),
                smtp_port=email_settings.get("smtp_port", 587),
                smtp_username=email_settings.get("smtp_username", ""),
                smtp_password=email_settings.get("smtp_password", ""),
                default_from=email_settings.get("from_email") or email_settings.get("smtp_username", ""),
                default_from_name=email_settings.get("from_name", "Mercura"),
                use_tls=bool(email_settings.get("use_tls", True))
            )
        except Exception as e:
            logger.error(f"Failed to create email service for org {organization_id}: {e}")
            return None
    
    def _create_error_result(
        self,
        message: str,
        error_code: str,
        retryable: bool = True,
        suggested_action: Optional[str] = None
    ) -> EmailResult:
        """Create a standardized error result."""
        return EmailResult(
            success=False,
            message=message,
            error_code=error_code,
            retryable=retryable,
            suggested_action=suggested_action or "Check your email settings and try again."
        )
    
    async def send_email(self, message: EmailMessage) -> EmailResult:
        """
        Send an email with optional attachments and user-friendly error handling.
        
        Args:
            message: EmailMessage with all email data
            
        Returns:
            EmailResult with success status and user-friendly messages
        """
        if not self.enabled:
            return self._create_error_result(
                message="Email is not configured. Please set up your SMTP settings first.",
                error_code="EMAIL_NOT_CONFIGURED",
                retryable=False,
                suggested_action="Go to Settings > Email to configure your email provider."
            )
        
        async def _send():
            """Inner send function for retry logic."""
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
            
            # Send via SMTP with timeout
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
        
        try:
            # Use retry logic for transient failures
            await with_retry(_send, config=EMAIL_RETRY_CONFIG)
            
            return EmailResult(
                success=True,
                message=f"Email sent successfully to {message.to_email}",
                sent_at=datetime.utcnow()
            )
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return self._create_error_result(
                message="Email authentication failed. Please check your email username and password.",
                error_code="SMTP_AUTH_FAILED",
                retryable=False,
                suggested_action="Go to Settings > Email and verify your SMTP credentials. For Gmail, use an App Password instead of your regular password."
            )
            
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"Recipient refused: {e}")
            return self._create_error_result(
                message=f"The email address {message.to_email} was rejected by the server.",
                error_code="SMTP_RECIPIENT_REFUSED",
                retryable=False,
                suggested_action="Check that the email address is correct and try again."
            )
            
        except smtplib.SMTPSenderRefused as e:
            logger.error(f"Sender refused: {e}")
            return self._create_error_result(
                message="Your email server rejected the sender address.",
                error_code="SMTP_SENDER_REFUSED",
                retryable=False,
                suggested_action="Verify your 'From' email address in Settings > Email matches your SMTP account."
            )
            
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP connection failed: {e}")
            return self._create_error_result(
                message=f"Could not connect to email server {self.smtp_host}:{self.smtp_port}.",
                error_code="SMTP_CONNECTION_FAILED",
                retryable=True,
                retry_after=30,
                suggested_action="Check your internet connection and verify your SMTP server settings."
            )
            
        except socket.timeout:
            logger.error("SMTP connection timed out")
            return self._create_error_result(
                message="Connection to email server timed out.",
                error_code="SMTP_TIMEOUT",
                retryable=True,
                retry_after=30,
                suggested_action="Check your internet connection and try again."
            )
            
        except socket.error as e:
            logger.error(f"Network error: {e}")
            return self._create_error_result(
                message="Network error while sending email.",
                error_code="SMTP_NETWORK_ERROR",
                retryable=True,
                retry_after=30,
                suggested_action="Check your internet connection and try again."
            )
            
        except ssl.SSLError as e:
            logger.error(f"SSL error: {e}")
            return self._create_error_result(
                message="Secure connection to email server failed.",
                error_code="SMTP_SSL_ERROR",
                retryable=False,
                suggested_action="Check your SMTP settings. Try disabling TLS if your provider doesn't support it."
            )
            
        except Exception as e:
            logger.exception(f"Unexpected email error: {e}")
            return self._create_error_result(
                message="An unexpected error occurred while sending the email.",
                error_code="SMTP_UNEXPECTED_ERROR",
                retryable=True,
                retry_after=60,
                suggested_action="Please try again. If the problem persists, contact support."
            )
    
    async def send_quote(
        self,
        quote_id: str,
        to_email: str,
        to_name: Optional[str] = None,
        message: Optional[str] = None,
        pdf_bytes: Optional[bytes] = None,
        organization_id: Optional[str] = None
    ) -> EmailResult:
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
            EmailResult with success status and user-friendly messages
        """
        # Fetch quote data
        quote = get_quote_with_items(quote_id, organization_id)
        if not quote:
            return self._create_error_result(
                message="Quote not found. It may have been deleted.",
                error_code="QUOTE_NOT_FOUND",
                retryable=False,
                suggested_action="Check the quote ID and try again."
            )
        
        # Get org info
        org_name = self.default_from_name
        if organization_id:
            org = get_organization(organization_id)
            if org:
                org_name = org.get('name', org_name)
        
        quote_number = quote.get('quote_number', quote_id[:8].upper())
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
            from_name=org_name,
            from_email=self.default_from
        )
        
        result = await self.send_email(email_msg)
        
        # Add quote context to error messages
        if not result.success:
            result.message = f"Quote #{quote_number} was saved, but {result.message}"
        else:
            result.message = f"Quote #{quote_number} sent successfully to {to_email}"
        
        return result
    
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
        """Build HTML email body for quote with Mercura branding."""
        items_html = ""
        for item in quote.get('items', [])[:5]:  # Show first 5 items
            desc = item.get('description') or item.get('product_name') or 'Item'
            qty = item.get('quantity', 1)
            price = float(item.get('unit_price', 0))
            total = qty * price
            items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{desc}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: center;">{qty}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: right;">${price:,.2f}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: right; font-weight: 600;">${total:,.2f}</td>
            </tr>
            """
        
        if len(quote.get('items', [])) > 5:
            items_html += f"""
            <tr>
                <td colspan="4" style="padding: 10px; text-align: center; color: #6b7280; font-style: italic;">
                    ... and {len(quote['items']) - 5} more items
                </td>
            </tr>
            """
        
        message_html = f"""
        <div style="background-color: #fff7ed; border-left: 4px solid #f97316; padding: 15px; margin: 20px 0; border-radius: 4px;">
            <p style="color: #7c2d12; margin: 0;">{message}</p>
        </div>
        """ if message else ""
        
        subtotal = quote.get('subtotal', 0)
        tax_amount = quote.get('tax_amount', 0)
        
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
                                <td style="background: linear-gradient(135deg, #f97316, #ea580c); padding: 30px; text-align: center;">
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
                                    <div style="background-color: #f9fafb; border-radius: 8px; padding: 20px; margin: 25px 0;">
                                        <h3 style="color: #111827; font-size: 14px; margin: 0 0 15px 0; text-transform: uppercase; letter-spacing: 0.5px;">Quote Summary</h3>
                                        <table width="100%" style="font-size: 14px; border-collapse: collapse;">
                                            <thead>
                                                <tr style="border-bottom: 2px solid #e5e7eb;">
                                                    <th style="padding: 10px; text-align: left;">Item</th>
                                                    <th style="padding: 10px; text-align: center;">Qty</th>
                                                    <th style="padding: 10px; text-align: right;">Price</th>
                                                    <th style="padding: 10px; text-align: right;">Total</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {items_html}
                                            </tbody>
                                        </table>
                                        <div style="border-top: 2px solid #e5e7eb; margin-top: 15px; padding-top: 15px;">
                                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                                <span style="color: #6b7280;">Subtotal:</span>
                                                <span style="font-weight: 500;">${float(subtotal):,.2f}</span>
                                            </div>
                                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                                <span style="color: #6b7280;">Tax:</span>
                                                <span style="font-weight: 500;">${float(tax_amount):,.2f}</span>
                                            </div>
                                            <div style="display: flex; justify-content: space-between; padding-top: 8px; border-top: 1px solid #e5e7eb;">
                                                <span style="color: #111827; font-weight: 600;">Total:</span>
                                                <span style="color: #f97316; font-size: 20px; font-weight: 700;">${float(quote_total):,.2f}</span>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <!-- CTA -->
                                    <div style="text-align: center; margin: 30px 0;">
                                        <a href="mailto:{self.default_from}?subject=RE: Quote #{quote_number}" 
                                           style="display: inline-block; background: linear-gradient(135deg, #f97316, #ea580c); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 6px; font-size: 15px; font-weight: 500; box-shadow: 0 4px 6px rgba(249, 115, 22, 0.3);">
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
                                    <p style="color: #9ca3af; font-size: 12px; margin: 0;">
                                        Sent with Mercura — AI-Powered Quoting
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
    
    async def test_connection(self) -> EmailResult:
        """Test SMTP connection without sending an email."""
        if not self.enabled:
            return self._create_error_result(
                message="Email is not configured.",
                error_code="EMAIL_NOT_CONFIGURED",
                retryable=False
            )
        
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.ehlo()
                if self.use_tls:
                    server.starttls()
                    server.ehlo()
                server.login(self.smtp_username, self.smtp_password)
                
                return EmailResult(
                    success=True,
                    message=f"Successfully connected to {self.smtp_host}",
                    sent_at=datetime.utcnow()
                )
                
        except smtplib.SMTPAuthenticationError:
            return self._create_error_result(
                message="Authentication failed. Check your username and password.",
                error_code="SMTP_AUTH_FAILED",
                retryable=False,
                suggested_action="For Gmail, use an App Password instead of your regular password."
            )
        except Exception as e:
            return self._create_error_result(
                message=f"Connection failed: {str(e)}",
                error_code="SMTP_CONNECTION_FAILED",
                retryable=True
            )


# Global instance (fallback for backward compatibility)
email_service: Optional[EmailService] = None
if EMAIL_AVAILABLE:
    try:
        email_service = EmailService()
    except Exception as e:
        logger.warning(f"Failed to initialize default email service: {e}")


def get_email_service_for_org(organization_id: str) -> Optional[EmailService]:
    """Get an email service configured for a specific organization."""
    return EmailService.from_organization(organization_id)
