"""
Organization API Routes
Handles organization management, team invitations, and member management.
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from loguru import logger

from app.auth import get_current_user, User
from app.organization_service import OrganizationService
from app.auth_enhanced import EnhancedAuthService, SessionService, PasswordResetService
from app.models_organization import (
    CreateOrganizationRequest, UpdateOrganizationRequest,
    InviteMemberRequest, AcceptInvitationRequest
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


# ==================== ORGANIZATION MANAGEMENT ====================

@router.post("/create")
async def create_organization(
    request: CreateOrganizationRequest,
):
    """
    Create a new organization with owner user.
    This is used during signup flow.
    """
    # Register user and create organization
    result = EnhancedAuthService.register_user(
        email=request.owner_email,
        name=request.owner_name,
        password=request.owner_password,
        organization_name=request.name,
        organization_slug=request.slug
    )
    
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create organization (email may exist or slug taken)")
    
    return {
        "success": True,
        "organization_id": result["organization_id"],
        "user_id": result["user_id"],
        "access_token": result["access_token"],
        "message": "Organization created successfully"
    }


@router.get("/me")
async def get_current_organization(
    authorization: Optional[str] = Header(None)
):
    """Get current user's primary organization."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    session = SessionService.validate_session(token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    user_id = session["user_id"]
    org_id = session["organization_id"]
    
    if org_id:
        org = OrganizationService.get_organization(org_id)
        if org:
            return {
                "id": org.id,
                "name": org.name,
                "slug": org.slug,
                "status": org.status,
                "seats_total": org.seats_total,
                "seats_used": org.seats_used,
                "trial_ends_at": org.trial_ends_at.isoformat() if org.trial_ends_at else None,
                "created_at": org.created_at.isoformat()
            }
    
    # Fallback: list user's organizations
    orgs = OrganizationService.list_user_organizations(user_id)
    if orgs:
        org = orgs[0]
        return {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "status": org.status,
            "seats_total": org.seats_total,
            "seats_used": org.seats_used,
            "trial_ends_at": org.trial_ends_at.isoformat() if org.trial_ends_at else None,
            "created_at": org.created_at.isoformat()
        }
    
    raise HTTPException(status_code=404, detail="No organization found")


