"""
Smart Alerts API Routes - Minimal & Helpful
"""

from fastapi import APIRouter, HTTPException

from app.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/")
async def get_alerts(
    user_id: str = "test-user",
    unread_only: bool = False,
    limit: int = 20
):
    """
    Get alerts for the current user.
    Only returns essential, actionable alerts.
    """
    alerts = AlertService.get_user_alerts(user_id, unread_only, limit)
    return {
        "alerts": [a.to_dict() for a in alerts],
        "count": len(alerts),
        "unread_count": AlertService.get_unread_count(user_id)
    }


@router.get("/unread-count")
async def get_unread_count(user_id: str = "test-user"):
    """Get count of unread alerts (for badge)."""
    count = AlertService.get_unread_count(user_id)
    return {"unread_count": count}


@router.post("/check")
async def run_alert_checks(user_id: str = "test-user"):
    """Manually trigger alert checks."""
    result = AlertService.run_all_checks(user_id)
    return result


@router.post("/{alert_id}/read")
async def mark_alert_read(alert_id: str, user_id: str = "test-user"):
    """Mark a specific alert as read."""
    success = AlertService.mark_read(user_id, alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {
        "success": True,
        "unread_count": AlertService.get_unread_count(user_id)
    }


@router.post("/mark-all-read")
async def mark_all_alerts_read(user_id: str = "test-user"):
    """Mark all alerts as read."""
    count = AlertService.mark_all_read(user_id)
    return {
        "success": True,
        "marked_read": count,
        "unread_count": 0
    }


@router.delete("/{alert_id}")
async def dismiss_alert(alert_id: str, user_id: str = "test-user"):
    """Dismiss/delete an alert."""
    success = AlertService.dismiss_alert(user_id, alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {
        "success": True,
        "unread_count": AlertService.get_unread_count(user_id)
    }


@router.get("/types")
async def get_alert_types():
    """
    Get available alert types.
    Only 3 essential types to avoid noise.
    """
    return {
        "types": [
            {
                "id": "new_rfq",
                "name": "New Quote Request",
                "description": "New RFQ email received - money on the table",
                "priority": "high",
                "when": "When new email arrives"
            },
            {
                "id": "follow_up_needed",
                "name": "Follow-up Needed",
                "description": "Quote sent 3-7 days ago, no response - deal going cold",
                "priority": "high",
                "when": "3-7 days after sending quote"
            },
            {
                "id": "quote_expiring",
                "name": "Quote Expiring",
                "description": "Quote expires in 7 days - time sensitive",
                "priority": "medium",
                "when": "21 days after sending (7 days before expiration)"
            }
        ]
    }
