"""
Smart Alerts Service - Refined
Helpful notifications without the noise
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class AlertType(str, Enum):
    # Only the essentials - things that truly need attention
    NEW_RFQ = "new_rfq"                    # Money on the table
    FOLLOW_UP_NEEDED = "follow_up_needed"  # Deal going cold
    QUOTE_EXPIRING = "quote_expiring"      # Time-sensitive


class AlertPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"


@dataclass
class Alert:
    id: str
    type: AlertType
    priority: AlertPriority
    title: str
    message: str
    created_at: datetime
    read: bool = False
    action_link: Optional[str] = None
    action_text: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        return result


class AlertService:
    """
    Minimal, helpful alerts.
    
    Principles:
    1. Only alert on things that need action
    2. One alert per event (no spam)
    3. Actionable - every alert has a clear next step
    4. Auto-resolve when situation changes
    """
    
    _alerts: Dict[str, List[Alert]] = {}
    
    @classmethod
    def get_user_alerts(cls, user_id: str, unread_only: bool = False, limit: int = 20) -> List[Alert]:
        """Get alerts - newest first, high priority first."""
        alerts = cls._alerts.get(user_id, [])
        
        if unread_only:
            alerts = [a for a in alerts if not a.read]
        
        # Sort: high priority first, then newest
        priority_order = {AlertPriority.HIGH: 0, AlertPriority.MEDIUM: 1}
        alerts = sorted(alerts, key=lambda a: (priority_order[a.priority], a.created_at), reverse=True)
        
        return alerts[:limit]
    
    @classmethod
    def create_alert(cls, user_id: str, alert: Alert) -> Optional[Alert]:
        """
        Create alert only if user doesn't already have one for this thing.
        Returns None if duplicate/unnecessary.
        """
        if user_id not in cls._alerts:
            cls._alerts[user_id] = []
        
        # Check for duplicates
        for existing in cls._alerts[user_id]:
            if existing.id == alert.id and not existing.read:
                return None  # Already have this alert
        
        cls._alerts[user_id].append(alert)
        
        # Keep last 50 alerts (trim old noise)
        cls._alerts[user_id] = cls._alerts[user_id][-50:]
        
        return alert
    
    @classmethod
    def mark_read(cls, user_id: str, alert_id: str) -> bool:
        """Mark alert as read."""
        for alert in cls._alerts.get(user_id, []):
            if alert.id == alert_id:
                alert.read = True
                return True
        return False
    
    @classmethod
    def mark_all_read(cls, user_id: str) -> int:
        """Mark all as read."""
        count = 0
        for alert in cls._alerts.get(user_id, []):
            if not alert.read:
                alert.read = True
                count += 1
        return count
    
    @classmethod
    def dismiss_alert(cls, user_id: str, alert_id: str) -> bool:
        """Remove alert completely."""
        alerts = cls._alerts.get(user_id, [])
        cls._alerts[user_id] = [a for a in alerts if a.id != alert_id]
        return True
    
    @classmethod
    def get_unread_count(cls, user_id: str) -> int:
        """Count unread alerts."""
        return len([a for a in cls._alerts.get(user_id, []) if not a.read])
    
    # ========== SMART ALERT GENERATORS ==========
    
    @classmethod
    def check_new_rfqs(cls, user_id: str) -> List[Alert]:
        """
        Alert when new RFQ email arrives.
        Only creates ONE alert per email.
        """
        from app.database_sqlite import list_extractions
        
        new_alerts = []
        emails = list_extractions(status='pending', limit=10)
        
        for email in emails:
            alert_id = f"rfq_{email['id']}"
            
            # Skip if already alerted
            if cls._alert_exists(user_id, alert_id):
                continue
            
            # Only alert on emails received in last 24 hours
            received = email.get('received_at') or email.get('created_at')
            if received:
                try:
                    received_dt = datetime.fromisoformat(received.replace('Z', '+00:00'))
                    if datetime.now() - received_dt > timedelta(hours=24):
                        continue  # Too old, don't alert
                except:
                    pass
            
            alert = Alert(
                id=alert_id,
                type=AlertType.NEW_RFQ,
                priority=AlertPriority.HIGH,
                title="New Quote Request",
                message=f"{email.get('from_name', 'A customer')} sent: {email.get('subject', 'New RFQ')[:50]}",
                created_at=datetime.now(),
                action_link="/inbox",
                action_text="View Email"
            )
            
            if cls.create_alert(user_id, alert):
                new_alerts.append(alert)
        
        return new_alerts
    
    @classmethod
    def check_follow_ups(cls, user_id: str) -> List[Alert]:
        """
        Alert when quote needs follow-up.
        Only for quotes sent 3-7 days ago (not too soon, not too late).
        """
        from app.database_sqlite import list_quotes
        
        new_alerts = []
        quotes = list_quotes(limit=50)
        
        for quote in quotes:
            sent_at = quote.get('sent_at') or quote.get('created_at')
            if not sent_at:
                continue
            
            try:
                sent_dt = datetime.fromisoformat(sent_at.replace('Z', '+00:00'))
                days_since = (datetime.now() - sent_dt).days
            except:
                continue
            
            # Only alert on 3-7 day window (sweet spot for follow-up)
            if days_since < 3 or days_since > 7:
                continue
            
            alert_id = f"followup_{quote['id']}"
            
            # Skip if already alerted
            if cls._alert_exists(user_id, alert_id):
                continue
            
            # Skip if quote was updated recently (they already followed up)
            updated_at = quote.get('updated_at')
            if updated_at:
                try:
                    updated_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    if datetime.now() - updated_dt < timedelta(days=1):
                        continue  # They already touched this quote today
                except:
                    pass
            
            alert = Alert(
                id=alert_id,
                type=AlertType.FOLLOW_UP_NEEDED,
                priority=AlertPriority.HIGH if days_since >= 5 else AlertPriority.MEDIUM,
                title="Follow-up Needed",
                message=f"{quote.get('customer_name', 'Customer')} hasn't responded to ${quote.get('total', 0):,.0f} quote ({days_since} days)",
                created_at=datetime.now(),
                action_link=f"/quotes/{quote['id']}",
                action_text="Follow Up"
            )
            
            if cls.create_alert(user_id, alert):
                new_alerts.append(alert)
        
        return new_alerts
    
    @classmethod
    def check_expiring_quotes(cls, user_id: str) -> List[Alert]:
        """
        Alert when quote is about to expire.
        Only alert once, 7 days before expiration.
        """
        from app.database_sqlite import list_quotes
        
        new_alerts = []
        quotes = list_quotes(limit=50)
        
        for quote in quotes:
            sent_at = quote.get('sent_at') or quote.get('created_at')
            if not sent_at:
                continue
            
            try:
                sent_dt = datetime.fromisoformat(sent_at.replace('Z', '+00:00'))
                days_since = (datetime.now() - sent_dt).days
            except:
                continue
            
            # Alert at 21 days (7 days before typical 30-day expiration)
            if days_since != 21:
                continue
            
            alert_id = f"expiring_{quote['id']}"
            
            # Skip if already alerted
            if cls._alert_exists(user_id, alert_id):
                continue
            
            alert = Alert(
                id=alert_id,
                type=AlertType.QUOTE_EXPIRING,
                priority=AlertPriority.MEDIUM,
                title="Quote Expiring Soon",
                message=f"{quote.get('customer_name', 'Customer')}'s ${quote.get('total', 0):,.0f} quote expires in 7 days",
                created_at=datetime.now(),
                action_link=f"/quotes/{quote['id']}",
                action_text="Renew Quote"
            )
            
            if cls.create_alert(user_id, alert):
                new_alerts.append(alert)
        
        return new_alerts
    
    @classmethod
    def run_all_checks(cls, user_id: str) -> Dict[str, Any]:
        """Run all alert checks. Returns only NEW alerts created."""
        new_alerts = []
        
        new_alerts.extend(cls.check_new_rfqs(user_id))
        new_alerts.extend(cls.check_follow_ups(user_id))
        new_alerts.extend(cls.check_expiring_quotes(user_id))
        
        # Auto-cleanup: Mark follow-up alerts as read if quote status changed
        cls._auto_resolve_alerts(user_id)
        
        return {
            "new_alerts_count": len(new_alerts),
            "total_unread": cls.get_unread_count(user_id),
            "alerts": [a.to_dict() for a in new_alerts]
        }
    
    @classmethod
    def _alert_exists(cls, user_id: str, alert_id: str) -> bool:
        """Check if alert already exists and is unread."""
        for alert in cls._alerts.get(user_id, []):
            if alert.id == alert_id and not alert.read:
                return True
        return False
    
    @classmethod
    def _auto_resolve_alerts(cls, user_id: str):
        """
        Automatically mark alerts as read when situation resolves.
        - Follow-up alerts if quote status changes from 'sent'
        """
        from app.database_sqlite import get_quotes
        
        quotes = {q['id']: q for q in get_quotes(limit=100)}
        
        for alert in cls._alerts.get(user_id, []):
            if alert.type == AlertType.FOLLOW_UP_NEEDED and not alert.read:
                # Extract quote ID from alert ID (followup_{quote_id})
                quote_id = alert.id.replace("followup_", "")
                quote = quotes.get(quote_id)
                
                if quote and quote.get('status') != 'sent':
                    # Quote status changed - auto-resolve
                    alert.read = True
