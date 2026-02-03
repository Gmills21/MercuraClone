"""
Onboarding and Simplification API Routes
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from app.onboarding_service import OnboardingService, SimplifiedModeService
from app.empty_states_service import EmptyStateService

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/checklist")
async def get_onboarding_checklist(user_id: str = "test-user"):
    """
    Get user's onboarding checklist progress.
    """
    return OnboardingService.get_checklist(user_id)


@router.post("/complete/{step_id}")
async def complete_onboarding_step(step_id: str, user_id: str = "test-user"):
    """
    Mark an onboarding step as complete.
    """
    success = OnboardingService.mark_step_complete(user_id, step_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to mark step complete")
    
    return {"success": True}


@router.post("/dismiss")
async def dismiss_checklist(user_id: str = "test-user"):
    """
    User dismissed the onboarding checklist.
    """
    success = OnboardingService.dismiss_checklist(user_id)
    return {"success": success}


@router.get("/should-show")
async def should_show_checklist(user_id: str = "test-user"):
    """
    Check if we should show the onboarding checklist.
    """
    return {
        "show": OnboardingService.should_show_checklist(user_id)
    }


@router.get("/tips")
async def get_contextual_tips(
    context: str = "",
    user_id: str = "test-user"
):
    """
    Get contextual tips based on current page.
    """
    tips = OnboardingService.get_quick_tips(user_id, context)
    return {"tips": tips}


@router.get("/mode")
async def get_ui_mode(user_id: str = "test-user"):
    """
    Get user's UI mode (simplified or advanced).
    """
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
    user_id: str = "test-user"
):
    """
    Set UI mode (simplified or advanced).
    """
    success = SimplifiedModeService.set_mode(user_id, mode)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    return {"success": True, "mode": mode}


@router.post("/record-quote")
async def record_quote_created(user_id: str = "test-user"):
    """
    Record that user created a quote (for auto-switch to advanced mode).
    """
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
    user_id: str = "test-user"
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
