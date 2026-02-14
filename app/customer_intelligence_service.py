"""
Customer Intelligence Service
Simple, actionable insights for sales teams
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import defaultdict

from app.database_sqlite import list_quotes, list_customers, list_products, get_customer_by_id


@dataclass
class CustomerInsight:
    """A single insight about a customer with clear action."""
    type: str  # 'opportunity', 'risk', 'trend', 'behavior'
    title: str
    description: str
    action: str
    action_link: str
    impact: str  # 'high', 'medium', 'low'
    metric_value: Optional[float] = None
    metric_label: Optional[str] = None


class CustomerIntelligenceService:
    """Generate simple, actionable customer insights."""
    
    @staticmethod
    def analyze_customer(customer_id: str, organization_id: str) -> Dict[str, Any]:
        """Generate complete intelligence profile for a customer."""
        try:
            customer = get_customer_by_id(customer_id, organization_id)
            if not customer:
                return {"error": "Customer not found"}
            
            quotes = list_quotes(organization_id=organization_id, limit=100)
            customer_quotes = [q for q in quotes if q.get('customer_id') == customer_id]
            
            return {
                "customer": customer,
                "health_score": CustomerIntelligenceService._calculate_health_score(customer_quotes),
                "insights": CustomerIntelligenceService._generate_insights(customer, customer_quotes),
                "metrics": CustomerIntelligenceService._calculate_metrics(customer_quotes),
                "predictions": CustomerIntelligenceService._generate_predictions(customer_quotes),
            }
        except Exception as e:
            import logging
            logging.error(f"Error analyzing customer {customer_id}: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return {"error": f"Failed to analyze customer: {str(e)}"}
    
    @staticmethod
    def _calculate_health_score(quotes: List[Dict]) -> Dict[str, Any]:
        """Calculate a simple 0-100 customer health score."""
        if not quotes:
            return {
                "score": 50,
                "label": "New Customer",
                "color": "gray",
                "explanation": "Not enough data yet. Send a quote to start building the relationship."
            }
        
        # Factors (simplified for beginners)
        total_quotes = len(quotes)
        won_quotes = len([q for q in quotes if q.get('status') == 'accepted'])
        
        # Count recent quotes with safe date parsing
        recent_quotes = 0
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)
        for q in quotes:
            created_at = q.get('created_at')
            if created_at:
                try:
                    created_dt = datetime.fromisoformat(str(created_at).replace('Z', '+00:00'))
                    if created_dt > cutoff_date:
                        recent_quotes += 1
                except (ValueError, TypeError):
                    continue
        
        # Calculate score
        win_rate = (won_quotes / total_quotes * 100) if total_quotes > 0 else 0
        
        # Simple scoring
        score = 50  # Start neutral
        score += min(win_rate, 40)  # Up to 40 points for win rate
        score += min(recent_quotes * 5, 10)  # Up to 10 points for recent activity
        
        score = min(100, max(0, int(score)))
        
        # Label and explanation
        if score >= 80:
            return {
                "score": score,
                "label": "Excellent",
                "color": "green",
                "explanation": "This customer buys consistently. Prioritize their requests."
            }
        elif score >= 60:
            return {
                "score": score,
                "label": "Good",
                "color": "blue",
                "explanation": "Solid relationship. Keep nurturing with regular follow-ups."
            }
        elif score >= 40:
            return {
                "score": score,
                "label": "At Risk",
                "color": "amber",
                "explanation": "Engagement dropping. Reach out to understand their needs."
            }
        else:
            return {
                "score": score,
                "label": "Needs Attention",
                "color": "red",
                "explanation": "This relationship needs work. Schedule a check-in call."
            }
    
    @staticmethod
    def _generate_insights(customer: Dict, quotes: List[Dict]) -> List[CustomerInsight]:
        """Generate actionable insights for a customer."""
        insights = []
        
        if not quotes:
            insights.append(CustomerInsight(
                type="opportunity",
                title="New Customer - First Impression Counts",
                description="This is a new relationship. Send a competitive first quote to establish trust.",
                action="Create First Quote",
                action_link=f"/quotes/new?customer={customer['id']}",
                impact="high",
                metric_value=None,
                metric_label=None
            ))
            return insights
        
        # Insight 1: Win Rate
        total = len(quotes)
        won = len([q for q in quotes if q.get('status') == 'accepted'])
        win_rate = (won / total * 100) if total > 0 else 0
        
        if win_rate >= 70:
            insights.append(CustomerInsight(
                type="behavior",
                title="VIP Customer - High Win Rate",
                description=f"They accept {win_rate:.0f}% of your quotes. They trust your pricing and service.",
                action="View Quote History",
                action_link=f"/quotes?customer={customer['id']}",
                impact="high",
                metric_value=win_rate,
                metric_label="Win Rate"
            ))
        elif win_rate < 30 and total >= 3:
            insights.append(CustomerInsight(
                type="risk",
                title="Price Sensitivity Detected",
                description=f"Only {win_rate:.0f}% of quotes accepted. They may be shopping around for better prices.",
                action="Review Competitor Pricing",
                action_link="/mappings",
                impact="high",
                metric_value=win_rate,
                metric_label="Win Rate"
            ))
        
        # Insight 2: Quote Gap
        if quotes:
            created_dates = [q.get('created_at') for q in quotes if q.get('created_at')]
            if created_dates:
                try:
                    last_quote_date = max(created_dates)
                    last_quote_dt = datetime.fromisoformat(str(last_quote_date).replace('Z', '+00:00'))
                    days_since = (datetime.now(timezone.utc) - last_quote_dt).days
                    
                    if days_since > 60:
                        insights.append(CustomerInsight(
                            type="risk",
                            title="Quote Gap - Customer Gone Quiet",
                            description=f"No quotes requested in {days_since} days. They might be buying elsewhere.",
                            action="Send Check-in Email",
                            action_link=f"/customers/{customer['id']}",
                            impact="high",
                            metric_value=days_since,
                            metric_label="Days Since Last Quote"
                        ))
                    elif days_since > 30:
                        insights.append(CustomerInsight(
                            type="opportunity",
                            title="Due for a Check-in",
                            description=f"It's been {days_since} days. A quick call could spark a new order.",
                            action="View Contact Info",
                            action_link=f"/customers/{customer['id']}",
                            impact="medium",
                            metric_value=days_since,
                            metric_label="Days Since Last Quote"
                        ))
                except (ValueError, TypeError):
                    pass  # Skip this insight if date parsing fails
        
        # Insight 3: Average Order Value
        accepted_quotes = [q for q in quotes if q.get('status') == 'accepted']
        if accepted_quotes:
            avg_value = sum(q.get('total', 0) for q in accepted_quotes) / len(accepted_quotes)
            
            if avg_value > 10000:
                insights.append(CustomerInsight(
                    type="behavior",
                    title="High-Value Buyer",
                    description=f"Average order is ${avg_value:,.0f}. Focus on larger projects with this customer.",
                    action="Create Large Quote",
                    action_link=f"/quotes/new?customer={customer['id']}",
                    impact="high",
                    metric_value=avg_value,
                    metric_label="Average Order"
                ))
        
        # Insight 4: Pending Follow-ups
        pending_quotes = [q for q in quotes if q.get('status') == 'sent']
        follow_up_needed = []
        for q in pending_quotes:
            date_str = q.get('sent_at') or q.get('created_at')
            if date_str:
                try:
                    sent_date = datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
                    if (datetime.now(timezone.utc) - sent_date).days > 3:
                        follow_up_needed.append(q)
                except (ValueError, TypeError):
                    continue
        
        if follow_up_needed:
            total_value = sum(q.get('total', 0) for q in follow_up_needed)
            insights.append(CustomerInsight(
                type="opportunity",
                title=f"{len(follow_up_needed)} Quote{'s' if len(follow_up_needed) > 1 else ''} Need Follow-up",
                description=f"${total_value:,.0f} in pending quotes. A quick call could close these deals.",
                action="Follow Up Now",
                action_link=f"/quotes/{follow_up_needed[0]['id']}",
                impact="high",
                metric_value=total_value,
                metric_label="Pending Value"
            ))
        
        # Insight 5: Response Time Pattern
        if len(quotes) >= 3:
            response_times = []
            for q in quotes:
                sent_at = q.get('sent_at')
                accepted_at = q.get('accepted_at')
                if sent_at and accepted_at:
                    try:
                        sent = datetime.fromisoformat(str(sent_at).replace('Z', '+00:00'))
                        accepted = datetime.fromisoformat(str(accepted_at).replace('Z', '+00:00'))
                        response_times.append((accepted - sent).days)
                    except (ValueError, TypeError):
                        continue
            
            if response_times:
                avg_response = sum(response_times) / len(response_times)
                if avg_response < 3:
                    insights.append(CustomerInsight(
                        type="behavior",
                        title="Fast Decision Maker",
                        description=f"They typically decide in {avg_response:.0f} days. Quick turnarounds are their style.",
                        action="Send Competitive Quote",
                        action_link=f"/quotes/new?customer={customer['id']}",
                        impact="medium",
                        metric_value=round(avg_response, 1),
                        metric_label="Avg Decision Time"
                    ))
        
        return insights
    
    @staticmethod
    def _calculate_metrics(quotes: List[Dict]) -> Dict[str, Any]:
        """Calculate simple, understandable metrics."""
        if not quotes:
            return {
                "total_quotes": 0,
                "total_value": 0,
                "win_rate": 0,
                "avg_quote_value": 0,
                "lifetime_value": 0,
                "quotes_this_month": 0,
            }
        
        accepted = [q for q in quotes if q.get('status') == 'accepted']
        total_value = sum(q.get('total', 0) for q in accepted)
        
        # Count quotes this month with safe date parsing
        quotes_this_month = 0
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        for q in quotes:
            created_at = q.get('created_at')
            if created_at:
                try:
                    created_dt = datetime.fromisoformat(str(created_at).replace('Z', '+00:00'))
                    if created_dt > cutoff_date:
                        quotes_this_month += 1
                except (ValueError, TypeError):
                    continue
        
        return {
            "total_quotes": len(quotes),
            "total_value": sum(q.get('total', 0) for q in quotes),
            "win_rate": round((len(accepted) / len(quotes) * 100), 1) if quotes else 0,
            "avg_quote_value": round(sum(q.get('total', 0) for q in quotes) / len(quotes), 2),
            "lifetime_value": round(total_value, 2),
            "quotes_this_month": quotes_this_month,
        }
    
    @staticmethod
    def _generate_predictions(quotes: List[Dict]) -> List[Dict[str, Any]]:
        """Generate simple predictions with explanations."""
        predictions = []
        
        if not quotes:
            predictions.append({
                "title": "Likely to Request Quote Soon?",
                "prediction": "Unknown",
                "explanation": "Not enough history yet. After 2-3 quotes, we'll predict their next order timing.",
                "confidence": "low"
            })
            return predictions
        
        # Parse quote dates safely
        quote_dates = []
        for q in quotes:
            created_at = q.get('created_at')
            if created_at:
                try:
                    dt = datetime.fromisoformat(str(created_at).replace('Z', '+00:00'))
                    quote_dates.append(dt)
                except (ValueError, TypeError):
                    continue
        
        quote_dates = sorted(quote_dates)
        
        # Predict next order based on pattern
        if len(quote_dates) >= 2:
            gaps = [(quote_dates[i+1] - quote_dates[i]).days for i in range(len(quote_dates)-1)]
            avg_gap = sum(gaps) / len(gaps)
            last_quote = quote_dates[-1]
            predicted_next = last_quote + timedelta(days=avg_gap)
            days_until = (predicted_next - datetime.now(timezone.utc)).days
            
            if days_until < 0:
                predictions.append({
                    "title": "Overdue for Next Order",
                    "prediction": f"Expected {abs(days_until)} days ago",
                    "explanation": f"They typically order every {avg_gap:.0f} days. Time to check in!",
                    "confidence": "medium" if len(gaps) >= 3 else "low"
                })
            elif days_until <= 7:
                predictions.append({
                    "title": "Order Expected Soon",
                    "prediction": f"Within {days_until} days",
                    "explanation": f"Based on their pattern of ordering every {avg_gap:.0f} days.",
                    "confidence": "medium" if len(gaps) >= 3 else "low"
                })
            else:
                predictions.append({
                    "title": "Next Order Prediction",
                    "prediction": f"In about {days_until} days",
                    "explanation": f"They order every {avg_gap:.0f} days on average.",
                    "confidence": "medium" if len(gaps) >= 3 else "low"
                })
        
        # Predict likelihood to accept next quote
        accepted = [q for q in quotes if q.get('status') == 'accepted']
        if len(quotes) >= 3:
            win_rate = len(accepted) / len(quotes)
            if win_rate >= 0.7:
                predictions.append({
                    "title": "Likely to Accept Next Quote",
                    "prediction": "High Probability",
                    "explanation": f"They've accepted {win_rate*100:.0f}% of quotes historically.",
                    "confidence": "high"
                })
            elif win_rate <= 0.3:
                predictions.append({
                    "title": "May Shop Around",
                    "prediction": "Review Pricing Carefully",
                    "explanation": f"They only accept {win_rate*100:.0f}% of quotes. Competitor check recommended.",
                    "confidence": "high"
                })
        
        return predictions
    
    @staticmethod
    def get_customer_list_intelligence(organization_id: str) -> Dict[str, Any]:
        """Get intelligence summary for all customers."""
        try:
            customers = list_customers(organization_id=organization_id, limit=100)
            quotes = list_quotes(organization_id=organization_id, limit=200)
            
            # Categorize customers
            categories = {
                "vip": [],  # High win rate, recent activity
                "active": [],  # Regular quotes
                "at_risk": [],  # Dropping off
                "new": [],  # No quotes yet
            }
            
            for customer in customers:
                try:
                    customer_quotes = [q for q in quotes if q.get('customer_id') == customer['id']]
                    
                    if not customer_quotes:
                        categories["new"].append(customer)
                        continue
                    
                    # Check last activity - handle missing or invalid dates
                    created_dates = [q.get('created_at') for q in customer_quotes if q.get('created_at')]
                    if not created_dates:
                        categories["new"].append(customer)
                        continue
                    
                    last_quote = max(created_dates)
                    if not last_quote:
                        categories["new"].append(customer)
                        continue
                    
                    try:
                        # Handle both 'Z' suffix and '+00:00' format
                        last_quote_str = str(last_quote).replace('Z', '+00:00')
                        last_quote_dt = datetime.fromisoformat(last_quote_str)
                        days_since = (datetime.now(timezone.utc) - last_quote_dt).days
                    except (ValueError, TypeError):
                        # If date parsing fails, treat as new
                        categories["new"].append(customer)
                        continue
                    
                    # Check win rate
                    accepted = len([q for q in customer_quotes if q.get('status') == 'accepted'])
                    win_rate = (accepted / len(customer_quotes)) if customer_quotes else 0
                    
                    if win_rate >= 0.7 and days_since < 60:
                        categories["vip"].append({**customer, "win_rate": round(win_rate * 100, 1)})
                    elif days_since > 90:
                        categories["at_risk"].append({**customer, "days_since": days_since})
                    else:
                        categories["active"].append(customer)
                        
                except Exception as e:
                    # Log error but don't fail the entire request for one customer
                    import logging
                    logging.error(f"Error processing customer {customer.get('id', 'unknown')}: {e}")
                    categories["new"].append(customer)
            
            return {
                "total_customers": len(customers),
                "categories": categories,
                "summary": {
                    "vip_count": len(categories["vip"]),
                    "active_count": len(categories["active"]),
                    "at_risk_count": len(categories["at_risk"]),
                    "new_count": len(categories["new"]),
                }
            }
        except Exception as e:
            import logging
            logging.error(f"Error in get_customer_list_intelligence: {e}")
            import traceback
            logging.error(traceback.format_exc())
            # Return empty but valid response instead of crashing
            return {
                "total_customers": 0,
                "categories": {"vip": [], "active": [], "at_risk": [], "new": []},
                "summary": {"vip_count": 0, "active_count": 0, "at_risk_count": 0, "new_count": 0},
                "error": str(e)
            }
