"""
Customer Intelligence API Routes
Simple, actionable insights for sales teams
"""

from fastapi import APIRouter, HTTPException, Depends

from app.customer_intelligence_service import CustomerIntelligenceService
from app.middleware.organization import get_current_user_and_org

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.get("/customers/{customer_id}")
async def get_customer_intelligence(
    customer_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get complete intelligence profile for a customer.
    Returns health score, insights, metrics, and predictions.
    """
    user_id, org_id = user_org
    result = CustomerIntelligenceService.analyze_customer(customer_id, org_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    # Convert insights to dicts
    result["insights"] = [
        {
            "type": i.type,
            "title": i.title,
            "description": i.description,
            "action": i.action,
            "action_link": i.action_link,
            "impact": i.impact,
            "metric_value": i.metric_value,
            "metric_label": i.metric_label,
        }
        for i in result["insights"]
    ]
    
    return result


@router.get("/customers")
async def get_customer_list_intelligence(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get intelligence summary for all customers.
    Categorized into VIP, Active, At-Risk, and New.
    """
    user_id, org_id = user_org
    return CustomerIntelligenceService.get_customer_list_intelligence(org_id)


@router.get("/customers/{customer_id}/health")
async def get_customer_health(
    customer_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get simple health score for a customer (0-100).
    Includes explanation of what the score means.
    """
    user_id, org_id = user_org
    result = CustomerIntelligenceService.analyze_customer(customer_id, org_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result["health_score"]


@router.get("/customers/{customer_id}/insights")
async def get_customer_insights(
    customer_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get actionable insights for a customer.
    Each insight includes what to do and why.
    """
    user_id, org_id = user_org
    result = CustomerIntelligenceService.analyze_customer(customer_id, org_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return {
        "insights": [
            {
                "type": i.type,
                "title": i.title,
                "description": i.description,
                "action": i.action,
                "action_link": i.action_link,
                "impact": i.impact,
                "metric_value": i.metric_value,
                "metric_label": i.metric_label,
            }
            for i in result["insights"]
        ]
    }


@router.get("/customers/{customer_id}/predictions")
async def get_customer_predictions(
    customer_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get predictions about a customer's future behavior.
    Includes confidence levels and explanations.
    """
    user_id, org_id = user_org
    result = CustomerIntelligenceService.analyze_customer(customer_id, org_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return {"predictions": result["predictions"]}


@router.get("/dashboard")
async def get_intelligence_dashboard(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get summary data for the intelligence dashboard.
    Top insights, at-risk customers, opportunities.
    """
    user_id, org_id = user_org
    list_intel = CustomerIntelligenceService.get_customer_list_intelligence(org_id)
    
    # Get top insights from at-risk and VIP customers
    top_insights = []
    
    # Sample a few at-risk customers for urgent insights
    for customer in list_intel["categories"]["at_risk"][:3]:
        intel = CustomerIntelligenceService.analyze_customer(customer["id"], org_id)
        if "insights" in intel:
            for insight in intel["insights"]:
                if insight.impact == "high":
                    top_insights.append({
                        "customer_name": customer["name"],
                        "customer_id": customer["id"],
                        **insight.__dict__
                    })
                    break  # Just one per customer
    
    return {
        "summary": list_intel["summary"],
        "top_insights": top_insights[:5],
        "urgent_actions": len(top_insights),
    }
