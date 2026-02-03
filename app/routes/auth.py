"""
Authentication API routes.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List

from app.auth import (
    authenticate_user, create_user, create_access_token,
    get_current_user, logout_user, User, list_users, check_permission
)

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
