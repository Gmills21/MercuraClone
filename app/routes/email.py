"""
Email API Routes
Send quotes and notifications via email using organization-specific SMTP settings.
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, EmailStr
from typing import Optional, List

from app.services.email_service import get_email_service_for_org, EmailMessage
from app.services.pdf_service import pdf_service
from app.middleware.organization import get_current_user_and_org
from app.posthog_utils import capture_event

router = APIRouter(prefix="/email", tags=["email"])


class SendQuoteRequest(BaseModel):
    """Request to send a quote via email."""
    to_email: EmailStr
    to_name: Optional[str] = None
    message: Optional[str] = None
    include_pdf: bool = True


class SendEmailRequest(BaseModel):
    """Request to send a custom email."""
    to_email: EmailStr
    to_name: Optional[str] = None
    subject: str
    body_text: str
    body_html: Optional[str] = None


class EmailStatusResponse(BaseModel):
    """Email send status response."""
    success: bool
    message: str
    sent_at: Optional[str] = None
    error: Optional[str] = None


@router.post("/quote/{quote_id}/send", response_model=EmailStatusResponse)
async def send_quote_email(
    quote_id: str,
    request: SendQuoteRequest,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Send a quote to a customer via email.
    
    Automatically generates and attaches a professional PDF quote.
    Uses organization-specific SMTP settings.
    """
    user_id, org_id = user_org
    
    # Get org-specific email service
    email_service = get_email_service_for_org(org_id)
    
    if not email_service:
        raise HTTPException(
            status_code=503,
            detail="Email service not configured. Please configure SMTP settings in Account > Email."
        )
    
    # Generate PDF if requested
    pdf_bytes = None
    if request.include_pdf and pdf_service:
        try:
            pdf_bytes = pdf_service.generate_quote_pdf(quote_id, org_id)
        except Exception as e:
            print(f"PDF generation failed: {e}")
            # Continue without PDF if generation fails
    
    # Send email
    result = email_service.send_quote(
        quote_id=quote_id,
        to_email=request.to_email,
        to_name=request.to_name,
        message=request.message,
        pdf_bytes=pdf_bytes,
        organization_id=org_id
    )
    
    # Track event
    capture_event(
        distinct_id=user_id,
        event_name="quote_email_sent",
        properties={
            "quote_id": quote_id,
            "to_email": request.to_email,
            "success": result["success"],
            "organization_id": org_id
        }
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Email failed"))
    
    return EmailStatusResponse(**result)


@router.post("/send", response_model=EmailStatusResponse)
async def send_custom_email(
    request: SendEmailRequest,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Send a custom email.
    
    For notifications, follow-ups, or any custom communication.
    Uses organization-specific SMTP settings.
    """
    user_id, org_id = user_org
    
    # Get org-specific email service
    email_service = get_email_service_for_org(org_id)
    
    if not email_service:
        raise HTTPException(
            status_code=503,
            detail="Email service not configured. Please configure SMTP settings in Account > Email."
        )
    
    message = EmailMessage(
        to_email=request.to_email,
        to_name=request.to_name,
        subject=request.subject,
        body_text=request.body_text,
        body_html=request.body_html
    )
    
    result = email_service.send_email(message)
    
    capture_event(
        distinct_id=user_id,
        event_name="custom_email_sent",
        properties={
            "to_email": request.to_email,
            "success": result["success"],
            "organization_id": org_id
        }
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Email failed"))
    
    return EmailStatusResponse(**result)


@router.get("/status")
async def email_status(user_org: tuple = Depends(get_current_user_and_org)):
    """
    Check email service status and configuration for the organization.
    """
    user_id, org_id = user_org
    
    # Get org-specific email service
    email_service = get_email_service_for_org(org_id)
    
    if not email_service:
        from app.database_sqlite import get_email_settings
        settings = get_email_settings(org_id)
        
        if not settings:
            return {
                "enabled": False,
                "configured": False,
                "message": "Email not configured. Go to Account > Email to configure SMTP settings."
            }
        
        if not settings.get("is_enabled"):
            return {
                "enabled": False,
                "configured": True,
                "message": "Email is configured but disabled. Enable it in Account > Email."
            }
        
        return {
            "enabled": False,
            "configured": False,
            "message": "Email configuration error. Check your SMTP settings."
        }
    
    return email_service.get_status()


@router.post("/test")
async def test_email_config(
    test_email: str = Body(..., embed=True),
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Test email configuration by sending a test email.
    Uses organization-specific SMTP settings.
    """
    user_id, org_id = user_org
    
    # Get org-specific email service
    email_service = get_email_service_for_org(org_id)
    
    if not email_service:
        raise HTTPException(
            status_code=503,
            detail="Email service not configured. Please configure SMTP settings first."
        )
    
    message = EmailMessage(
        to_email=test_email,
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
    
    result = email_service.send_email(message)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Test failed"))
    
    return {"success": True, "message": f"Test email sent to {test_email}"}
