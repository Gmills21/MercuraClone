"""
Business Impact Tracker
Serious metrics for serious business owners
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from app.database_sqlite import list_quotes, list_customers


@dataclass
class TimeImpact:
    """Time savings calculation for a specific action."""
    action: str  # 'smart_quote', 'follow_up_alert', 'quickbooks_sync'
    time_saved_minutes: float
    context: str  # What was the specific action
    created_at: datetime


class BusinessImpactService:
    """
    Track real business impact: time saved, revenue won, efficiency gained.
    No gamification - just the numbers that matter.
    """
    
    # Time savings benchmarks (minutes)
    TIME_BENCHMARKS = {
        'smart_quote': {
            'manual_time': 18,  # Traditional quoting
            'tool_time': 2,     # With OpenMercura
            'description': 'AI-powered quote creation'
        },
        'follow_up_alert': {
            'manual_time': 8,   # Checking quotes, deciding who to call
            'tool_time': 1,     # Alert → click → call
            'description': 'Follow-up reminder and action'
        },
        'quickbooks_sync': {
            'manual_time': 45,  # Export/import, data entry
            'tool_time': 2,     # One-click sync
            'description': 'QuickBooks data synchronization'
        },
        'customer_lookup': {
            'manual_time': 5,   # Searching files/crm
            'tool_time': 0.5,   # Instant search
            'description': 'Customer information lookup'
        },
        'price_check': {
            'manual_time': 10,  # Checking competitor prices manually
            'tool_time': 1,     # View competitor map
            'description': 'Competitive price verification'
        }
    }
    
    # In-memory tracking (use database in production)
    _impacts: Dict[str, List[TimeImpact]] = {}
    
    @classmethod
    def record_time_saved(cls, user_id: str, action_type: str, context: str = "") -> TimeImpact:
        """Record time saved from using a feature."""
        benchmark = cls.TIME_BENCHMARKS.get(action_type)
        if not benchmark:
            return None
        
        time_saved = benchmark['manual_time'] - benchmark['tool_time']
        
        impact = TimeImpact(
            action=action_type,
            time_saved_minutes=time_saved,
            context=context or benchmark['description'],
            created_at=datetime.now()
        )
        
        if user_id not in cls._impacts:
            cls._impacts[user_id] = []
        
        cls._impacts[user_id].append(impact)
        
        # Keep last 1000 records
        cls._impacts[user_id] = cls._impacts[user_id][-1000:]
        
        return impact
    
    @classmethod
    def get_time_summary(cls, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get time savings summary for period."""
        impacts = cls._impacts.get(user_id, [])
        cutoff = datetime.now() - timedelta(days=days)
        
        recent_impacts = [i for i in impacts if i.created_at > cutoff]
        
        # Total time saved
        total_minutes = sum(i.time_saved_minutes for i in recent_impacts)
        total_hours = total_minutes / 60
        
        # By action type
        by_action = {}
        for action_type, benchmark in cls.TIME_BENCHMARKS.items():
            action_impacts = [i for i in recent_impacts if i.action == action_type]
            action_minutes = sum(i.time_saved_minutes for i in action_impacts)
            by_action[action_type] = {
                'count': len(action_impacts),
                'minutes_saved': action_minutes,
                'hours_saved': action_minutes / 60,
                'description': benchmark['description']
            }
        
        # Daily average
        days_with_activity = len(set(i.created_at.date() for i in recent_impacts))
        daily_avg = total_hours / max(days_with_activity, 1)
        
        return {
            'period_days': days,
            'total_minutes_saved': total_minutes,
            'total_hours_saved': round(total_hours, 1),
            'daily_average_hours': round(daily_avg, 2),
            'actions_tracked': len(recent_impacts),
            'by_feature': by_action,
            'hourly_rate': 50,  # Configurable
            'dollar_value': round(total_hours * 50, 2)  # $50/hr default
        }
    
    @classmethod
    def get_quote_efficiency(cls, user_id: str) -> Dict[str, Any]:
        """
        Calculate quote efficiency metrics.
        How fast are quotes being created and won?
        """
        quotes = list_quotes(limit=100)
        
        if not quotes:
            return {
                'total_quotes': 0,
                'avg_creation_time_estimate': '2 min',
                'manual_time_equivalent': '0 hours',
                'time_saved_this_month': '0 hours'
            }
        
        # Estimate time saved on quotes created
        total_quotes = len(quotes)
        time_per_quote_manual = 18  # minutes
        time_per_quote_tool = 2     # minutes
        
        total_manual_time = (total_quotes * time_per_quote_manual) / 60  # hours
        total_tool_time = (total_quotes * time_per_quote_tool) / 60      # hours
        time_saved = total_manual_time - total_tool_time
        
        # Win rate
        accepted = len([q for q in quotes if q.get('status') == 'accepted'])
        win_rate = (accepted / total_quotes * 100) if total_quotes > 0 else 0
        
        # Revenue metrics
        total_value = sum(q.get('total', 0) for q in quotes if q.get('status') == 'accepted')
        avg_quote_value = total_value / accepted if accepted > 0 else 0
        
        return {
            'total_quotes_created': total_quotes,
            'quotes_accepted': accepted,
            'win_rate_percent': round(win_rate, 1),
            'total_revenue': round(total_value, 2),
            'average_quote_value': round(avg_quote_value, 2),
            'time_saved_hours': round(time_saved, 1),
            'manual_time_equivalent_hours': round(total_manual_time, 1),
            'efficiency_gain_percent': 89,  # (18-2)/18 * 100
            'estimated_monthly_time_savings': f'{round(time_saved, 1)} hours'
        }
    
    @classmethod
    def get_follow_up_impact(cls, user_id: str) -> Dict[str, Any]:
        """
        Calculate impact of follow-up alerts on win rate.
        """
        from app.database_sqlite import list_quotes
        
        # Get quotes that were sent and had follow-up
        # This is a simplified version - in production you'd track which quotes
        # had follow-up alerts acted upon
        
        quotes = list_quotes(limit=200)
        sent_quotes = [q for q in quotes if q.get('status') in ['sent', 'accepted', 'rejected']]
        
        if not sent_quotes:
            return {
                'quotes_needing_follow_up': 0,
                'avg_response_time_days': 0,
                'follow_up_conversion_rate': 0
            }
        
        # Calculate response times for quotes that were decided
        response_times = []
        converted_after_follow_up = 0
        
        for q in sent_quotes:
            if q.get('status') in ['accepted', 'rejected'] and q.get('updated_at'):
                try:
                    sent = datetime.fromisoformat(q.get('sent_at', q.get('created_at', '')).replace('Z', '+00:00'))
                    decided = datetime.fromisoformat(q['updated_at'].replace('Z', '+00:00'))
                    days = (decided - sent).days
                    response_times.append(days)
                    
                    if q.get('status') == 'accepted' and days > 3:
                        converted_after_follow_up += 1
                except:
                    pass
        
        avg_response = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            'quotes_sent': len(sent_quotes),
            'quotes_needing_follow_up': len([q for q in sent_quotes if q.get('status') == 'sent']),
            'avg_response_time_days': round(avg_response, 1),
            'converted_after_follow_up': converted_after_follow_up,
            'follow_up_value': f'${converted_after_follow_up * 5000:,.0f}'  # Estimated
        }
    
    @classmethod
    def get_roi_summary(cls, user_id: str) -> Dict[str, Any]:
        """
        Full ROI calculation for the business.
        What are they paying vs what are they getting?
        """
        time_summary = cls.get_time_summary(user_id, days=30)
        quote_eff = cls.get_quote_efficiency(user_id)
        follow_up = cls.get_follow_up_impact(user_id)
        
        # Monthly subscription cost (example)
        monthly_cost = 99  # $99/month for Pro plan
        
        # Value generated
        time_value = time_summary['dollar_value']
        revenue_from_follow_ups = follow_up.get('converted_after_follow_up', 0) * 5000
        
        total_value = time_value + (revenue_from_follow_ups * 0.2)  # 20% attribution
        roi_percent = ((total_value - monthly_cost) / monthly_cost * 100) if monthly_cost > 0 else 0
        
        return {
            'monthly_subscription_cost': monthly_cost,
            'time_saved_value': round(time_value, 2),
            'additional_revenue_attributed': round(revenue_from_follow_ups * 0.2, 2),
            'total_value_generated': round(total_value, 2),
            'roi_percent': round(roi_percent, 0),
            'payback_period_days': '< 1' if roi_percent > 100 else '7',
            'break_even_quotes': max(1, int(monthly_cost / 50)),  # At ~$50 value per quote
            'recommendation': 'Strong ROI' if roi_percent > 200 else 'Good ROI' if roi_percent > 100 else 'Monitor usage'
        }
    
    @classmethod
    def get_weekly_report(cls, user_id: str) -> Dict[str, Any]:
        """
        Generate weekly business impact report.
        """
        time_7d = cls.get_time_summary(user_id, days=7)
        time_30d = cls.get_time_summary(user_id, days=30)
        quote_eff = cls.get_quote_efficiency(user_id)
        roi = cls.get_roi_summary(user_id)
        
        return {
            'report_period': 'Last 7 Days',
            'generated_at': datetime.now().isoformat(),
            'time_saved_this_week': f"{time_7d['total_hours_saved']} hours",
            'time_saved_this_month': f"{time_30d['total_hours_saved']} hours",
            'quotes_created': quote_eff['total_quotes_created'],
            'win_rate': f"{quote_eff['win_rate_percent']}%",
            'revenue_closed': f"${quote_eff['total_revenue']:,.2f}",
            'roi': f"{roi['roi_percent']}%",
            'key_insight': cls._generate_insight(time_7d, quote_eff, roi),
            'actions_recommended': cls._generate_recommendations(quote_eff)
        }
    
    @classmethod
    def _generate_insight(cls, time_data: Dict, quote_data: Dict, roi_data: Dict) -> str:
        """Generate a key insight for the weekly report."""
        insights = []
        
        if time_data['total_hours_saved'] > 5:
            insights.append(f"You saved {time_data['total_hours_saved']} hours this week.")
        
        if quote_data['win_rate_percent'] > 50:
            insights.append(f"Strong {quote_data['win_rate_percent']}% win rate.")
        
        if roi_data['roi_percent'] > 300:
            insights.append("Exceptional ROI - you're getting 3x+ value.")
        
        if not insights:
            insights.append("Steady progress. Keep using Smart Quotes for maximum efficiency.")
        
        return " ".join(insights)
    
    @classmethod
    def _generate_recommendations(cls, quote_data: Dict) -> List[str]:
        """Generate actionable recommendations."""
        recs = []
        
        if quote_data['win_rate_percent'] < 40:
            recs.append("Win rate below 40% - review your pricing strategy")
        
        if quote_data['total_quotes_created'] < 5:
            recs.append("Quote volume low - check for unprocessed RFQs in inbox")
        
        if quote_data.get('quotes_needing_follow_up', 0) > 3:
            recs.append(f"{quote_data['quotes_needing_follow_up']} quotes need follow-up - check alerts")
        
        if not recs:
            recs.append("Continue current workflow - metrics look good")
        
        return recs
