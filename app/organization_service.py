"""
Organization Service
Handles organization/company management, team invitations, and data isolation.
"""

import uuid
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from loguru import logger

from app.database_sqlite import get_db
from app.models_organization import (
    Organization, OrganizationMember, OrganizationInvitation,
    OrganizationStatus
)


class OrganizationService:
    """Service for managing organizations and team members."""
    
    @staticmethod
    def create_organization(
        name: str,
        slug: str,
        owner_user_id: str,
        trial_days: int = 14
    ) -> Optional[Organization]:
        """
        Create a new organization.
        """
        org_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        trial_ends = (datetime.utcnow() + timedelta(days=trial_days)).isoformat()
        
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Check if slug is available
                cursor.execute("SELECT id FROM organizations WHERE slug = ?", (slug,))
                if cursor.fetchone():
                    logger.error(f"Organization slug '{slug}' already exists")
                    return None
                
                # Create organization
                cursor.execute("""
                    INSERT INTO organizations (
                        id, name, slug, owner_user_id, status,
                        seats_total, seats_used, settings, branding,
                        created_at, updated_at, trial_ends_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    org_id, name, slug, owner_user_id, OrganizationStatus.TRIAL,
                    1, 1, json.dumps({}), json.dumps({}),
                    now, now, trial_ends
                ))
                
                # Add owner as member
                member_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO organization_members (
                        id, organization_id, user_id, role, is_active, joined_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (member_id, org_id, owner_user_id, 'owner', True, now))
                
                # Update user's company_id to match org_id
                cursor.execute("""
                    UPDATE users SET company_id = ? WHERE id = ?
                """, (org_id, owner_user_id))
                
                conn.commit()
                
                logger.info(f"Created organization: {slug} (ID: {org_id})")
                
                return Organization(
                    id=org_id,
                    name=name,
                    slug=slug,
                    owner_user_id=owner_user_id,
                    status=OrganizationStatus.TRIAL,
                    seats_total=1,
                    seats_used=1,
                    created_at=datetime.fromisoformat(now),
                    updated_at=datetime.fromisoformat(now),
                    trial_ends_at=datetime.fromisoformat(trial_ends)
                )
        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            return None
    
    @staticmethod
    def get_organization(org_id: str) -> Optional[Organization]:
        """Get organization by ID."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM organizations WHERE id = ?", (org_id,))
            row = cursor.fetchone()
            
            if row:
                return Organization(
                    id=row["id"],
                    name=row["name"],
                    slug=row["slug"],
                    domain=row["domain"],
                    owner_user_id=row["owner_user_id"],
                    subscription_id=row["subscription_id"],
                    status=OrganizationStatus(row["status"]),
                    seats_total=row["seats_total"],
                    seats_used=row["seats_used"],
                    settings=json.loads(row["settings"] or "{}"),
                    branding=json.loads(row["branding"] or "{}"),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    trial_ends_at=datetime.fromisoformat(row["trial_ends_at"]) if row["trial_ends_at"] else None,
                    metadata=json.loads(row["metadata"]) if row["metadata"] else None
                )
            return None
    
    @staticmethod
    def get_organization_by_slug(slug: str) -> Optional[Organization]:
        """Get organization by slug."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM organizations WHERE slug = ?", (slug,))
            row = cursor.fetchone()
            
            if row:
                return OrganizationService.get_organization(row["id"])
            return None
    
    @staticmethod
    def update_organization(org_id: str, updates: Dict[str, Any]) -> bool:
        """Update organization fields."""
        allowed_fields = ["name", "domain", "settings", "branding", "status"]
        
        set_parts = []
        values = []
        
        for key, value in updates.items():
            if key in allowed_fields:
                set_parts.append(f"{key} = ?")
                if key in ["settings", "branding"] and isinstance(value, dict):
                    values.append(json.dumps(value))
                else:
                    values.append(value)
        
        if not set_parts:
            return False
        
        values.append(datetime.utcnow().isoformat())
        values.append(org_id)
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE organizations 
                SET {', '.join(set_parts)}, updated_at = ?
                WHERE id = ?
            """, values)
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def list_user_organizations(user_id: str) -> List[Organization]:
        """List all organizations a user belongs to."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.* FROM organizations o
                JOIN organization_members om ON o.id = om.organization_id
                WHERE om.user_id = ? AND om.is_active = 1
                ORDER BY om.joined_at DESC
            """, (user_id,))
            
            orgs = []
            for row in cursor.fetchall():
                orgs.append(Organization(
                    id=row["id"],
                    name=row["name"],
                    slug=row["slug"],
                    domain=row["domain"],
                    owner_user_id=row["owner_user_id"],
                    subscription_id=row["subscription_id"],
                    status=OrganizationStatus(row["status"]),
                    seats_total=row["seats_total"],
                    seats_used=row["seats_used"],
                    settings=json.loads(row["settings"] or "{}"),
                    branding=json.loads(row["branding"] or "{}"),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    trial_ends_at=datetime.fromisoformat(row["trial_ends_at"]) if row["trial_ends_at"] else None
                ))
            return orgs
    
    @staticmethod
    def get_members(org_id: str) -> List[Dict[str, Any]]:
        """Get all members of an organization."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT om.*, u.email, u.name
                FROM organization_members om
                JOIN users u ON om.user_id = u.id
                WHERE om.organization_id = ? AND om.is_active = 1
                ORDER BY om.joined_at ASC
            """, (org_id,))
            
            members = []
            for row in cursor.fetchall():
                members.append({
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "email": row["email"],
                    "name": row["name"],
                    "role": row["role"],
                    "joined_at": row["joined_at"],
                    "last_active_at": row["last_active_at"]
                })
            return members
    
    @staticmethod
    def invite_member(
        org_id: str,
        email: str,
        role: str,
        invited_by: str
    ) -> Optional[OrganizationInvitation]:
        """Create an invitation for a new team member."""
        invite_id = str(uuid.uuid4())
        token = secrets.token_urlsafe(32)
        now = datetime.utcnow()
        expires = now + timedelta(days=7)
        
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Check if already invited or member
                cursor.execute("""
                    SELECT id FROM organization_invitations 
                    WHERE organization_id = ? AND email = ? AND status = 'pending'
                """, (org_id, email))
                if cursor.fetchone():
                    logger.error(f"User {email} already has pending invitation for org {org_id}")
                    return None
                
                cursor.execute("""
                    SELECT om.id FROM organization_members om
                    JOIN users u ON om.user_id = u.id
                    WHERE om.organization_id = ? AND u.email = ? AND om.is_active = 1
                """, (org_id, email))
                if cursor.fetchone():
                    logger.error(f"User {email} is already a member of org {org_id}")
                    return None
                
                # Create invitation
                cursor.execute("""
                    INSERT INTO organization_invitations (
                        id, organization_id, email, role, token,
                        invited_by, created_at, expires_at, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    invite_id, org_id, email, role, token,
                    invited_by, now.isoformat(), expires.isoformat(), 'pending'
                ))
                
                conn.commit()
                
                logger.info(f"Created invitation for {email} to org {org_id}")
                
                return OrganizationInvitation(
                    id=invite_id,
                    organization_id=org_id,
                    email=email,
                    role=role,
                    token=token,
                    invited_by=invited_by,
                    created_at=now,
                    expires_at=expires,
                    status='pending'
                )
        except Exception as e:
            logger.error(f"Error creating invitation: {e}")
            return None
    
    @staticmethod
    def get_invitation_by_token(token: str) -> Optional[Dict[str, Any]]:
        """Get invitation details by token."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.*, o.name as org_name, o.slug as org_slug
                FROM organization_invitations i
                JOIN organizations o ON i.organization_id = o.id
                WHERE i.token = ?
            """, (token,))
            row = cursor.fetchone()
            
            if row:
                return {
                    "id": row["id"],
                    "organization_id": row["organization_id"],
                    "organization_name": row["org_name"],
                    "organization_slug": row["org_slug"],
                    "email": row["email"],
                    "role": row["role"],
                    "token": row["token"],
                    "expires_at": row["expires_at"],
                    "status": row["status"]
                }
            return None
    
    @staticmethod
    def accept_invitation(token: str, user_id: str) -> bool:
        """Accept an invitation and add user to organization."""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Get invitation
                cursor.execute("""
                    SELECT * FROM organization_invitations
                    WHERE token = ? AND status = 'pending'
                """, (token,))
                invite = cursor.fetchone()
                
                if not invite:
                    logger.error(f"Invitation not found or already used: {token}")
                    return False
                
                # Check expiration
                expires_at = datetime.fromisoformat(invite["expires_at"])
                if datetime.utcnow() > expires_at:
                    cursor.execute("""
                        UPDATE organization_invitations
                        SET status = 'expired'
                        WHERE id = ?
                    """, (invite["id"],))
                    conn.commit()
                    logger.error(f"Invitation expired: {token}")
                    return False
                
                # Add user to organization
                member_id = str(uuid.uuid4())
                now = datetime.utcnow().isoformat()
                
                cursor.execute("""
                    INSERT INTO organization_members (
                        id, organization_id, user_id, role, is_active, invited_by, joined_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    member_id,
                    invite["organization_id"],
                    user_id,
                    invite["role"],
                    True,
                    invite["invited_by"],
                    now
                ))
                
                # Mark invitation as accepted
                cursor.execute("""
                    UPDATE organization_invitations
                    SET status = 'accepted', accepted_at = ?, accepted_by = ?
                    WHERE id = ?
                """, (now, user_id, invite["id"]))
                
                # Update organization seats_used
                cursor.execute("""
                    UPDATE organizations
                    SET seats_used = seats_used + 1
                    WHERE id = ?
                """, (invite["organization_id"],))
                
                # Update user's company_id
                cursor.execute("""
                    UPDATE users SET company_id = ? WHERE id = ?
                """, (invite["organization_id"], user_id))
                
                conn.commit()
                
                logger.info(f"User {user_id} joined organization {invite['organization_id']}")
                return True
                
        except Exception as e:
            logger.error(f"Error accepting invitation: {e}")
            return False
    
    @staticmethod
    def remove_member(org_id: str, user_id: str) -> bool:
        """Remove a member from organization."""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Don't allow removing owner
                cursor.execute("""
                    SELECT owner_user_id FROM organizations WHERE id = ?
                """, (org_id,))
                org = cursor.fetchone()
                if org and org["owner_user_id"] == user_id:
                    logger.error(f"Cannot remove organization owner: {user_id}")
                    return False
                
                # Deactivate membership
                cursor.execute("""
                    UPDATE organization_members
                    SET is_active = 0
                    WHERE organization_id = ? AND user_id = ?
                """, (org_id, user_id))
                
                # Decrease seats_used
                cursor.execute("""
                    UPDATE organizations
                    SET seats_used = MAX(0, seats_used - 1)
                    WHERE id = ?
                """, (org_id,))
                
                conn.commit()
                
                logger.info(f"Removed user {user_id} from organization {org_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error removing member: {e}")
            return False
    
    @staticmethod
    def update_member_role(org_id: str, user_id: str, new_role: str) -> bool:
        """Update a member's role."""
        valid_roles = ['owner', 'admin', 'manager', 'sales_rep', 'viewer']
        if new_role not in valid_roles:
            return False
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE organization_members
                SET role = ?
                WHERE organization_id = ? AND user_id = ?
            """, (new_role, org_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
