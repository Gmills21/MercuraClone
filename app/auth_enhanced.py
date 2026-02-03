"""
Enhanced Authentication Service
Adds session persistence, password reset, and improved security.
"""

import uuid
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from loguru import logger
import json

from app.database_sqlite import get_db
from app.auth import _hash_password, _verify_password, User


class SessionService:
    """Persistent session management (replaces in-memory tokens)."""
    
    @staticmethod
    def create_session(
        user_id: str,
        organization_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        remember_me: bool = False
    ) -> str:
        """
        Create a new session and return the token.
        Sessions are stored in database for persistence across restarts.
        """
        session_id = str(uuid.uuid4())
        token = secrets.token_urlsafe(32)
        now = datetime.utcnow()
        
        # Remember me = 30 days, otherwise 24 hours
        expires_delta = timedelta(days=30 if remember_me else 1)
        expires = now + expires_delta
        
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sessions (
                        id, user_id, token, organization_id,
                        created_at, expires_at, last_used_at,
                        user_agent, ip_address, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id, user_id, token, organization_id,
                    now.isoformat(), expires.isoformat(), now.isoformat(),
                    user_agent, ip_address, True
                ))
                conn.commit()
                
                logger.info(f"Created session for user {user_id}: {session_id}")
                return token
                
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    @staticmethod
    def validate_session(token: str) -> Optional[Dict[str, Any]]:
        """
        Validate session token and return session info.
        Returns None if invalid or expired.
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sessions
                WHERE token = ? AND is_active = 1
            """, (token,))
            session = cursor.fetchone()
            
            if not session:
                return None
            
            # Check expiration
            expires_at = datetime.fromisoformat(session["expires_at"])
            if datetime.utcnow() > expires_at:
                # Expire the session
                cursor.execute("""
                    UPDATE sessions SET is_active = 0 WHERE id = ?
                """, (session["id"],))
                conn.commit()
                return None
            
            # Update last_used_at
            cursor.execute("""
                UPDATE sessions SET last_used_at = ? WHERE id = ?
            """, (datetime.utcnow().isoformat(), session["id"]))
            conn.commit()
            
            return {
                "session_id": session["id"],
                "user_id": session["user_id"],
                "organization_id": session["organization_id"],
                "created_at": session["created_at"],
                "expires_at": session["expires_at"]
            }
    
    @staticmethod
    def revoke_session(token: str) -> bool:
        """Revoke a session (logout)."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sessions SET is_active = 0
                WHERE token = ?
            """, (token,))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def list_user_sessions(user_id: str) -> list:
        """List all active sessions for a user."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, created_at, last_used_at, user_agent, ip_address, expires_at
                FROM sessions
                WHERE user_id = ? AND is_active = 1
                ORDER BY last_used_at DESC
            """, (user_id,))
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    "id": row["id"],
                    "created_at": row["created_at"],
                    "last_used_at": row["last_used_at"],
                    "user_agent": row["user_agent"],
                    "ip_address": row["ip_address"],
                    "expires_at": row["expires_at"]
                })
            return sessions
    
    @staticmethod
    def revoke_all_sessions(user_id: str, except_session_id: Optional[str] = None) -> int:
        """Revoke all sessions for a user (except optionally one)."""
        with get_db() as conn:
            cursor = conn.cursor()
            if except_session_id:
                cursor.execute("""
                    UPDATE sessions SET is_active = 0
                    WHERE user_id = ? AND id != ?
                """, (user_id, except_session_id))
            else:
                cursor.execute("""
                    UPDATE sessions SET is_active = 0
                    WHERE user_id = ?
                """, (user_id,))
            conn.commit()
            return cursor.rowcount


