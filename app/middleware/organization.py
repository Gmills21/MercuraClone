"""Organization context middleware."""
from fastapi import Header, HTTPException, Depends
from typing import Optional, Tuple
from app.auth_enhanced import SessionService

async def get_current_organization(
    authorization: Optional[str] = Header(None)
) -> str:
    """Get organization ID from session."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing authorization")
    
    token = authorization.replace("Bearer ", "")
    session = SessionService.validate_session(token)
    
    if not session:
        raise HTTPException(401, "Invalid session")
    
    return session.get("organization_id")


async def get_current_user_and_org(
    authorization: Optional[str] = Header(None)
) -> Tuple[str, str]:
    """Get both user_id and organization_id."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing authorization")
    
    token = authorization.replace("Bearer ", "")
    session = SessionService.validate_session(token)
    
    if not session:
        raise HTTPException(401, "Invalid session")
    
    return session["user_id"], session["organization_id"]
