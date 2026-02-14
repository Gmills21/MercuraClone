"""
Smart Alerts API Routes - Production Ready
Organization-scoped alerts with real-time checks
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.alert_service import AlertService, AlertType, AlertPriority
from app.middleware.organization import get_current_user_and_org
from app.dependencies import require_admin

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/")
async def get_alerts(
    unread_only: bool = False,
    limit: int = 50,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get alerts for the current organization.
    Returns actionable alerts sorted by priority and recency.
    """
    user_id, org_id = user_org
    
    alerts = AlertService.get_user_alerts(
        organization_id=org_id,
        user_id=user_id,
        unread_only=unread_only,
        limit=limit
    )
    
    return {
        "alerts": alerts,
        "count": len(alerts),
        "unread_count": AlertService.get_unread_count(org_id, user_id)
    }


@router.get("/unread-count")
async def get_unread_count(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Get count of unread alerts (for notification badge)."""
    user_id, org_id = user_org
    
    count = AlertService.get_unread_count(org_id, user_id)
    return {"unread_count": count}


@router.post("/check")
async def run_alert_checks(
    user_org: tuple = Depends(require_admin)
):
    """
    Manually trigger alert checks.
    Creates new alerts for qualifying conditions.
    """
    user_id, org_id = user_org
    
    result = AlertService.run_all_checks(org_id, user_id)
    return result


@router.post("/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Mark a specific alert as read."""
    user_id, org_id = user_org
    
    success = AlertService.mark_read(org_id, alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {
        "success": True,
        "unread_count": AlertService.get_unread_count(org_id, user_id)
    }


@router.post("/mark-all-read")
async def mark_all_alerts_read(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Mark all alerts as read."""
    user_id, org_id = user_org
    
    count = AlertService.mark_all_read(org_id, user_id)
    return {
        "success": True,
        "marked_read": count,
        "unread_count": 0
    }


@router.delete("/{alert_id}")
async def dismiss_alert(
    alert_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Dismiss/delete an alert."""
    user_id, org_id = user_org
    
    success = AlertService.dismiss_alert(org_id, alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {
        "success": True,
        "unread_count": AlertService.get_unread_count(org_id, user_id)
    }


@router.get("/types")
async def get_alert_types():
    """
    Get available alert types and their descriptions.
    """
    return {
        "types": [
            {
                "id": AlertType.NEW_RFQ,
                "name": "New Quote Request",
                "description": "New RFQ email received - potential revenue",
                "priority": "high",
                "when": "When new email arrives within 24 hours"
            },
            {
                "id": AlertType.FOLLOW_UP_NEEDED,
                "name": "Follow-up Needed",
                "description": "Quote sent 3-7 days ago with no response",
                "priority": "high",
                "when": "3-7 days after quote is sent"
            },
            {
                "id": AlertType.QUOTE_EXPIRING,
                "name": "Quote Expiring",
                "description": "Quote expires in 7 days",
                "priority": "medium",
                "when": "21 days after quote is sent"
            }
        ]
    }
