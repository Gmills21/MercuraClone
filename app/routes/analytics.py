"""
Analytics API routes for quote performance and metrics.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from app.analytics import get_quote_statistics, get_sales_velocity_metrics
from app.auth import get_current_user, User, check_permission

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
    current_user: User = Depends(get_current_user)
):
    """
    Get quote analytics for the specified period.
    Requires authentication.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        stats = get_quote_statistics(days)
        return AnalyticsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/velocity")
async def get_velocity_metrics(current_user: User = Depends(get_current_user)):
    """
    Get sales velocity and ROI metrics.
    Shows time savings and efficiency gains.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        metrics = get_sales_velocity_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard_summary(current_user: User = Depends(get_current_user)):
    """
    Get complete dashboard data for the current user.
    Includes quotes, customers, and performance metrics.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    from app.database_sqlite import list_customers, list_quotes, list_products
    
    try:
        # Get basic counts
        customers = list_customers(limit=1000)
        quotes = list_quotes(limit=1000)
        products = list_products(limit=1000)
        
        # Get analytics
        stats = get_quote_statistics(30)
        velocity = get_sales_velocity_metrics()
        
        return {
            "user": {
                "name": current_user.name,
                "role": current_user.role,
                "email": current_user.email
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
