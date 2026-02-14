"""Organization context middleware."""
from fastapi import Header, HTTPException, Depends
from typing import Optional, Tuple
from app.auth_enhanced import SessionService
from app.auth import get_current_user
from app.database_sqlite import get_or_create_default_organization


def _org_id_for_user(company_id: Optional[str]) -> str:
    """Resolve organization ID from user's company_id (e.g. 'default' -> actual default org)."""
    if company_id and company_id != "default":
        return company_id
    return get_or_create_default_organization()


async def get_current_organization(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> str:
    """Get organization ID from session or simple token fallback."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        session = SessionService.validate_session(token)
        if session:
            return session.get("organization_id")
        # Fallback: simple in-memory token from auth.create_access_token (e.g. /auth/login)
        user = get_current_user(token)
        if user:
            return _org_id_for_user(user.company_id)
    raise HTTPException(401, "Missing authorization")


async def get_current_user_and_org(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> Tuple[str, str]:
    """Get both user_id and organization_id. Session token first, then simple token fallback."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        session = SessionService.validate_session(token)
        if session:
            return session["user_id"], session["organization_id"]
        # Fallback: simple in-memory token from auth.create_access_token (e.g. /auth/login)
        user = get_current_user(token)
        if user:
            org_id = _org_id_for_user(user.company_id)
            return user.id, org_id
    raise HTTPException(401, "Missing authorization")
