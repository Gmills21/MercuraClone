"""
Business Impact API Routes
Serious metrics for serious business owners
"""

from fastapi import APIRouter, Depends
from typing import Optional
from pydantic import BaseModel

from app.business_impact_service import BusinessImpactService
from app.middleware.organization import get_current_user_and_org

router = APIRouter(prefix="/impact", tags=["business-impact"])


@router.get("/time-summary")
async def get_time_summary(
    days: int = 30,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get time savings summary.
    
    Returns:
    - Total hours saved
    - Breakdown by feature
    - Dollar value of time saved
    """
    user_id, org_id = user_org
    return BusinessImpactService.get_time_summary(user_id, org_id, days)


@router.get("/quote-efficiency")
async def get_quote_efficiency(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get quote efficiency metrics.
    
    Returns:
    - Quotes created
    - Win rate
    - Time saved on quoting
    - Revenue metrics
    """
    _, org_id = user_org
    return BusinessImpactService.get_quote_efficiency(org_id)


@router.get("/follow-up-impact")
async def get_follow_up_impact(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get follow-up alert impact.
    
    Returns:
    - Quotes needing follow-up
    - Conversion rate after follow-up
    - Revenue attributed to follow-ups
    """
    _, org_id = user_org
    return BusinessImpactService.get_follow_up_impact(org_id)


@router.get("/roi")
async def get_roi_summary(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get full ROI calculation.
    
    Returns:
    - Subscription cost
    - Value generated
    - ROI percentage
    - Payback period
    """
    user_id, org_id = user_org
    return BusinessImpactService.get_roi_summary(user_id, org_id)


@router.get("/weekly-report")
async def get_weekly_report(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get weekly business impact report.
    
    Comprehensive summary of:
    - Time saved
    - Quotes and revenue
    - ROI
    - Recommendations
    """
    user_id, org_id = user_org
    return BusinessImpactService.get_weekly_report(user_id, org_id)


@router.post("/track")
async def track_time_saved(
    action_type: str,
    context: Optional[str] = "",
    user_org: tuple = Depends(get_current_user_and_org)
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
    user_id, _ = user_org
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
async def get_impact_dashboard(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get all impact metrics for dashboard display.
    Combined endpoint for efficiency.
    """
    user_id, org_id = user_org
    return {
        "time_this_month": BusinessImpactService.get_time_summary(user_id, 30),
        "quote_efficiency": BusinessImpactService.get_quote_efficiency(org_id),
        "follow_up": BusinessImpactService.get_follow_up_impact(org_id),
        "roi": BusinessImpactService.get_roi_summary(user_id, org_id),
        "weekly": BusinessImpactService.get_weekly_report(user_id, org_id)
    }

class ROISimulationRequest(BaseModel):
    requests_per_year: int
    employees: int
    manual_time_mins: float
    avg_value_per_quote: float

@router.post("/simulate")
async def simulate_roi(request: ROISimulationRequest):
    """
    Calculate projected ROI based on simulated inputs.
    """
    return BusinessImpactService.calculate_roi_simulation(
        request.requests_per_year,
        request.employees,
        request.manual_time_mins,
        request.avg_value_per_quote
    )

