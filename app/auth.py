"""
User authentication and role management for multi-user support.
"""

import os
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# Simple token-based auth (no JWT for simplicity)
ACCESS_TOKEN_EXPIRE_DAYS = 30

# In-memory token store (use Redis in production)
_active_tokens: Dict[str, Dict[str, Any]] = {}


def _hash_password(password: str) -> str:
    """Hash password with salt."""
    salt = secrets.token_hex(16)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return salt + pwdhash.hex()


def _verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    salt = password_hash[:32]
    stored_hash = password_hash[32:]
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return pwdhash.hex() == stored_hash


@dataclass
class User:
    id: str
    email: str
    name: str
    role: str  # 'admin', 'sales_rep', 'manager', 'viewer'
    company_id: str
    password_hash: str
    created_at: str
    last_login: Optional[str] = None
    is_active: bool = True


# Default admin user (for initial setup)
DEFAULT_USERS = [
    {
        "id": "admin-001",
        "email": "admin@openmercura.local",
        "name": "System Admin",
        "role": "admin",
        "company_id": "default",
        "password_hash": _hash_password("admin123"),  # Change in production!
        "created_at": datetime.utcnow().isoformat(),
        "is_active": True
    }
]


def create_user(email: str, name: str, password: str, role: str = "sales_rep", company_id: str = "default") -> Optional[User]:
    """Create a new user."""
    from app.database_sqlite import get_db
    
    user_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (id, email, name, password_hash, role, company_id, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, email, name, _hash_password(password), role, company_id, now, True
            ))
            conn.commit()
            
            return User(
                id=user_id,
                email=email,
                name=name,
                role=role,
                company_id=company_id,
                password_hash="",
                created_at=now,
                is_active=True
            )
    except Exception as e:
        print(f"Error creating user: {e}")
        return None


def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate user and return user object."""
    from app.database_sqlite import get_db
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (email,))
        row = cursor.fetchone()
        
        if row and _verify_password(password, row["password_hash"]):
            # Update last login
            now = datetime.utcnow().isoformat()
            cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, row["id"]))
            conn.commit()
            
            return User(
                id=row["id"],
                email=row["email"],
                name=row["name"],
                role=row["role"],
                company_id=row["company_id"],
                password_hash="",
                created_at=row["created_at"],
                last_login=now,
                is_active=row["is_active"]
            )
    
    return None


def create_access_token(user_id: str) -> str:
    """Create new access token for user."""
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    
    _active_tokens[token] = {
        "user_id": user_id,
        "expires": expires.isoformat(),
        "created": datetime.utcnow().isoformat()
    }
    
    return token


def get_current_user(token: str) -> Optional[User]:
    """Get current user from token."""
    from app.database_sqlite import get_db
    
    token_data = _active_tokens.get(token)
    if not token_data:
        return None
    
    # Check expiration
    expires = datetime.fromisoformat(token_data["expires"])
    if datetime.utcnow() > expires:
        del _active_tokens[token]
        return None
    
    user_id = token_data["user_id"]
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ? AND is_active = 1", (user_id,))
        row = cursor.fetchone()
        
        if row:
            return User(
                id=row["id"],
                email=row["email"],
                name=row["name"],
                role=row["role"],
                company_id=row["company_id"],
                password_hash="",
                created_at=row["created_at"],
                last_login=row["last_login"],
                is_active=row["is_active"]
            )
    
    return None


def logout_user(token: str):
    """Logout user by invalidating token."""
    if token in _active_tokens:
        del _active_tokens[token]


def check_permission(user: User, required_role: str) -> bool:
    """Check if user has required permission level."""
    role_hierarchy = {
        "viewer": 0,
        "sales_rep": 1,
        "manager": 2,
        "admin": 3
    }
    
    user_level = role_hierarchy.get(user.role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level


def list_users(company_id: str) -> List[User]:
    """List all users in company."""
    from app.database_sqlite import get_db
    
    users = []
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE company_id = ?", (company_id,))
        for row in cursor.fetchall():
            users.append(User(
                id=row["id"],
                email=row["email"],
                name=row["name"],
                role=row["role"],
                company_id=row["company_id"],
                password_hash="",
                created_at=row["created_at"],
                last_login=row["last_login"],
                is_active=row["is_active"]
            ))
    
    return users
