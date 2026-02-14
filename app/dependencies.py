from fastapi import Depends, HTTPException
from app.middleware.organization import get_current_user_and_org
from app.database_sqlite import get_user_by_id

async def require_admin(user_org: tuple = Depends(get_current_user_and_org)):
    """
    Dependency to ensure the current user has 'admin' or 'owner' role.
    Returns (user_id, org_id) to maintain compatibility with existing code.
    """
    user_id, org_id = user_org
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if user.get("role") not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    return user_id, org_id

async def require_owner(user_org: tuple = Depends(get_current_user_and_org)):
    """
    Dependency to ensure the current user has 'owner' role.
    Returns (user_id, org_id).
    """
    user_id, org_id = user_org
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if user.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Owner privileges required")
    
    return user_id, org_id
