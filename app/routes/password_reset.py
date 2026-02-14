"""
Password Reset API Routes
Secure password reset flow with email delivery.
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from app.services.password_reset_service import PasswordResetService
from app.services.email_service import email_service, EmailMessage

router = APIRouter(prefix="/auth/password-reset", tags=["password-reset"])


class RequestResetRequest(BaseModel):
    email: EmailStr


class RequestResetResponse(BaseModel):
    success: bool
    message: str


class ValidateTokenResponse(BaseModel):
    valid: bool
    email: Optional[str] = None
    name: Optional[str] = None
    error: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class ResetPasswordResponse(BaseModel):
    success: bool
    message: str
    email: Optional[str] = None
    error: Optional[str] = None


def _send_reset_email(to_email: str, to_name: str, reset_token: str, org_name: str = "Mercura"):
    """Send password reset email to user."""
    if not email_service:
        return False
    
    # Build reset URL (frontend URL)
    import os
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    reset_url = f"{frontend_url}/reset-password?token={reset_token}"
    
    subject = f"Reset your {org_name} password"
    
    text_body = f"""Hi {to_name},

You requested a password reset for your {org_name} account.

Click the link below to reset your password:
{reset_url}

This link will expire in 24 hours.

If you didn't request this, you can safely ignore this email.

Best regards,
The {org_name} Team
"""
    
    html_body = f"""
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
                    <tr>
                        <td style="background: linear-gradient(135deg, #f97316, #ea580c); padding: 30px; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">{org_name}</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="color: #111827; font-size: 20px; margin: 0 0 20px 0;">Reset Your Password</h2>
                            <p style="color: #374151; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                                Hi {to_name},
                            </p>
                            <p style="color: #374151; font-size: 15px; line-height: 1.6; margin: 0 0 30px 0;">
                                We received a request to reset your password. Click the button below to create a new password:
                            </p>
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{reset_url}" style="display: inline-block; background: linear-gradient(135deg, #f97316, #ea580c); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 6px; font-size: 15px; font-weight: 500;">
                                    Reset Password
                                </a>
                            </div>
                            <p style="color: #6b7280; font-size: 14px; line-height: 1.5; margin: 20px 0;">
                                Or copy and paste this link into your browser:<br>
                                <a href="{reset_url}" style="color: #ea580c; word-break: break-all;">{reset_url}</a>
                            </p>
                            <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 25px 0;">
                                <p style="color: #92400e; font-size: 14px; margin: 0;">
                                    <strong>Note:</strong> This link expires in 24 hours.
                                </p>
                            </div>
                            <p style="color: #6b7280; font-size: 14px; line-height: 1.5; margin: 20px 0 0 0;">
                                If you didn't request a password reset, you can safely ignore this email.
                            </p>
                        </td>
                    </tr>
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
    
    message = EmailMessage(
        to_email=to_email,
        to_name=to_name,
        subject=subject,
        body_text=text_body,
        body_html=html_body
    )
    
    result = email_service.send_email(message)
    return result.get("success", False)


@router.post("/request", response_model=RequestResetResponse)
async def request_password_reset(request: RequestResetRequest):
    """
    Request a password reset email.
    
    Always returns success to prevent email enumeration attacks.
    """
    result = PasswordResetService.create_reset_token(request.email)
    
    if not result["success"]:
        # Rate limit hit - still return generic message but log it
        return RequestResetResponse(
            success=True,
            message="If an account exists with this email, a password reset link has been sent."
        )
    
    # Send email if user exists
    if result["token"] and result["user"]:
        email_sent = _send_reset_email(
            to_email=result["user"]["email"],
            to_name=result["user"]["name"],
            reset_token=result["token"],
            org_name=result["user"].get("org_name", "Mercura")
        )
        
        if not email_sent:
            # Log this but don't fail the request - user can try again
            print(f"WARNING: Failed to send password reset email to {request.email}")
    
    # Always return generic success message
    return RequestResetResponse(
        success=True,
        message="If an account exists with this email, a password reset link has been sent."
    )


@router.get("/validate/{token}", response_model=ValidateTokenResponse)
async def validate_reset_token(token: str):
    """
    Validate a password reset token.
    Used by frontend to show appropriate UI.
    """
    result = PasswordResetService.validate_token(token)
    
    if not result["valid"]:
        return ValidateTokenResponse(
            valid=False,
            error=result.get("error", "Invalid token")
        )
    
    return ValidateTokenResponse(
        valid=True,
        email=result["email"],
        name=result["name"]
    )


@router.post("/reset", response_model=ResetPasswordResponse)
async def reset_password(request: ResetPasswordRequest):
    """
    Reset password using a valid token.
    """
    result = PasswordResetService.reset_password(request.token, request.new_password)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return ResetPasswordResponse(
        success=True,
        message="Password reset successfully. You can now log in with your new password.",
        email=result.get("email")
    )
