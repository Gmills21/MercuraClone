"""Organization context middleware."""
from fastapi import Header, HTTPException, Depends
from typing import Optional, Tuple
from app.auth_enhanced import SessionService
from app.database_sqlite import get_or_create_default_organization

async def get_current_organization(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> str:
    """Get organization ID from session or X-User-ID fallback."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        session = SessionService.validate_session(token)
        if session:
            return session.get("organization_id")
    # Removed dangerous fallback
    # if x_user_id:
    #     return get_or_create_default_organization()
    raise HTTPException(401, "Missing authorization")


async def get_current_user_and_org(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> Tuple[str, str]:
    """Get both user_id and organization_id. Uses Bearer session or X-User-ID fallback for dashboard."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        session = SessionService.validate_session(token)
        if session:
            return session["user_id"], session["organization_id"]
    # Removed dangerous fallback
    # if x_user_id:
    #     org_id = get_or_create_default_organization()
    #     return x_user_id, org_id
    raise HTTPException(401, "Missing authorization")
