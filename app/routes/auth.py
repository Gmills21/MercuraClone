"""
Authentication API routes.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
import re

from app.auth import (
    authenticate_user, create_user, create_access_token,
    get_current_user, logout_user, User, list_users, check_permission
)
from app.database_sqlite import get_db
from app.middleware.csrf import get_csrf_token
import hashlib
import hmac

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


class UserCreateRequest(BaseModel):
    email: str
    name: str
    password: str
    role: str = "sales_rep"


class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str
    company_name: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets security requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class RegisterResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict
    organization_id: str
    onboarding_required: bool = True


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    created_at: str
    last_login: Optional[str]


async def get_current_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from bearer token."""
    token = credentials.credentials
    user = get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login and get access token."""
    user = authenticate_user(request.email, request.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(user.id)
    
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role
        }
    )


@router.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest):
    """Register a new user with organization. Self-service signup."""
    import uuid
    from app.auth import _hash_password
    
    now = datetime.utcnow().isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (request.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create organization
        org_id = str(uuid.uuid4())
        org_slug = request.company_name.lower().replace(" ", "-").replace("_", "-")
        # Ensure unique slug
        base_slug = org_slug
        counter = 1
        while True:
            cursor.execute("SELECT id FROM organizations WHERE slug = ?", (org_slug,))
            if not cursor.fetchone():
                break
            org_slug = f"{base_slug}-{counter}"
            counter += 1
        
        cursor.execute("""
            INSERT INTO organizations (id, name, slug, owner_user_id, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'trial', ?, ?)
        """, (org_id, request.company_name, org_slug, "temp", now, now))
        
        # Create user
        user_id = str(uuid.uuid4())
        password_hash = _hash_password(request.password)
        
        cursor.execute("""
            INSERT INTO users (id, email, name, password_hash, role, company_id, created_at, is_active)
            VALUES (?, ?, ?, ?, 'admin', ?, ?, ?)
        """, (user_id, request.email, request.name, password_hash, org_id, now, 1))
        
        # Update organization owner
        cursor.execute("UPDATE organizations SET owner_user_id = ? WHERE id = ?", (user_id, org_id))
        
        # Create organization member
        member_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO organization_members (id, organization_id, user_id, role, joined_at)
            VALUES (?, ?, ?, 'admin', ?)
        """, (member_id, org_id, user_id, now))
        
        conn.commit()
    
    # Create access token
    token = create_access_token(user_id)
    
    return RegisterResponse(
        access_token=token,
        token_type="bearer",
        user={
            "id": user_id,
            "email": request.email,
            "name": request.name,
            "role": "admin"
        },
        organization_id=org_id,
        onboarding_required=True
    )


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout and invalidate token."""
    token = credentials.credentials
    logout_user(token)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user_token)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.post("/users", response_model=UserResponse)
async def create_new_user(
    request: UserCreateRequest,
    current_user: User = Depends(get_current_user_token)
):
    """Create a new user. Requires admin or manager role."""
    if not check_permission(current_user, "manager"):
        raise HTTPException(status_code=403, detail="Requires manager or admin role")
    
    # Validate role
    valid_roles = ["viewer", "sales_rep", "manager", "admin"]
    if request.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
    
    user = create_user(
        email=request.email,
        name=request.name,
        password=request.password,
        role=request.role
    )
    
    if not user:
        raise HTTPException(status_code=400, detail="Failed to create user (email may exist)")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: User = Depends(get_current_user_token)):
    """List all users in company. Requires admin or manager role."""
    if not check_permission(current_user, "manager"):
        raise HTTPException(status_code=403, detail="Requires manager or admin role")
    
    users = list_users(current_user.company_id)
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            name=u.name,
            role=u.role,
            created_at=u.created_at,
            last_login=u.last_login
        )
        for u in users
    ]


# CSRF Token endpoint
class CSRFTokenResponse(BaseModel):
    csrf_token: str


@router.get("/csrf-token", response_model=CSRFTokenResponse)
async def get_csrf_token_endpoint(request: Request):
    """
    Get a CSRF token for state-changing operations.
    
    The token should be included in the X-CSRF-Token header for all
    POST, PUT, PATCH, and DELETE requests.
    """
    # Generate token based on session
    from app.middleware.csrf import CSRFMiddleware
    
    # Get session identifier
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        session_id = auth_header[7:]
    else:
        ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "")
        session_id = hashlib.sha256(f"{ip}:{user_agent}".encode()).hexdigest()[:32]
    
    # Generate token using same logic as middleware
    secret_key = os.getenv("CSRF_SECRET_KEY") or os.getenv("JWT_SECRET_KEY") or "dev-secret-key-change-in-production"
    timestamp = datetime.utcnow().isoformat()
    data = f"{session_id}:{timestamp}"
    token = hmac.new(
        secret_key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:32]
    
    return CSRFTokenResponse(csrf_token=f"{token}:{timestamp}")
