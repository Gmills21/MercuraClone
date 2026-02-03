"""
Business Impact API Routes
Serious metrics for serious business owners
"""

from fastapi import APIRouter
from typing import Optional

from app.business_impact_service import BusinessImpactService

router = APIRouter(prefix="/impact", tags=["business-impact"])


@router.get("/time-summary")
async def get_time_summary(user_id: str = "test-user", days: int = 30):
    """
    Get time savings summary.
    
    Returns:
    - Total hours saved
    - Breakdown by feature
    - Dollar value of time saved
    """
    return BusinessImpactService.get_time_summary(user_id, days)


@router.get("/quote-efficiency")
async def get_quote_efficiency(user_id: str = "test-user"):
    """
    Get quote efficiency metrics.
    
    Returns:
    - Quotes created
    - Win rate
    - Time saved on quoting
    - Revenue metrics
    """
    return BusinessImpactService.get_quote_efficiency(user_id)


@router.get("/follow-up-impact")
async def get_follow_up_impact(user_id: str = "test-user"):
    """
    Get follow-up alert impact.
    
    Returns:
    - Quotes needing follow-up
    - Conversion rate after follow-up
    - Revenue attributed to follow-ups
    """
    return BusinessImpactService.get_follow_up_impact(user_id)


@router.get("/roi")
async def get_roi_summary(user_id: str = "test-user"):
    """
    Get full ROI calculation.
    
    Returns:
    - Subscription cost
    - Value generated
    - ROI percentage
    - Payback period
    """
    return BusinessImpactService.get_roi_summary(user_id)


@router.get("/weekly-report")
async def get_weekly_report(user_id: str = "test-user"):
    """
    Get weekly business impact report.
    
    Comprehensive summary of:
    - Time saved
    - Quotes and revenue
    - ROI
    - Recommendations
    """
    return BusinessImpactService.get_weekly_report(user_id)


@router.post("/track")
async def track_time_saved(
    action_type: str,
    context: Optional[str] = "",
    user_id: str = "test-user"
):
    """
    Track time saved from an action.
    
    Action types:
    - smart_quote: AI quote creation
    - follow_up_alert: Acting on follow-up reminder
    - quickbooks_sync: QB integration sync
    - customer_lookup: Finding customer info
    - price_check: Competitive price check
    """
    impact = BusinessImpactService.record_time_saved(user_id, action_type, context)
    
    if impact:
        return {
            "recorded": True,
            "action": impact.action,
            "time_saved_minutes": impact.time_saved_minutes,
            "message": f"Saved {impact.time_saved_minutes} minutes"
        }
    
    return {"recorded": False, "error": "Unknown action type"}


@router.get("/dashboard")
async def get_impact_dashboard(user_id: str = "test-user"):
    """
    Get all impact metrics for dashboard display.
    Combined endpoint for efficiency.
    """
    return {
        "time_this_month": BusinessImpactService.get_time_summary(user_id, 30),
        "quote_efficiency": BusinessImpactService.get_quote_efficiency(user_id),
        "follow_up": BusinessImpactService.get_follow_up_impact(user_id),
        "roi": BusinessImpactService.get_roi_summary(user_id),
        "weekly": BusinessImpactService.get_weekly_report(user_id)
    }