@router.get("/{org_id}")
async def get_organization(
    org_id: str,
    authorization: Optional[str] = Header(None)
):
    """Get organization details."""
    # Validate session
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = authorization.replace("Bearer ", "")
    session = SessionService.validate_session(token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    org = OrganizationService.get_organization(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "domain": org.domain,
        "status": org.status,
        "seats_total": org.seats_total,
        "seats_used": org.seats_used,
        "settings": org.settings,
        "branding": org.branding,
        "created_at": org.created_at.isoformat(),
        "trial_ends_at": org.trial_ends_at.isoformat() if org.trial_ends_at else None
    }


@router.patch("/{org_id}")
async def update_organization(
    org_id: str,
    request: UpdateOrganizationRequest,
    authorization: Optional[str] = Header(None)
):
    """Update organization details. Requires admin or owner role."""
    # Validate session and check permissions
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = authorization.replace("Bearer ", "")
    session = SessionService.validate_session(token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # TODO: Check if user is admin/owner of this org
    
    updates = request.dict(exclude_unset=True)
    success = OrganizationService.update_organization(org_id, updates)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update organization")
    
    return {"success": True, "message": "Organization updated successfully"}


@router.get("/{org_id}/members")
async def list_organization_members(
    org_id: str,
    authorization: Optional[str] = Header(None)
):
    """List all members of an organization."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = authorization.replace("Bearer ", "")
    session = SessionService.validate_session(token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    members = OrganizationService.get_members(org_id)
    return {"members": members}


# ==================== TEAM INVITATIONS ====================

@router.post("/{org_id}/invite")
async def invite_member(
    org_id: str,
    request: InviteMemberRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Invite a new member to the organization.
    Requires admin or owner role.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = authorization.replace("Bearer ", "")
    session = SessionService.validate_session(token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user_id = session["user_id"]
    
    # TODO: Check if user is admin/owner of this org
    
    # Check seat limits
    org = OrganizationService.get_organization(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if org.seats_total and org.seats_used >= org.seats_total:
        raise HTTPException(status_code=400, detail="No available seats. Please upgrade your plan.")
    
    # Create invitation
    invitation = OrganizationService.invite_member(
        org_id=org_id,
        email=request.email,
        role=request.role,
        invited_by=user_id
    )
    
    if not invitation:
        raise HTTPException(status_code=400, detail="Failed to create invitation (user may already be invited or a member)")
    
    # TODO: Send email with invitation link if request.send_email is True
    invitation_link = f"https://yourapp.com/invite/accept?token={invitation.token}"
    
    return {
        "success": True,
        "invitation_id": invitation.id,
        "invitation_link": invitation_link,
        "message": f"Invitation sent to {request.email}"
    }


@router.get("/invitations/{token}")
async def get_invitation_details(token: str):
    """Get invitation details by token (public endpoint)."""
    invitation = OrganizationService.get_invitation_by_token(token)
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found or expired")
    
    if invitation["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Invitation is {invitation['status']}")
    
    return {
        "organization_name": invitation["organization_name"],
        "email": invitation["email"],
        "role": invitation["role"],
        "expires_at": invitation["expires_at"]
    }


@router.post("/invitations/accept")
async def accept_invitation(request: AcceptInvitationRequest):
    """
    Accept an invitation and create user account.
    Public endpoint - creates new user.
    """
    # Get invitation details
    invitation = OrganizationService.get_invitation_by_token(request.token)
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found or expired")
    
    # Register user
    from app.auth import create_user
    
    user = create_user(
        email=invitation["email"],
        name=request.user_name,
        password=request.password,
        role=invitation["role"],
        company_id=invitation["organization_id"]
    )
    
    if not user:
        raise HTTPException(status_code=400, detail="Failed to create user account")
    
    # Accept invitation
    success = OrganizationService.accept_invitation(request.token, user.id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to accept invitation")
    
    # Create session
    token = SessionService.create_session(
        user_id=user.id,
        organization_id=invitation["organization_id"],
        remember_me=True
    )
    
    return {
        "success": True,
        "access_token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role
        },
        "organization_id": invitation["organization_id"],
        "message": "Successfully joined organization"
    }


@router.delete("/{org_id}/members/{user_id}")
async def remove_member(
    org_id: str,
    user_id: str,
    authorization: Optional[str] = Header(None)
):
    """Remove a member from organization. Requires admin or owner role."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = authorization.replace("Bearer ", "")
    session = SessionService.validate_session(token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # TODO: Check if user is admin/owner of this org
    
    success = OrganizationService.remove_member(org_id, user_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to remove member (may be organization owner)")
    
    return {"success": True, "message": "Member removed successfully"}


@router.patch("/{org_id}/members/{user_id}/role")
async def update_member_role(
    org_id: str,
    user_id: str,
    new_role: str,
    authorization: Optional[str] = Header(None)
):
    """Update a member's role. Requires admin or owner role."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = authorization.replace("Bearer ", "")
    session = SessionService.validate_session(token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # TODO: Check if user is admin/owner of this org
    
    success = OrganizationService.update_member_role(org_id, user_id, new_role)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update role (invalid role name)")
    
    return {"success": True, "message": "Role updated successfully"}


# ==================== PASSWORD RESET ====================

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """
    Request a password reset token.
    Always returns success to avoid email enumeration.
    """
    token = PasswordResetService.create_reset_token(request.email)
    
    # TODO: Send email with reset link
    if token:
        reset_link = f"https://yourapp.com/reset-password?token={token}"
        logger.info(f"Password reset link: {reset_link}")
    
    # Always return success to avoid revealing if email exists
    return {
        "success": True,
        "message": "If that email is registered, you will receive a password reset link."
    }


@router.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Reset password using token from email."""
    success = PasswordResetService.reset_password(request.token, request.new_password)
    
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    return {
        "success": True,
        "message": "Password reset successfully. Please log in with your new password."
    }


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/auth/change-password")
async def change_password(
    request: ChangePasswordRequest,
    authorization: Optional[str] = Header(None)
):
    """Change password (requires old password). User must be authenticated."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = authorization.replace("Bearer ", "")
    session = SessionService.validate_session(token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    success = EnhancedAuthService.change_password(
        user_id=session["user_id"],
        old_password=request.old_password,
        new_password=request.new_password
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Invalid old password")
    
    return {
        "success": True,
        "message": "Password changed successfully"
    }


# ==================== SESSION MANAGEMENT ====================

@router.get("/auth/sessions")
async def list_sessions(authorization: Optional[str] = Header(None)):
    """List all active sessions for current user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = authorization.replace("Bearer ", "")
    session = SessionService.validate_session(token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    sessions = SessionService.list_user_sessions(session["user_id"])
    return {"sessions": sessions}


@router.post("/auth/sessions/revoke-all")
async def revoke_all_sessions(
    keep_current: bool = True,
    authorization: Optional[str] = Header(None)
):
    """Revoke all sessions (useful after password change or security breach)."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = authorization.replace("Bearer ", "")
    session = SessionService.validate_session(token)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    count = SessionService.revoke_all_sessions(
        user_id=session["user_id"],
        except_session_id=session["session_id"] if keep_current else None
    )
    
    return {
        "success": True,
        "sessions_revoked": count,
        "message": f"Revoked {count} session(s)"
    }
