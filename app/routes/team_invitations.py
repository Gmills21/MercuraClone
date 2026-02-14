"""
Team Invitation API Routes
Handle inviting and managing team members.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

from app.services.team_invitation_service import TeamInvitationService
from app.services.email_service import email_service, EmailMessage
from app.middleware.organization import get_current_user_and_org

router = APIRouter(prefix="/team/invitations", tags=["team-invitations"])


class CreateInvitationRequest(BaseModel):
    email: EmailStr
    role: str = Field(default="sales_rep", pattern="^(viewer|sales_rep|manager|admin)$")


class CreateInvitationResponse(BaseModel):
    success: bool
    invite_id: Optional[str] = None
    token: Optional[str] = None
    message: str
    is_resend: bool = False


class AcceptInvitationRequest(BaseModel):
    token: str
    name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8)


class AcceptInvitationResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    email: Optional[str] = None
    organization_id: Optional[str] = None
    message: str
    error: Optional[str] = None


class InvitationResponse(BaseModel):
    id: str
    email: str
    role: str
    status: str
    created_at: str
    expires_at: str
    accepted_at: Optional[str] = None
    invited_by_name: Optional[str] = None


class InvitationValidationResponse(BaseModel):
    valid: bool
    email: Optional[str] = None
    org_name: Optional[str] = None
    role: Optional[str] = None
    inviter_name: Optional[str] = None
    error: Optional[str] = None


def _send_invitation_email(
    to_email: str,
    org_name: str,
    inviter_name: str,
    invite_token: str,
    role: str
):
    """Send team invitation email."""
    if not email_service:
        return False
    
    import os
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    invite_url = f"{frontend_url}/accept-invite?token={invite_token}"
    
    role_display = {
        "viewer": "Viewer",
        "sales_rep": "Sales Rep",
        "manager": "Manager",
        "admin": "Admin"
    }.get(role, role)
    
    subject = f"You've been invited to join {org_name} on Mercura"
    
    text_body = f"""Hi there,

{inviter_name} has invited you to join {org_name} on Mercura as a {role_display}.

Mercura is an AI-powered inside sales platform that helps industrial distributors automate RFQ processing and quote generation.

Click the link below to accept the invitation:
{invite_url}

This invitation expires in 7 days.

If you have any questions, please contact {inviter_name} directly.

Best regards,
The Mercura Team
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
                            <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">Mercura</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="color: #111827; font-size: 20px; margin: 0 0 20px 0;">You've Been Invited!</h2>
                            <p style="color: #374151; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                                <strong>{inviter_name}</strong> has invited you to join <strong>{org_name}</strong> on Mercura as a <strong>{role_display}</strong>.
                            </p>
                            <div style="background-color: #fff7ed; border-left: 4px solid #f97316; padding: 15px; margin: 20px 0;">
                                <p style="color: #9a3412; font-size: 14px; margin: 0;">
                                    Mercura helps industrial distributors automate RFQ processing and quote generation with AI.
                                </p>
                            </div>
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{invite_url}" style="display: inline-block; background: linear-gradient(135deg, #f97316, #ea580c); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 6px; font-size: 15px; font-weight: 500;">
                                    Accept Invitation
                                </a>
                            </div>
                            <p style="color: #6b7280; font-size: 14px; line-height: 1.5; margin: 20px 0;">
                                Or copy and paste this link:<br>
                                <a href="{invite_url}" style="color: #ea580c; word-break: break-all;">{invite_url}</a>
                            </p>
                            <div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 15px; margin: 25px 0;">
                                <p style="color: #1e40af; font-size: 14px; margin: 0;">
                                    <strong>Note:</strong> This invitation expires in 7 days.
                                </p>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #f9fafb; padding: 20px 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                            <p style="color: #6b7280; font-size: 13px; margin: 0;">
                                If you have questions, contact {inviter_name} directly.
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
        subject=subject,
        body_text=text_body,
        body_html=html_body
    )
    
    result = email_service.send_email(message)
    return result.get("success", False)


