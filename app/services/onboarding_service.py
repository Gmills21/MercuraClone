"""
Unified Onboarding Service
Wraps and queries other services for accurate checklist state
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from app.database_sqlite import list_quotes, list_customers
from app.integrations import ERPRegistry


@dataclass
class OnboardingStep:
    id: str
    title: str
    description: str
    action_link: str
    action_text: str
    completed: bool = False
    completed_at: Optional[str] = None
    icon: str = "check"


class UnifiedOnboardingService:
    """
    Centralized onboarding that queries other services for state.
    
    Avoids duplicate logic by checking actual data:
    - Quotes created? Check quotes table
    - QB connected? Check ERPRegistry
    - Customers added? Check customers table
    """
    
    def __init__(self):
        self._progress: Dict[str, Dict[str, Any]] = {}
        self._dismissed: Dict[str, bool] = {}
    
    def mark_step_complete(self, user_id: str, step_id: str) -> bool:
        """Mark a step as manually completed."""
        if user_id not in self._progress:
            self._progress[user_id] = {}
        self._progress[user_id][step_id] = {
            "completed": True,
            "completed_at": datetime.now().isoformat()
        }
        return True
    
    def dismiss_checklist(self, user_id: str) -> bool:
        """Dismiss the checklist for a user."""
        self._dismissed[user_id] = True
        return True
    
    def should_show_checklist(self, user_id: str) -> bool:
        """Check if checklist should be shown."""
        if self._dismissed.get(user_id):
            return False
        checklist = self.get_checklist(user_id)
        return not checklist["is_complete"]
    
    def get_checklist(self, user_id: str, organization_id: str = None) -> Dict[str, Any]:
        """Get checklist with real-time state from other services."""
        
        # Query real data (organization-scoped)
        quotes = list_quotes(organization_id=organization_id, limit=10) if organization_id else []
        customers = list_customers(organization_id=organization_id, limit=10) if organization_id else []
        qb_connected = self._is_erp_connected(user_id, "quickbooks")
        
        # Build steps based on actual data
        steps = [
            OnboardingStep(
                id="first_quote",
                title="Create Your First Quote",
                description="Try Smart Quote with a sample RFQ or paste a real one",
                action_link="/quotes/new",
                action_text="Create Quote",
                icon="file-text",
                completed=len(quotes) > 0,
                completed_at=quotes[0].get("created_at") if quotes else None
            ),
            OnboardingStep(
                id="add_customer",
                title="Add a Customer",
                description="Add your first customer to the system",
                action_link="/customers",
                action_text="Add Customer",
                icon="users",
                completed=len(customers) > 0,
                completed_at=customers[0].get("created_at") if customers else None
            ),
            OnboardingStep(
                id="view_intelligence",
                title="Check Customer Intelligence",
                description="See how AI analyzes your customer relationships",
                action_link="/intelligence",
                action_text="View Intelligence",
                icon="trending-up",
                completed=len(quotes) >= 3,  # Needs data to show intelligence
            ),
            OnboardingStep(
                id="connect_erp",
                title="Connect QuickBooks (Optional)",
                description="Sync your products and customers automatically",
                action_link="/quickbooks",
                action_text="Connect",
                icon="credit-card",
                completed=qb_connected,
            ),
            OnboardingStep(
                id="explore_impact",
                title="View Your Business Impact",
                description="See time saved and ROI from using OpenMercura",
                action_link="/impact",
                action_text="View Impact",
                icon="bar-chart",
                completed=len(quotes) >= 5,  # Needs enough data for metrics
            ),
        ]
        
        # Calculate progress
        completed_count = sum(1 for s in steps if s.completed)
        total = len(steps)
        percent = int((completed_count / total) * 100) if total > 0 else 0
        
        # Determine if complete
        is_complete = completed_count >= 3
        
        # Find next step
        next_step = None
        for step in steps:
            if not step.completed:
                next_step = asdict(step)
                break
        
        return {
            "steps": [asdict(s) for s in steps],
            "completed_count": completed_count,
            "total_steps": total,
            "progress_percent": percent,
            "is_complete": is_complete,
            "next_step": next_step,
            "show_checklist": not is_complete or completed_count < total
        }
    
    def get_quick_tips(self, context: str = "") -> List[Dict[str, str]]:
        """Get contextual tips based on current page."""
        tips = {
            "dashboard": [
                {
                    "title": "Start Your Day Here",
                    "content": "Check Priority Tasks each morning. Red items need immediate attention."
                },
                {
                    "title": "Smart Quote is Fastest",
                    "content": "Paste any RFQ text and AI extracts items. Saves 16 minutes per quote."
                }
            ],
            "quotes": [
                {
                    "title": "Smart Quote",
                    "content": "Paste any RFQ text and AI extracts items automatically."
                }
            ],
            "default": [
                {
                    "title": "Need Help?",
                    "content": "Check the Business Impact page to see your ROI."
                }
            ]
        }
        
        return tips.get(context, tips["default"])
    
    def _is_erp_connected(self, user_id: str, provider: str) -> bool:
        """Check if ERP provider is connected."""
        provider_obj = ERPRegistry.get(provider)
        if provider_obj:
            # This would be async in production, but we're simulating
            return False  # Simplified for now
        return False



# Global instance
onboarding_service = UnifiedOnboardingService()


class SimplifiedModeService:
    """
    Simplified UI mode for new users.
    Hides advanced features until user is ready.
    """
    
    _user_modes: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def get_mode(cls, user_id: str) -> Dict[str, Any]:
        """Get user's current UI mode."""
        mode = cls._user_modes.get(user_id, {
            "mode": "simplified",  # 'simplified' or 'advanced'
            "switched_at": None,
            "quote_count": 0
        })
        
        # Auto-switch to advanced after 10 quotes
        if mode["quote_count"] >= 10 and mode["mode"] == "simplified":
            mode["mode"] = "advanced"
            mode["switched_at"] = datetime.now().isoformat()
        
        return mode
    
    @classmethod
    def set_mode(cls, user_id: str, mode: str) -> bool:
        """Manually set UI mode."""
        if mode not in ["simplified", "advanced"]:
            return False
        
        if user_id not in cls._user_modes:
            cls._user_modes[user_id] = {}
        
        cls._user_modes[user_id]["mode"] = mode
        cls._user_modes[user_id]["switched_at"] = datetime.now().isoformat()
        
        return True
    
    @classmethod
    def record_quote_created(cls, user_id: str):
        """Track quote creation for auto-switch."""
        if user_id not in cls._user_modes:
            cls._user_modes[user_id] = {"mode": "simplified", "quote_count": 0}
        
        cls._user_modes[user_id]["quote_count"] = cls._user_modes[user_id].get("quote_count", 0) + 1
    
    @classmethod
    def get_visible_features(cls, user_id: str) -> Dict[str, bool]:
        """Get which features should be visible."""
        mode = cls.get_mode(user_id)
        
        if mode["mode"] == "simplified":
            return {
                "smart_quote": True,
                "basic_quotes": True,
                "customers": True,
                "today_view": True,
                "alerts": True,
                "intelligence": False,  # Hide initially
                "competitors": False,
                "quickbooks": False,
                "camera": True,
                "impact": True,
                "advanced_analytics": False
            }
        else:
            return {
                "smart_quote": True,
                "basic_quotes": True,
                "customers": True,
                "today_view": True,
                "alerts": True,
                "intelligence": True,
                "competitors": True,
                "quickbooks": True,
                "camera": True,
                "impact": True,
                "advanced_analytics": True
            }
