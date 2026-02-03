"""
Analytics API routes for quote performance and metrics.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from app.analytics import get_quote_statistics, get_sales_velocity_metrics
# from app.auth import get_current_user, User, check_permission
from app.middleware.organization import get_current_user_and_org

router = APIRouter(prefix="/analytics", tags=["analytics"])


class AnalyticsResponse(BaseModel):
    period_days: int
    summary: dict
    by_status: dict
    daily_trend: list
    top_customers: list
    conversion_metrics: dict


@router.get("/quotes", response_model=AnalyticsResponse)
async def get_quote_analytics(
    days: int = 30,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get quote analytics for the specified period.
    Requires authentication.
    """
    # Assuming get_quote_statistics needs org aware update, but for now just securing endpoint
    try:
        stats = get_quote_statistics(days)
        return AnalyticsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/velocity")
async def get_velocity_metrics(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get sales velocity and ROI metrics.
    Shows time savings and efficiency gains.
    """
    # sales velocity is likely organization-wide, we should pass org_id if metrics support it
    # For now, just securing the endpoint
    
    try:
        metrics = get_sales_velocity_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard_summary(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get complete dashboard data for the current user.
    Includes quotes, customers, and performance metrics.
    """
    user_id, org_id = user_org
    
    from app.database_sqlite import list_customers, list_quotes, list_products, get_user_by_id
    
    try:
        # Get user details
        user = get_user_by_id(user_id)
        
        # Get basic counts
        customers = list_customers(organization_id=org_id, limit=1000)
        quotes = list_quotes(organization_id=org_id, limit=1000)
        products = list_products(organization_id=org_id, limit=1000)
        
        # Get analytics
        stats = get_quote_statistics(30)
        velocity = get_sales_velocity_metrics()
        
        return {
            "user": {
                "name": user.get("name") if user else "Unknown",
                "role": user.get("role") if user else "user",
                "email": user.get("email") if user else "unknown@email.com"
            },
            "counts": {
                "customers": len(customers),
                "quotes": len(quotes),
                "products": len(products)
            },
            "performance": stats["summary"],
            "velocity": velocity["velocity"],
            "time_savings": velocity["time_savings"],
            "recent_quotes": quotes[:5],
            "top_customers": stats["top_customers"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
