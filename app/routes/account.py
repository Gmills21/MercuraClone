"""
Account self-service: deletion (soft-delete).
We retain billing/invoice data for audit and compliance; account is deactivated, not purged.
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from app.middleware.organization import get_current_user_and_org
from app.database_sqlite import get_db, get_user_by_id
from app.auth_enhanced import SessionService

router = APIRouter(prefix="/account", tags=["account"])


@router.post("/delete")
async def delete_account(user_org: tuple = Depends(get_current_user_and_org)):
    """
    Soft-delete the current user's account.
    - Sets user to inactive and records deleted_at (data retained for audit/compliance).
    - Revokes all sessions so the user is logged out immediately.
    For full data purge (e.g. GDPR right to erasure), contact support; we retain
    invoice/subscription records where required by law.
    """
    user_id, org_id = user_org

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Account is already deactivated")

    now = datetime.utcnow().isoformat()
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET is_active = 0, deleted_at = ? WHERE id = ?",
                (now, user_id),
            )
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=500, detail="Failed to update account")
        SessionService.revoke_all_sessions(user_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Account deletion failed")

    return {
        "success": True,
        "message": "Your account has been deactivated. You have been logged out. For full data removal, contact support.",
    }
