"""
Settings API Routes
Organization settings including email configuration.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional

from app.middleware.organization import get_current_user_and_org
from app.database_sqlite import (
    get_email_settings,
    create_or_update_email_settings,
    delete_email_settings
)
from app.config import settings

router = APIRouter(prefix="/settings", tags=["settings"])


class EmailSettingsRequest(BaseModel):
    """Email configuration request."""
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP server hostname")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: str = Field(..., description="SMTP username/email")
    smtp_password: str = Field(..., description="SMTP password or app-specific password")
    from_email: Optional[str] = Field(default=None, description="Sender email address (defaults to username)")
    from_name: str = Field(default="Mercura", description="Sender display name")
    use_tls: bool = Field(default=True, description="Use TLS encryption")
    is_enabled: bool = Field(default=False, description="Enable email sending")


class EmailSettingsResponse(BaseModel):
    """Email configuration response (excludes password)."""
    smtp_host: str
    smtp_port: int
    smtp_username: str
    from_email: str
    from_name: str
    use_tls: bool
    is_enabled: bool
    configured: bool


class EmailTestRequest(BaseModel):
    """Test email request."""
    test_email: str = Field(..., description="Email address to send test to")


@router.get("/email", response_model=EmailSettingsResponse)
async def get_email_config(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get email settings for the current organization.
    Password is not returned for security.
    """
    user_id, org_id = user_org
    
    email_settings = get_email_settings(org_id)
    
    if not email_settings:
        # Return default/unconfigured state
        return EmailSettingsResponse(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_username="",
            from_email="",
            from_name="Mercura",
            use_tls=True,
            is_enabled=False,
            configured=False
        )
    
    return EmailSettingsResponse(
        smtp_host=email_settings.get("smtp_host", "smtp.gmail.com"),
        smtp_port=email_settings.get("smtp_port", 587),
        smtp_username=email_settings.get("smtp_username", ""),
        from_email=email_settings.get("from_email", email_settings.get("smtp_username", "")),
        from_name=email_settings.get("from_name", "Mercura"),
        use_tls=bool(email_settings.get("use_tls", True)),
        is_enabled=bool(email_settings.get("is_enabled", False)),
        configured=bool(email_settings.get("smtp_username") and email_settings.get("smtp_password"))
    )


@router.post("/email", response_model=EmailSettingsResponse)
async def update_email_config(
    request: EmailSettingsRequest,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Update email settings for the current organization.
    Only admins can update email settings.
    """
    user_id, org_id = user_org
    
    # TODO: Check if user is admin/manager
    
    # Update settings
    updated = create_or_update_email_settings(
        organization_id=org_id,
        smtp_host=request.smtp_host,
        smtp_port=request.smtp_port,
        smtp_username=request.smtp_username,
        smtp_password=request.smtp_password,
        from_email=request.from_email or request.smtp_username,
        from_name=request.from_name,
        use_tls=request.use_tls,
        is_enabled=request.is_enabled
    )
    
    return EmailSettingsResponse(
        smtp_host=updated.get("smtp_host", "smtp.gmail.com"),
        smtp_port=updated.get("smtp_port", 587),
        smtp_username=updated.get("smtp_username", ""),
        from_email=updated.get("from_email", updated.get("smtp_username", "")),
        from_name=updated.get("from_name", "Mercura"),
        use_tls=bool(updated.get("use_tls", True)),
        is_enabled=bool(updated.get("is_enabled", False)),
        configured=True
    )


@router.delete("/email")
async def delete_email_config(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Delete email settings for the current organization.
    """
    user_id, org_id = user_org
    
    deleted = delete_email_settings(org_id)
    
    return {"success": deleted, "message": "Email settings deleted" if deleted else "No settings to delete"}


@router.post("/email/test")
async def test_email_config(
    request: EmailTestRequest,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Test email configuration by sending a test email.
    """
    user_id, org_id = user_org
    
    # Get org email settings
    email_settings = get_email_settings(org_id)
    
    if not email_settings or not email_settings.get("is_enabled"):
        raise HTTPException(
            status_code=400,
            detail="Email is not configured or not enabled. Please configure email settings first."
        )
    
    # Build email service with org settings
    from app.services.email_service import EmailService, EmailMessage
    
    service = EmailService(
        smtp_host=email_settings.get("smtp_host", "smtp.gmail.com"),
        smtp_port=email_settings.get("smtp_port", 587),
        smtp_username=email_settings.get("smtp_username", ""),
        smtp_password=email_settings.get("smtp_password", ""),
        default_from=email_settings.get("from_email") or email_settings.get("smtp_username", ""),
        default_from_name=email_settings.get("from_name", "Mercura")
    )
    
    if not service.enabled:
        raise HTTPException(
            status_code=400,
            detail="Email service could not be initialized. Check your SMTP settings."
        )
    
    # Send test email
    message = EmailMessage(
        to_email=request.test_email,
        subject="Mercura Email Test",
        body_text="""This is a test email from your Mercura account.

If you received this, your email configuration is working correctly!

You can now send quotes to customers via email.
""",
        body_html="""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #f97316, #ea580c); padding: 30px; border-radius: 8px 8px 0 0; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px;">Mercura</h1>
            </div>
            <div style="background: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
                <h2 style="color: #111827; margin-top: 0;">Email Test Successful! 🎉</h2>
                <p style="color: #374151; line-height: 1.6;">This is a test email from your <strong>Mercura</strong> account.</p>
                <p style="color: #374151; line-height: 1.6;">If you're seeing this, your email configuration is working correctly!</p>
                <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0;">
                    <p style="color: #92400e; margin: 0;">You can now send quotes to customers via email.</p>
                </div>
            </div>
        </div>
        """
    )
    
    result = service.send_email(message)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to send test email"))
    
    return {
        "success": True,
        "message": f"Test email sent to {request.test_email}",
        "sent_at": result.get("sent_at")
    }


@router.get("/email/providers")
async def get_email_providers():
    """
    Get list of common email providers and their SMTP settings.
    """
    return {
        "providers": [
            {
                "name": "Gmail / Google Workspace",
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587,
                "use_tls": True,
                "notes": "Use App Password if 2FA is enabled"
            },
            {
                "name": "Microsoft 365 / Outlook",
                "smtp_host": "smtp.office365.com",
                "smtp_port": 587,
                "use_tls": True,
                "notes": "Use your full email as username"
            },
            {
                "name": "SendGrid",
                "smtp_host": "smtp.sendgrid.net",
                "smtp_port": 587,
                "use_tls": True,
                "notes": "Use 'apikey' as username and your API key as password"
            },
            {
                "name": "Mailgun",
                "smtp_host": "smtp.mailgun.org",
                "smtp_port": 587,
                "use_tls": True,
                "notes": "Use your Mailgun SMTP credentials"
            },
            {
                "name": "AWS SES",
                "smtp_host": "email-smtp.us-east-1.amazonaws.com",
                "smtp_port": 587,
                "use_tls": True,
                "notes": "Use your SES SMTP credentials"
            },
            {
                "name": "GoDaddy",
                "smtp_host": "smtpout.secureserver.net",
                "smtp_port": 587,
                "use_tls": True,
                "notes": "Use your full email as username"
            },
            {
                "name": "Namecheap",
                "smtp_host": "mail.privateemail.com",
                "smtp_port": 587,
                "use_tls": True,
                "notes": "Private Email hosting"
            }
        ]
    }
