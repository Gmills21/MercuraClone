"""
Smart Alerts Service - Production Ready
Organization-scoped alerts with database persistence
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from loguru import logger

from app.database_sqlite import (
    create_alert, list_alerts, get_unread_alert_count,
    mark_alert_read, mark_all_alerts_read, dismiss_alert,
    alert_exists, auto_resolve_alerts,
    list_quotes, list_emails
)


class AlertType(str, Enum):
    NEW_RFQ = "new_rfq"                    # New quote request received
    FOLLOW_UP_NEEDED = "follow_up_needed"  # Quote needs follow-up
    QUOTE_EXPIRING = "quote_expiring"      # Quote expires soon
    LOW_MARGIN = "low_margin"              # Quote has low margin
    PRICE_DISCREPANCY = "price_discrepancy"  # Price differs from catalog


class AlertPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Alert:
    id: str
    organization_id: str
    user_id: Optional[str]
    type: AlertType
    priority: AlertPriority
    title: str
    message: str
    created_at: datetime
    is_read: bool = False
    action_link: Optional[str] = None
    action_text: Optional[str] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "type": self.type.value,
            "priority": self.priority.value,
            "title": self.title,
            "message": self.message,
            "is_read": self.is_read,
            "action_link": self.action_link,
            "action_text": self.action_text,
            "related_entity_type": self.related_entity_type,
            "related_entity_id": self.related_entity_id,
            "created_at": self.created_at.isoformat(),
        }


class AlertService:
    """
    Production-ready alert service.
    
    Principles:
    1. Organization-scoped - alerts are per organization
    2. Database persisted - survives restarts
    3. Auto-resolve - alerts clean themselves up
    4. Actionable - every alert has a clear next step
    """
    
    @classmethod
    def get_user_alerts(
        cls,
        organization_id: str,
        user_id: Optional[str] = None,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get alerts for an organization/user."""
        return list_alerts(
            organization_id=organization_id,
            user_id=user_id,
            unread_only=unread_only,
            limit=limit
        )
    
    @classmethod
    def get_unread_count(cls, organization_id: str, user_id: Optional[str] = None) -> int:
        """Get unread alert count."""
        return get_unread_alert_count(organization_id, user_id)
    
    @classmethod
    def mark_read(cls, organization_id: str, alert_id: str) -> bool:
        """Mark alert as read."""
        return mark_alert_read(alert_id, organization_id)
    
    @classmethod
    def mark_all_read(cls, organization_id: str, user_id: Optional[str] = None) -> int:
        """Mark all alerts as read."""
        return mark_all_alerts_read(organization_id, user_id)
    
    @classmethod
    def dismiss_alert(cls, organization_id: str, alert_id: str) -> bool:
        """Dismiss an alert."""
        return dismiss_alert(alert_id, organization_id)
    
    # ========== ALERT GENERATORS ==========
    
    @classmethod
    def check_new_rfqs(cls, organization_id: str) -> List[Dict[str, Any]]:
        """Alert on new RFQ emails received in last 24 hours."""
        new_alerts = []
        
        try:
            emails = list_emails(organization_id=organization_id, limit=20)
            
            for email in emails:
                # Skip if already alerted
                if alert_exists(organization_id, AlertType.NEW_RFQ, email["id"]):
                    continue
                
                # Only alert on emails received in last 24 hours
                received = email.get("received_at") or email.get("created_at")
                if received:
                    try:
                        received_dt = datetime.fromisoformat(received.replace("Z", "+00:00"))
                        if datetime.now() - received_dt > timedelta(hours=24):
                            continue
                    except:
                        pass
                
                alert_data = {
                    "id": str(uuid.uuid4()),
                    "organization_id": organization_id,
                    "user_id": None,
                    "alert_type": AlertType.NEW_RFQ,
                    "priority": AlertPriority.HIGH,
                    "title": "New Quote Request",
                    "message": f"{email.get('sender_email', 'A customer')} sent a new RFQ",
                    "action_link": "/emails",
                    "action_text": "View Email",
                    "related_entity_type": "email",
                    "related_entity_id": email["id"],
                    "created_at": datetime.utcnow().isoformat(),
                }
                
                created = create_alert(alert_data)
                if created:
                    new_alerts.append(created)
                    logger.info(f"Created NEW_RFQ alert for email {email['id']}")
        
        except Exception as e:
            logger.error(f"Error checking for new RFQs: {e}")
        
        return new_alerts
    
    @classmethod
    def check_follow_ups(cls, organization_id: str) -> List[Dict[str, Any]]:
        """Alert on quotes that need follow-up (sent 3-7 days ago)."""
        new_alerts = []
        
        try:
            quotes = list_quotes(organization_id=organization_id, limit=100)
            
            for quote in quotes:
                if quote.get("status") != "sent":
                    continue
                
                sent_at = quote.get("sent_at") or quote.get("created_at")
                if not sent_at:
                    continue
                
                try:
                    sent_dt = datetime.fromisoformat(sent_at.replace("Z", "+00:00"))
                    days_since = (datetime.now() - sent_dt).days
                except:
                    continue
                
                # Alert on 3-7 day window
                if days_since < 3 or days_since > 7:
                    continue
                
                # Skip if already alerted
                if alert_exists(organization_id, AlertType.FOLLOW_UP_NEEDED, quote["id"]):
                    continue
                
                alert_data = {
                    "id": str(uuid.uuid4()),
                    "organization_id": organization_id,
                    "user_id": quote.get("assigned_user_id"),
                    "alert_type": AlertType.FOLLOW_UP_NEEDED,
                    "priority": AlertPriority.HIGH if days_since >= 5 else AlertPriority.MEDIUM,
                    "title": "Follow-up Needed",
                    "message": f"{quote.get('customer_name', 'Customer')} hasn't responded to ${quote.get('total', 0):,.0f} quote ({days_since} days)",
                    "action_link": f"/quotes/{quote['id']}",
                    "action_text": "Follow Up",
                    "related_entity_type": "quote",
                    "related_entity_id": quote["id"],
                    "created_at": datetime.utcnow().isoformat(),
                }
                
                created = create_alert(alert_data)
                if created:
                    new_alerts.append(created)
                    logger.info(f"Created FOLLOW_UP_NEEDED alert for quote {quote['id']}")
        
        except Exception as e:
            logger.error(f"Error checking for follow-ups: {e}")
        
        return new_alerts
    
    @classmethod
    def check_expiring_quotes(cls, organization_id: str) -> List[Dict[str, Any]]:
        """Alert on quotes expiring in 7 days (21 days old)."""
        new_alerts = []
        
        try:
            quotes = list_quotes(organization_id=organization_id, limit=100)
            
            for quote in quotes:
                if quote.get("status") != "sent":
                    continue
                
                sent_at = quote.get("sent_at") or quote.get("created_at")
                if not sent_at:
                    continue
                
                try:
                    sent_dt = datetime.fromisoformat(sent_at.replace("Z", "+00:00"))
                    days_since = (datetime.now() - sent_dt).days
                except:
                    continue
                
                # Alert at exactly 21 days (7 days before typical 30-day expiration)
                if days_since != 21:
                    continue
                
                # Skip if already alerted
                if alert_exists(organization_id, AlertType.QUOTE_EXPIRING, quote["id"]):
                    continue
                
                alert_data = {
                    "id": str(uuid.uuid4()),
                    "organization_id": organization_id,
                    "user_id": quote.get("assigned_user_id"),
                    "alert_type": AlertType.QUOTE_EXPIRING,
                    "priority": AlertPriority.MEDIUM,
                    "title": "Quote Expiring Soon",
                    "message": f"{quote.get('customer_name', 'Customer')}'s ${quote.get('total', 0):,.0f} quote expires in 7 days",
                    "action_link": f"/quotes/{quote['id']}",
                    "action_text": "Renew Quote",
                    "related_entity_type": "quote",
                    "related_entity_id": quote["id"],
                    "created_at": datetime.utcnow().isoformat(),
                }
                
                created = create_alert(alert_data)
                if created:
                    new_alerts.append(created)
                    logger.info(f"Created QUOTE_EXPIRING alert for quote {quote['id']}")
        
        except Exception as e:
            logger.error(f"Error checking for expiring quotes: {e}")
        
        return new_alerts
    
    @classmethod
    def run_all_checks(cls, organization_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Run all alert checks and return new alerts created."""
        new_alerts = []
        
        try:
            new_alerts.extend(cls.check_new_rfqs(organization_id))
            new_alerts.extend(cls.check_follow_ups(organization_id))
            new_alerts.extend(cls.check_expiring_quotes(organization_id))
            
            # Auto-resolve alerts that no longer apply
            resolved = auto_resolve_alerts(organization_id)
            if resolved > 0:
                logger.info(f"Auto-resolved {resolved} alerts for org {organization_id}")
        
        except Exception as e:
            logger.error(f"Error running alert checks: {e}")
        
        return {
            "new_alerts_count": len(new_alerts),
            "total_unread": cls.get_unread_count(organization_id, user_id),
            "alerts": new_alerts,
        }