class PasswordResetService:
    """Handle password reset flow."""
    
    @staticmethod
    def create_reset_token(user_email: str) -> Optional[str]:
        """
        Create a password reset token for user.
        Returns the token if successful.
        """
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Get user ID from email
                cursor.execute("SELECT id FROM users WHERE email = ?", (user_email,))
                user = cursor.fetchone()
                
                if not user:
                    logger.warning(f"Password reset requested for non-existent email: {user_email}")
                    # Don't reveal that email doesn't exist
                    return None
                
                user_id = user["id"]
                
                # Create reset token
                token_id = str(uuid.uuid4())
                token = secrets.token_urlsafe(32)
                now = datetime.utcnow()
                expires = now + timedelta(hours=1)  # 1 hour expiration
                
                cursor.execute("""
                    INSERT INTO password_reset_tokens (
                        id, user_id, token, created_at, expires_at, is_used
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    token_id, user_id, token,
                    now.isoformat(), expires.isoformat(), False
                ))
                conn.commit()
                
                logger.info(f"Created password reset token for user {user_id}")
                return token
                
        except Exception as e:
            logger.error(f"Error creating password reset token: {e}")
            return None
    
    @staticmethod
    def validate_reset_token(token: str) -> Optional[str]:
        """
        Validate a password reset token.
        Returns user_id if valid, None otherwise.
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM password_reset_tokens
                WHERE token = ? AND is_used = 0
            """, (token,))
            reset = cursor.fetchone()
            
            if not reset:
                return None
            
            # Check expiration
            expires_at = datetime.fromisoformat(reset["expires_at"])
            if datetime.utcnow() > expires_at:
                logger.warning(f"Password reset token expired: {token}")
                return None
            
            return reset["user_id"]
    
    @staticmethod
    def reset_password(token: str, new_password: str) -> bool:
        """
        Reset user password using a valid token.
        """
        user_id = PasswordResetService.validate_reset_token(token)
        if not user_id:
            return False
        
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Update password
                password_hash = _hash_password(new_password)
                cursor.execute("""
                    UPDATE users SET password_hash = ? WHERE id = ?
                """, (password_hash, user_id))
                
                # Mark token as used
                cursor.execute("""
                    UPDATE password_reset_tokens
                    SET is_used = 1, used_at = ?
                    WHERE token = ?
                """, (datetime.utcnow().isoformat(), token))
                
                # Revoke all sessions for security
                cursor.execute("""
                    UPDATE sessions SET is_active = 0 WHERE user_id = ?
                """, (user_id,))
                
                conn.commit()
                
                logger.info(f"Password reset successful for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            return False


class EnhancedAuthService:
    """Enhanced authentication with all the features."""
    
    @staticmethod
    def register_user(
        email: str,
        name: str,
        password: str,
        organization_name: Optional[str] = None,
        organization_slug: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Register a new user and optionally create their organization.
        Returns user info and access token.
        """
        from app.organization_service import OrganizationService
        
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                
                # Check if email exists
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                if cursor.fetchone():
                    logger.error(f"Email already registered: {email}")
                    return None
                
                # Create user
                user_id = str(uuid.uuid4())
                now = datetime.utcnow().isoformat()
                password_hash = _hash_password(password)
                
                cursor.execute("""
                    INSERT INTO users (
                        id, email, name, password_hash, role, company_id,
                        created_at, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, email, name, password_hash, 'owner', 'default',
                    now, True
                ))
                conn.commit()
                
                # Create organization if provided
                org_id = None
                if organization_name and organization_slug:
                    org = OrganizationService.create_organization(
                        name=organization_name,
                        slug=organization_slug,
                        owner_user_id=user_id
                    )
                    if org:
                        org_id = org.id
                
                # Create session
                token = SessionService.create_session(
                    user_id=user_id,
                    organization_id=org_id,
                    remember_me=True
                )
                
                logger.info(f"Registered new user: {email}")
                
                return {
                    "user_id": user_id,
                    "email": email,
                    "name": name,
                    "organization_id": org_id,
                    "access_token": token
                }
                
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return None
    
    @staticmethod
    def login_user(
        email: str,
        password: str,
        remember_me: bool = False,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Login user and create session.
        Returns user info and access token.
        """
        from app.auth import authenticate_user
        
        user = authenticate_user(email, password)
        if not user:
            return None
        
        # Get user's primary organization
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT organization_id FROM organization_members
                WHERE user_id = ? AND is_active = 1
                ORDER BY joined_at ASC
                LIMIT 1
            """, (user.id,))
            org_row = cursor.fetchone()
            org_id = org_row["organization_id"] if org_row else user.company_id
        
        # Create session
        token = SessionService.create_session(
            user_id=user.id,
            organization_id=org_id,
            remember_me=remember_me,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        return {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "organization_id": org_id,
            "access_token": token
        }
    
    @staticmethod
    def change_password(user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password (requires old password)."""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT password_hash FROM users WHERE id = ?
                """, (user_id,))
                user = cursor.fetchone()
                
                if not user:
                    return False
                
                # Verify old password
                if not _verify_password(old_password, user["password_hash"]):
                    logger.warning(f"Invalid old password for user {user_id}")
                    return False
                
                # Update password
                new_hash = _hash_password(new_password)
                cursor.execute("""
                    UPDATE users SET password_hash = ? WHERE id = ?
                """, (new_hash, user_id))
                conn.commit()
                
                logger.info(f"Password changed for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            return False
