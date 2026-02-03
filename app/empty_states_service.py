"""
Empty States Service
Helpful, guiding empty states instead of blank pages
"""

from typing import Dict, Any


class EmptyStateService:
    """
    Provide contextual empty states with clear next steps.
    Never show "No data" - always show "Here's what to do"
    """
    
    @staticmethod
    def get_quotes_empty_state(has_customers: bool = False) -> Dict[str, Any]:
        """Empty state for quotes list."""
        if not has_customers:
            return {
                "title": "No Quotes Yet",
                "subtitle": "Start by adding a customer, then create your first quote",
                "icon": "file-text",
                "primary_action": {
                    "text": "Add Your First Customer",
                    "link": "/customers"
                },
                "secondary_action": None,
                "help_text": "Quotes help you track opportunities and close deals faster."
            }
        
        return {
            "title": "No Quotes Yet",
            "subtitle": "Create your first quote and start closing deals",
            "icon": "file-text",
            "primary_action": {
                "text": "Create First Quote",
                "link": "/quotes/new"
            },
            "secondary_action": {
                "text": "Learn How Smart Quote Works",
                "link": "#help"
            },
            "help_text": "Smart Quote saves 16 minutes per quote with AI extraction."
        }
    
    @staticmethod
    def get_customers_empty_state() -> Dict[str, Any]:
        """Empty state for customers list."""
        return {
            "title": "No Customers Yet",
            "subtitle": "Add your first customer to get started",
            "icon": "users",
            "primary_action": {
                "text": "Add First Customer",
                "link": "/customers"
            },
            "secondary_action": {
                "text": "Import from QuickBooks",
                "link": "/quickbooks"
            },
            "help_text": "Customers are the foundation of your sales workflow."
        }
    
    @staticmethod
    def get_inbox_empty_state() -> Dict[str, Any]:
        """Empty state for email inbox."""
        return {
            "title": "Inbox Empty",
            "subtitle": "New RFQ emails will appear here automatically",
            "icon": "mail",
            "primary_action": {
                "text": "Create Quote Manually",
                "link": "/quotes/new"
            },
            "secondary_action": {
                "text": "Set Up Email Forwarding",
                "link": "#setup"
            },
            "help_text": "Forward RFQ emails to your OpenMercura address to process them automatically."
        }
    
    @staticmethod
    def get_alerts_empty_state() -> Dict[str, Any]:
        """Empty state for alerts."""
        return {
            "title": "All Caught Up",
            "subtitle": "No alerts right now. We'll notify you when action is needed.",
            "icon": "check-circle",
            "primary_action": None,
            "secondary_action": None,
            "help_text": "Alerts appear for: new RFQs, follow-ups needed, and expiring quotes."
        }
    
    @staticmethod
    def get_intelligence_empty_state() -> Dict[str, Any]:
        """Empty state for customer intelligence."""
        return {
            "title": "Intelligence Needs Data",
            "subtitle": "Create a few quotes first to see customer insights",
            "icon": "trending-up",
            "primary_action": {
                "text": "Create a Quote",
                "link": "/quotes/new"
            },
            "secondary_action": None,
            "help_text": "After 2-3 quotes per customer, we'll show health scores and predictions."
        }
    
    @staticmethod
    def get_impact_empty_state() -> Dict[str, Any]:
        """Empty state for business impact."""
        return {
            "title": "No Impact Data Yet",
            "subtitle": "Start using OpenMercura to see your time savings and ROI",
            "icon": "bar-chart",
            "primary_action": {
                "text": "Create Your First Quote",
                "link": "/quotes/new"
            },
            "secondary_action": None,
            "help_text": "We'll track time saved on every Smart Quote and show you the value."
        }
