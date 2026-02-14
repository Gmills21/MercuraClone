"""
Onboarding and Simplification API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.services.onboarding_service import onboarding_service, UnifiedOnboardingService, SimplifiedModeService
from app.empty_states_service import EmptyStateService
from app.middleware.organization import get_current_user_and_org

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/checklist")
async def get_onboarding_checklist(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get user's onboarding checklist progress.
    """
    user_id, org_id = user_org
    return onboarding_service.get_checklist(user_id, org_id)


@router.post("/complete/{step_id}")
async def complete_onboarding_step(
    step_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Mark an onboarding step as complete.
    """
    user_id, org_id = user_org
    success = onboarding_service.mark_step_complete(user_id, step_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to mark step complete")
    
    return {"success": True}


@router.post("/dismiss")
async def dismiss_checklist(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    User dismissed the onboarding checklist.
    """
    user_id, org_id = user_org
    success = onboarding_service.dismiss_checklist(user_id)
    return {"success": success}


@router.get("/should-show")
async def should_show_checklist(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Check if we should show the onboarding checklist.
    """
    user_id, org_id = user_org
    return {
        "show": onboarding_service.should_show_checklist(user_id)
    }


@router.get("/tips")
async def get_contextual_tips(
    context: str = "",
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get contextual tips based on current page.
    """
    user_id, org_id = user_org
    tips = onboarding_service.get_quick_tips(context)
    return {"tips": tips}


@router.get("/mode")
async def get_ui_mode(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get user's UI mode (simplified or advanced).
    """
    user_id, org_id = user_org
    mode = SimplifiedModeService.get_mode(user_id)
    features = SimplifiedModeService.get_visible_features(user_id)
    
    return {
        "mode": mode["mode"],
        "features": features,
        "can_switch": True
    }


@router.post("/mode")
async def set_ui_mode(
    mode: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Set UI mode (simplified or advanced).
    """
    user_id, org_id = user_org
    success = SimplifiedModeService.set_mode(user_id, mode)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    return {"success": True, "mode": mode}


@router.post("/record-quote")
async def record_quote_created(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Record that user created a quote (for auto-switch to advanced mode).
    """
    user_id, org_id = user_org
    SimplifiedModeService.record_quote_created(user_id)
    mode = SimplifiedModeService.get_mode(user_id)
    
    return {
        "success": True,
        "quote_count": mode.get("quote_count", 0),
        "mode": mode["mode"]
    }


# Empty States
@router.get("/empty-state/{page}")
async def get_empty_state(
    page: str,
    has_customers: bool = False,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get contextual empty state for a page.
    """
    service = EmptyStateService()
    
    if page == "quotes":
        return service.get_quotes_empty_state(has_customers)
    elif page == "customers":
        return service.get_customers_empty_state()
    elif page == "inbox":
        return service.get_inbox_empty_state()
    elif page == "alerts":
        return service.get_alerts_empty_state()
    elif page == "intelligence":
        return service.get_intelligence_empty_state()
    elif page == "impact":
        return service.get_impact_empty_state()
    else:
        return {
            "title": "Nothing Here Yet",
            "subtitle": "Get started by exploring the features",
            "icon": "box",
            "primary_action": {
                "text": "Go to Dashboard",
                "link": "/"
            },
            "secondary_action": None,
            "help_text": ""
        }
