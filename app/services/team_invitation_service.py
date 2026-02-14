"""
Team Invitation Service
Handles inviting team members to organizations.
"""

import secrets
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from app.database_sqlite import get_db
from app.utils.transactions import (
    transaction,
    atomic,
    TransactionOptions,
    IsolationLevel
)
from app.errors import (
    AppError,
    ErrorCategory,
    ErrorSeverity,
    validation_error,
    not_found,
    forbidden,
    quota_exceeded
)


INVITE_TOKEN_EXPIRY_DAYS = 7
MAX_PENDING_INVITES_PER_ORG = 20


class QuotaExceededError(Exception):
    """Raised when seat quota is exceeded; used to rollback the transaction."""

class TooManyPendingInvitesError(Exception):
    """Raised when too many pending invites; used to rollback the transaction."""


class TeamInvitationService:
    """Service for managing team invitations."""
    
    @staticmethod
    def _generate_token() -> str:
        """Generate a secure invitation token."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def _get_org_member_count(organization_id: str) -> int:
        """Get current member count for an organization."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM organization_members
                WHERE organization_id = ? AND is_active = 1
            """, (organization_id,))
            return cursor.fetchone()[0]
    
    @staticmethod
    def _get_pending_invite_count(organization_id: str) -> int:
        """Get count of pending invitations."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM organization_invitations
                WHERE organization_id = ? AND status = 'pending'
            """, (organization_id,))
            row = cursor.fetchone()
            return row[0] if row else 0
    
    @staticmethod
    def _get_org_seats(organization_id: str) -> Dict[str, int]:
        """Get seat information for organization."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT seats_total, seats_used FROM organizations
                WHERE id = ?
            """, (organization_id,))
            row = cursor.fetchone()
            if row:
                return {"total": row["seats_total"] or 1, "used": row["seats_used"] or 0}
            return {"total": 1, "used": 0}
    
    @staticmethod
    def _user_exists(email: str) -> Optional[Dict[str, Any]]:
        """Check if user already exists with this email."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.email, u.name, u.is_active, o.id as org_id, o.name as org_name
                FROM users u
                JOIN organization_members om ON u.id = om.user_id
                JOIN organizations o ON om.organization_id = o.id
                WHERE u.email = ?
                LIMIT 1
            """, (email.lower().strip(),))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    @staticmethod
    def _get_existing_invite(organization_id: str, email: str) -> Optional[Dict[str, Any]]:
        """Check for existing pending invite."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, token, expires_at, status
                FROM organization_invitations
                WHERE organization_id = ? AND email = ? AND status = 'pending'
            """, (organization_id, email.lower().strip()))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    @staticmethod
    def create_invitation(
        organization_id: str,
        email: str,
        role: str,
        invited_by: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create a new team invitation.
        """
        # Validate role
        valid_roles = ["viewer", "sales_rep", "manager", "admin"]
        if role not in valid_roles:
            return validation_error(
                field="role",
                message=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            ).to_dict()
        
        # Check if user already exists
        existing_user = TeamInvitationService._user_exists(email)
        if existing_user:
            return AppError(
                category=ErrorCategory.CONFLICT,
                code="USER_EXISTS",
                message="A user with this email already exists. They may already be in your organization or another one.",
                severity=ErrorSeverity.INFO,
                http_status=409,
                retryable=False
            ).to_dict()
        
        # Check for existing pending invite (outside transaction; no state change)
        existing = TeamInvitationService._get_existing_invite(organization_id, email)
        if existing:
            return {
                "success": True,
                "token": existing["token"],
                "is_resend": True,
                "message": "Invitation resent successfully",
                "invite_id": existing["id"]
            }
        
        token = TeamInvitationService._generate_token()
        now = datetime.utcnow()
        expires_at = now + timedelta(days=INVITE_TOKEN_EXPIRY_DAYS)
        invite_id = secrets.token_hex(16)
        
        # Seat check and insert in one transaction to prevent over-allocating seats
        try:
            with atomic() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT seats_total, seats_used FROM organizations WHERE id = ?
                """, (organization_id,))
                row = cursor.fetchone()
                seats_total = (row["seats_total"] or 1) if row else 1
                seats_used = (row["seats_used"] or 0) if row else 0
                cursor.execute("""
                    SELECT COUNT(*) FROM organization_invitations
                    WHERE organization_id = ? AND status = 'pending'
                """, (organization_id,))
                pending_row = cursor.fetchone()
                pending = pending_row[0] if pending_row else 0
                if seats_used + pending >= seats_total:
                    raise QuotaExceededError()
                if pending >= MAX_PENDING_INVITES_PER_ORG:
                    raise TooManyPendingInvitesError()
                cursor.execute("""
                    INSERT INTO organization_invitations
                    (id, organization_id, email, role, token, invited_by, created_at, expires_at, status, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                """, (
                    invite_id, organization_id, email.lower().strip(), role, token,
                    invited_by, now.isoformat(), expires_at.isoformat(),
                    json.dumps(metadata or {})
                ))
        except QuotaExceededError:
            return quota_exceeded("team seats").to_dict()
        except TooManyPendingInvitesError:
            return AppError(
                category=ErrorCategory.BUSINESS_RULE_VIOLATION,
                code="TOO_MANY_PENDING_INVITES",
                message=f"Too many pending invitations. Maximum is {MAX_PENDING_INVITES_PER_ORG}. Please cancel unused invitations.",
                severity=ErrorSeverity.INFO,
                http_status=400,
                retryable=False
            ).to_dict()
        
        # Get inviter info
        inviter_name = "Someone"
        org_name = "Your Organization"
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM users WHERE id = ?", (invited_by,))
            row = cursor.fetchone()
            if row:
                inviter_name = row["name"]
            
            cursor.execute("SELECT name FROM organizations WHERE id = ?", (organization_id,))
            row = cursor.fetchone()
            if row:
                org_name = row["name"]
        
        return {
            "success": True,
            "token": token,
            "invite_id": invite_id,
            "is_resend": False,
            "email": email,
            "role": role,
            "expires_at": expires_at.isoformat(),
            "inviter_name": inviter_name,
            "org_name": org_name,
            "message": "Invitation created successfully"
        }
    
    @staticmethod
    def validate_invitation(token: str) -> Dict[str, Any]:
        """
        Validate an invitation token.
        """
        if not token:
            return validation_error(field="token", message="Token is required").to_dict()
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT oi.id, oi.organization_id, oi.email, oi.role, oi.expires_at,
                       oi.status, oi.metadata, o.name as org_name,
                       u.name as inviter_name
                FROM organization_invitations oi
                JOIN organizations o ON oi.organization_id = o.id
                JOIN users u ON oi.invited_by = u.id
                WHERE oi.token = ?
            """, (token,))
            row = cursor.fetchone()
            
            if not row:
                return {"valid": False, "error": "Invalid invitation link"}
            
            invite = dict(row)
            
            # Check status
            if invite["status"] != "pending":
                if invite["status"] == "accepted":
                    return {"valid": False, "error": "This invitation has already been accepted"}
                if invite["status"] == "canceled":
                    return {"valid": False, "error": "This invitation has been canceled"}
                if invite["status"] == "expired":
                    return {"valid": False, "error": "This invitation has expired"}
            
            # Check expiration
            expires_at = datetime.fromisoformat(invite["expires_at"])
            if datetime.utcnow() > expires_at:
                # Mark as expired safely
                with atomic() as write_conn:
                    write_cursor = write_conn.cursor()
                    write_cursor.execute(
                        "UPDATE organization_invitations SET status = 'expired' WHERE id = ?",
                        (invite["id"],)
                    )
                return {"valid": False, "error": "This invitation has expired"}
            
            # Check if user already exists (edge case)
            cursor.execute("SELECT id FROM users WHERE email = ?", (invite["email"],))
            if cursor.fetchone():
                return {"valid": False, "error": "An account with this email already exists"}
            
            return {
                "valid": True,
                "invite_id": invite["id"],
                "organization_id": invite["organization_id"],
                "org_name": invite["org_name"],
                "email": invite["email"],
                "role": invite["role"],
                "inviter_name": invite["inviter_name"],
                "expires_at": invite["expires_at"]
            }
    
    @staticmethod
    def accept_invitation(token: str, name: str, password: str) -> Dict[str, Any]:
        """
        Accept an invitation and create user account.
        """
        # Validate invitation
        validation = TeamInvitationService.validate_invitation(token)
        if not validation.get("valid"):
            return validation
        
        # Validate inputs
        if not name or len(name) < 2:
            return validation_error(field="name", message="Name must be at least 2 characters").to_dict()
        
        if len(password) < 8:
            return {"success": False, "error": "Password must be at least 8 characters"}
        
        if not any(c.isupper() for c in password):
            return {"success": False, "error": "Password must contain at least one uppercase letter"}
        
        if not any(c.islower() for c in password):
            return {"success": False, "error": "Password must contain at least one lowercase letter"}
        
        if not any(c.isdigit() for c in password):
            return {"success": False, "error": "Password must contain at least one number"}
        
        # Check again if user exists (race condition protection)
        existing = TeamInvitationService._user_exists(validation["email"])
        if existing:
            return {"success": False, "error": "An account with this email already exists"}
        
        # Create user
        from app.auth import hash_password
        import uuid
        
        user_id = str(uuid.uuid4())
        password_hash = hash_password(password)
        now = datetime.utcnow().isoformat()
        
        # Use IMMEDIATE isolation level transaction for critical multi-statement signup
        tx_options = TransactionOptions(isolation_level=IsolationLevel.IMMEDIATE)
        
        with transaction(tx_options) as conn:
            cursor = conn.cursor()
            
            # Create user
            cursor.execute("""
                INSERT INTO users (id, email, name, password_hash, role, company_id, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                user_id, validation["email"], name, password_hash,
                validation["role"], validation["organization_id"], now
            ))
            
            # Add to organization members
            member_id = secrets.token_hex(16)
            cursor.execute("""
                INSERT INTO organization_members
                (id, organization_id, user_id, role, is_active, invited_by, joined_at)
                VALUES (?, ?, ?, ?, 1, ?, ?)
            """, (
                member_id, validation["organization_id"], user_id,
                validation["role"], validation["invite_id"], now
            ))
            
            # Update invitation status
            cursor.execute("""
                UPDATE organization_invitations
                SET status = 'accepted', accepted_at = ?, accepted_by = ?
                WHERE id = ?
            """, (now, user_id, validation["invite_id"]))
            
            # Update organization seats_used
            cursor.execute("""
                UPDATE organizations
                SET seats_used = seats_used + 1, updated_at = ?
                WHERE id = ?
            """, (now, validation["organization_id"]))
            
            # conn.commit() is automatic on success
        
        # Create auth token
        from app.auth import create_access_token
        auth_token = create_access_token(user_id)
        
        return {
            "success": True,
            "message": "Invitation accepted successfully",
            "user_id": user_id,
            "token": auth_token,
            "email": validation["email"],
            "organization_id": validation["organization_id"],
            "org_name": validation["org_name"]
        }
    
    @staticmethod
    def cancel_invitation(invite_id: str, canceled_by: str) -> Dict[str, Any]:
        """
        Cancel a pending invitation.
        """
        # Using atomic for read+update consistency
        with atomic() as conn:
            cursor = conn.cursor()
            
            # Verify the invite exists and belongs to the user's org
            cursor.execute("""
                SELECT oi.id, oi.organization_id, oi.status, o.owner_user_id
                FROM organization_invitations oi
                JOIN organizations o ON oi.organization_id = o.id
                WHERE oi.id = ?
            """, (invite_id,))
            row = cursor.fetchone()
            
            if not row:
                return not_found("Invitation").to_dict()
            
            invite = dict(row)
            
            # Check permissions (must be org owner or admin)
            cursor.execute("""
                SELECT role FROM organization_members
                WHERE organization_id = ? AND user_id = ?
            """, (invite["organization_id"], canceled_by))
            perm_row = cursor.fetchone()
            
            is_owner = invite["owner_user_id"] == canceled_by
            is_admin = perm_row and perm_row["role"] == "admin"
            
            if not (is_owner or is_admin):
                return forbidden().to_dict()
            
            if invite["status"] != "pending":
                return {"success": False, "error": "Can only cancel pending invitations"}
            
            # Cancel the invitation
            cursor.execute("""
                UPDATE organization_invitations SET status = 'canceled' WHERE id = ?
            """, (invite_id,))
            
            return {"success": True, "message": "Invitation canceled"}
    
    @staticmethod
    def list_invitations(organization_id: str) -> List[Dict[str, Any]]:
        """
        List all invitations for an organization.
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT oi.id, oi.email, oi.role, oi.status, oi.created_at,
                       oi.expires_at, oi.accepted_at, u.name as invited_by_name
                FROM organization_invitations oi
                LEFT JOIN users u ON oi.invited_by = u.id
                WHERE oi.organization_id = ?
                ORDER BY oi.created_at DESC
            """, (organization_id,))
            
            invites = []
            for row in cursor.fetchall():
                invite = dict(row)
                # Check if expired
                if invite["status"] == "pending":
                    expires = datetime.fromisoformat(invite["expires_at"])
                    if datetime.utcnow() > expires:
                        invite["status"] = "expired"
                invites.append(invite)
            
            return invites
    
    @staticmethod
    def cleanup_expired_invitations() -> int:
        """Mark expired invitations as expired (run as scheduled job)."""
        with atomic() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                UPDATE organization_invitations
                SET status = 'expired'
                WHERE status = 'pending' AND expires_at < ?
            """, (now,))
            updated = cursor.rowcount
            return updated