@router.post("/", response_model=CreateInvitationResponse)
async def create_invitation(
    request: CreateInvitationRequest,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Create a new team invitation.
    Requires admin or manager role.
    """
    user_id, org_id = user_org
    
    result = TeamInvitationService.create_invitation(
        organization_id=org_id,
        email=request.email,
        role=request.role,
        invited_by=user_id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Send invitation email
    email_sent = _send_invitation_email(
        to_email=result["email"],
        org_name=result["org_name"],
        inviter_name=result["inviter_name"],
        invite_token=result["token"],
        role=result["role"]
    )
    
    if not email_sent and not result.get("is_resend"):
        print(f"WARNING: Failed to send invitation email to {request.email}")
    
    return CreateInvitationResponse(
        success=True,
        invite_id=result["invite_id"],
        token=result["token"],
        message=result["message"],
        is_resend=result.get("is_resend", False)
    )


@router.get("/validate/{token}", response_model=InvitationValidationResponse)
async def validate_invitation(token: str):
    """
    Validate an invitation token.
    Used by frontend to show appropriate UI.
    """
    result = TeamInvitationService.validate_invitation(token)
    
    if not result["valid"]:
        return InvitationValidationResponse(
            valid=False,
            error=result.get("error", "Invalid invitation")
        )
    
    return InvitationValidationResponse(
        valid=True,
        email=result["email"],
        org_name=result["org_name"],
        role=result["role"],
        inviter_name=result["inviter_name"]
    )


@router.post("/accept", response_model=AcceptInvitationResponse)
async def accept_invitation(request: AcceptInvitationRequest):
    """
    Accept an invitation and create user account.
    """
    result = TeamInvitationService.accept_invitation(
        token=request.token,
        name=request.name,
        password=request.password
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return AcceptInvitationResponse(
        success=True,
        token=result["token"],
        email=result["email"],
        organization_id=result["organization_id"],
        message="Welcome to Mercura! Your account has been created."
    )


@router.get("/", response_model=List[InvitationResponse])
async def list_invitations(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    List all invitations for the organization.
    Requires admin or manager role.
    """
    user_id, org_id = user_org
    
    invitations = TeamInvitationService.list_invitations(org_id)
    return [InvitationResponse(**inv) for inv in invitations]


@router.delete("/{invite_id}")
async def cancel_invitation(
    invite_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Cancel a pending invitation.
    Requires admin role or organization owner.
    """
    user_id, org_id = user_org
    
    result = TeamInvitationService.cancel_invitation(invite_id, user_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {"success": True, "message": "Invitation canceled"}


@router.post("/{invite_id}/resend", response_model=CreateInvitationResponse)
async def resend_invitation(
    invite_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Resend an existing invitation.
    Requires admin or manager role.
    """
    user_id, org_id = user_org
    
    # Get existing invite
    from app.database_sqlite import get_db
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT oi.email, oi.role, oi.token, oi.status, oi.organization_id,
                   o.name as org_name, u.name as inviter_name
            FROM organization_invitations oi
            JOIN organizations o ON oi.organization_id = o.id
            JOIN users u ON oi.invited_by = u.id
            WHERE oi.id = ? AND oi.organization_id = ?
        """, (invite_id, org_id))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Invitation not found")
        
        invite = dict(row)
        
        if invite["status"] != "pending":
            raise HTTPException(status_code=400, detail=f"Cannot resend {invite['status']} invitation")
    
    # Resend email
    email_sent = _send_invitation_email(
        to_email=invite["email"],
        org_name=invite["org_name"],
        inviter_name=invite["inviter_name"],
        invite_token=invite["token"],
        role=invite["role"]
    )
    
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send invitation email")
    
    return CreateInvitationResponse(
        success=True,
        invite_id=invite_id,
        token=invite["token"],
        message="Invitation resent successfully",
        is_resend=True
    )
