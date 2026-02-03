"""
Onboarding Service
Track and guide new users through their first experience
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


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


class OnboardingService:
    """
    Guide new users through first-time setup.
    Progressive disclosure - don't show everything at once.
    """
    
    # In-memory store (use database in production)
    _user_progress: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def get_checklist(cls, user_id: str) -> Dict[str, Any]:
        """Get personalized onboarding checklist."""
        # Default checklist for new users
        default_steps = [
            OnboardingStep(
                id="first_quote",
                title="Create Your First Quote",
                description="Try Smart Quote with a sample RFQ or paste a real one",
                action_link="/quotes/new",
                action_text="Create Quote",
                icon="file-text"
            ),
            OnboardingStep(
                id="add_customer",
                title="Add a Customer",
                description="Add your first customer to the system",
                action_link="/customers",
                action_text="Add Customer",
                icon="users"
            ),
            OnboardingStep(
                id="view_intelligence",
                title="Check Customer Intelligence",
                description="See how AI analyzes your customer relationships",
                action_link="/intelligence",
                action_text="View Intelligence",
                icon="trending-up"
            ),
            OnboardingStep(
                id="connect_quickbooks",
                title="Connect QuickBooks (Optional)",
                description="Sync your products and customers automatically",
                action_link="/quickbooks",
                action_text="Connect",
                icon="credit-card"
            ),
            OnboardingStep(
                id="explore_impact",
                title="View Your Business Impact",
                description="See time saved and ROI from using OpenMercura",
                action_link="/impact",
                action_text="View Impact",
                icon="bar-chart"
            ),
        ]
        
        # Get user's progress
        progress = cls._user_progress.get(user_id, {})
        
        # Merge with completion status
        steps = []
        completed_count = 0
        for step in default_steps:
            step_data = asdict(step)
            if step.id in progress:
                step_data["completed"] = progress[step.id]["completed"]
                step_data["completed_at"] = progress[step.id].get("completed_at")
            if step_data["completed"]:
                completed_count += 1
            steps.append(step_data)
        
        # Calculate progress
        total = len(steps)
        percent = int((completed_count / total) * 100) if total > 0 else 0
        
        # Determine if onboarding is complete
        is_complete = completed_count >= 3  # At least 3 steps done
        
        return {
            "steps": steps,
            "completed_count": completed_count,
            "total_steps": total,
            "progress_percent": percent,
            "is_complete": is_complete,
            "next_step": cls._get_next_step(steps),
            "show_checklist": not is_complete or completed_count < total
        }
    
    @classmethod
    def mark_step_complete(cls, user_id: str, step_id: str) -> bool:
        """Mark an onboarding step as complete."""
        if user_id not in cls._user_progress:
            cls._user_progress[user_id] = {}
        
        cls._user_progress[user_id][step_id] = {
            "completed": True,
            "completed_at": datetime.now().isoformat()
        }
        
        return True
    
    @classmethod
    def dismiss_checklist(cls, user_id: str) -> bool:
        """User chose to dismiss the checklist."""
        if user_id not in cls._user_progress:
            cls._user_progress[user_id] = {}
        
        cls._user_progress[user_id]["checklist_dismissed"] = True
        cls._user_progress[user_id]["dismissed_at"] = datetime.now().isoformat()
        
        return True
    
    @classmethod
    def should_show_checklist(cls, user_id: str) -> bool:
        """Check if we should show the onboarding checklist."""
        progress = cls._user_progress.get(user_id, {})
        
        # Don't show if explicitly dismissed
        if progress.get("checklist_dismissed"):
            return False
        
        # Don't show if completed all steps
        checklist = cls.get_checklist(user_id)
        if checklist["is_complete"]:
            return False
        
        return True
    
    @classmethod
    def get_quick_tips(cls, user_id: str, context: str = "") -> List[Dict[str, str]]:
        """Get contextual tips based on where user is in the app."""
        tips = {
            "dashboard": [
                {
                    "title": "Start Your Day Here",
                    "content": "Check Priority Tasks each morning. Red items need immediate attention."
                },
                {
                    "title": "Quick Actions",
                    "content": "Use Smart Quote for fastest quote creation. It saves 16 minutes per quote."
                }
            ],
            "quotes": [
                {
                    "title": "Smart Quote",
                    "content": "Paste any RFQ text and AI will extract items automatically."
                },
                {
                    "title": "Follow-ups",
                    "content": "Quotes sent 3+ days ago need follow-up. Check alerts."
                }
            ],
            "customers": [
                {
                    "title": "Customer Intelligence",
                    "content": "Click any customer to see their health score and insights."
                }
            ],
            "intelligence": [
                {
                    "title": "Health Score",
                    "content": "80+ means excellent relationship. Under 40 needs attention."
                },
                {
                    "title": "At-Risk Customers",
                    "content": "These customers haven't requested quotes in 90+ days."
                }
            ],
            "default": [
                {
                    "title": "Need Help?",
                    "content": "Check the Business Impact page to see your ROI and time savings."
                }
            ]
        }
        
        return tips.get(context, tips["default"])
    
    @classmethod
    def _get_next_step(cls, steps: List[Dict]) -> Optional[Dict]:
        """Get the next uncompleted step."""
        for step in steps:
            if not step["completed"]:
                return step
        return None


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
