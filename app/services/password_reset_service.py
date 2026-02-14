"""
Password Reset Service
Handles secure password reset flow with time-limited tokens.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

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
    validation_error
)


RESET_TOKEN_EXPIRY_HOURS = 24
MAX_RESET_ATTEMPTS_PER_DAY = 3


class PasswordResetService:
    """Service for managing password reset tokens and flow."""
    
    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash the token for storage (prevents DB leak from being usable)."""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def _generate_token() -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def _get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.email, u.name, u.is_active, o.name as org_name
                FROM users u
                JOIN organization_members om ON u.id = om.user_id
                JOIN organizations o ON om.organization_id = o.id
                WHERE u.email = ? AND u.is_active = 1
                LIMIT 1
            """, (email.lower().strip(),))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    @staticmethod
    def _count_recent_attempts(user_id: str, hours: int = 24) -> int:
        """Count recent password reset attempts to prevent abuse."""
        with get_db() as conn:
            cursor = conn.cursor()
            since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            cursor.execute("""
                SELECT COUNT(*) FROM password_reset_tokens
                WHERE user_id = ? AND created_at > ?
            """, (user_id, since))
            row = cursor.fetchone()
            return row[0] if row else 0
    
    @staticmethod
    def create_reset_token(email: str) -> Dict[str, Any]:
        """
        Create a password reset token for the given email.
        Returns dict with success status and either token or error message.
        """
        user = PasswordResetService._get_user_by_email(email)
        
        if not user:
            # Return success even if user not found (prevents email enumeration)
            return {
                "success": True,
                "message": "If an account exists with this email, a reset link has been sent.",
                "token": None,
                "user": None
            }
        
        # Check rate limiting
        recent_attempts = PasswordResetService._count_recent_attempts(user["id"])
        if recent_attempts >= MAX_RESET_ATTEMPTS_PER_DAY:
            return AppError(
                category=ErrorCategory.RATE_LIMIT_ERROR,
                code="TOO_MANY_RESET_ATTEMPTS",
                message="Too many reset attempts. Please try again in 24 hours.",
                severity=ErrorSeverity.WARNING,
                http_status=429,
                retryable=True,
                retry_after_seconds=86400,
                suggested_action="Wait 24 hours before requesting another password reset."
            ).to_dict()
        
        # Generate token
        plain_token = PasswordResetService._generate_token()
        hashed_token = PasswordResetService._hash_token(plain_token)
        
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=RESET_TOKEN_EXPIRY_HOURS)
        
        # Store in database using atomic transaction
        with atomic() as conn:
            cursor = conn.cursor()
            token_id = secrets.token_hex(16)
            cursor.execute("""
                INSERT INTO password_reset_tokens (id, user_id, token, created_at, expires_at, is_used)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (token_id, user["id"], hashed_token, now.isoformat(), expires_at.isoformat()))
            # conn.commit() is automatic on success
        
        return {
            "success": True,
            "token": plain_token,
            "user": user,
            "expires_at": expires_at.isoformat(),
            "message": "Reset token created successfully"
        }
    
    @staticmethod
    def validate_token(token: str) -> Dict[str, Any]:
        """
        Validate a reset token and return user info if valid.
        """
        if not token:
            return validation_error(field="token", message="Token is required").to_dict()
        
        hashed_token = PasswordResetService._hash_token(token)
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT prt.id, prt.user_id, prt.expires_at, prt.is_used,
                       u.email, u.name, u.is_active
                FROM password_reset_tokens prt
                JOIN users u ON prt.user_id = u.id
                WHERE prt.token = ?
            """, (hashed_token,))
            row = cursor.fetchone()
            
            if not row:
                return {"valid": False, "error": "Invalid or expired token"}
            
            token_data = dict(row)
            
            # Check if already used
            if token_data["is_used"]:
                return {"valid": False, "error": "Token has already been used"}
            
            # Check expiration
            expires_at = datetime.fromisoformat(token_data["expires_at"])
            if datetime.utcnow() > expires_at:
                return {"valid": False, "error": "Token has expired"}
            
            # Check user is active
            if not token_data["is_active"]:
                return {"valid": False, "error": "User account is inactive"}
            
            return {
                "valid": True,
                "user_id": token_data["user_id"],
                "email": token_data["email"],
                "name": token_data["name"],
                "token_id": token_data["id"]
            }
    
    @staticmethod
    def reset_password(token: str, new_password: str) -> Dict[str, Any]:
        """
        Reset password using a valid token.
        """
        # Validate token first
        validation = PasswordResetService.validate_token(token)
        if not validation.get("valid"):
            return validation
        
        # Validate password strength
        if len(new_password) < 8:
            return validation_error(field="password", message="Password must be at least 8 characters").to_dict()
        
        if not any(c.isupper() for c in new_password):
            return validation_error(field="password", message="Password must contain at least one uppercase letter").to_dict()
        
        if not any(c.islower() for c in new_password):
            return validation_error(field="password", message="Password must contain at least one lowercase letter").to_dict()
        
        if not any(c.isdigit() for c in new_password):
            return validation_error(field="password", message="Password must contain at least one number").to_dict()
        
        # Hash new password
        from app.auth import hash_password
        password_hash = hash_password(new_password)
        
        now = datetime.utcnow().isoformat()
        
        # Use IMMEDIATE transaction for critical security updates
        tx_options = TransactionOptions(isolation_level=IsolationLevel.IMMEDIATE)
        
        with transaction(tx_options) as conn:
            cursor = conn.cursor()
            
            # Update password
            cursor.execute("""
                UPDATE users SET password_hash = ?, updated_at = ?
                WHERE id = ?
            """, (password_hash, now, validation["user_id"]))
            
            # Mark token as used
            hashed_token = PasswordResetService._hash_token(token)
            cursor.execute("""
                UPDATE password_reset_tokens
                SET is_used = 1, used_at = ?
                WHERE token = ?
            """, (now, hashed_token))
            
            # Invalidate all user sessions for security
            cursor.execute("""
                UPDATE sessions SET is_active = 0
                WHERE user_id = ?
            """, (validation["user_id"],))
            
            # conn.commit() is automatic
        
        return {
            "success": True,
            "message": "Password reset successfully",
            "email": validation["email"]
        }
    
    @staticmethod
    def cleanup_expired_tokens() -> int:
        """Delete expired tokens (run as scheduled job)."""
        with atomic() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                DELETE FROM password_reset_tokens
                WHERE expires_at < ? AND is_used = 1
            """, (now,))
            deleted = cursor.rowcount
            return deleted
