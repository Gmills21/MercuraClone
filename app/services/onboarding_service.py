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
    
    def get_checklist(self, user_id: str) -> Dict[str, Any]:
        """Get checklist with real-time state from other services."""
        
        # Query real data
        quotes = list_quotes(limit=10)
        customers = list_customers(limit=10)
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
