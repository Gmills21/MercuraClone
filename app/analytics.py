"""
Quote analytics and performance tracking.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from app.database_sqlite import get_db


def get_quote_statistics(days: int = 30) -> Dict[str, Any]:
    """Get quote performance statistics."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Total quotes
        cursor.execute("""
            SELECT COUNT(*), SUM(total), AVG(total)
            FROM quotes
            WHERE created_at >= ?
        """, (start_date.isoformat(),))
        row = cursor.fetchone()
        total_quotes = row[0] or 0
        total_value = row[1] or 0
        avg_value = row[2] or 0
        
        # Quotes by status
        cursor.execute("""
            SELECT status, COUNT(*), SUM(total)
            FROM quotes
            WHERE created_at >= ?
            GROUP BY status
        """, (start_date.isoformat(),))
        
        by_status = {}
        for row in cursor.fetchall():
            by_status[row[0]] = {
                "count": row[1],
                "value": row[2] or 0
            }
        
        # Quotes per day (trend)
        cursor.execute("""
            SELECT date(created_at) as day, COUNT(*)
            FROM quotes
            WHERE created_at >= ?
            GROUP BY day
            ORDER BY day
        """, (start_date.isoformat(),))
        
        daily_trend = []
        for row in cursor.fetchall():
            daily_trend.append({
                "date": row[0],
                "count": row[1]
            })
        
        # Top customers by quote value
        cursor.execute("""
            SELECT c.name, COUNT(q.id) as quote_count, SUM(q.total) as total_value
            FROM quotes q
            JOIN customers c ON q.customer_id = c.id
            WHERE q.created_at >= ?
            GROUP BY q.customer_id
            ORDER BY total_value DESC
            LIMIT 5
        """, (start_date.isoformat(),))
        
        top_customers = []
        for row in cursor.fetchall():
            top_customers.append({
                "name": row[0],
                "quotes": row[1],
                "value": row[2] or 0
            })
        
        # Average time to create quote (simulated metric)
        # In real implementation, track start/end times
        avg_time_minutes = 5.0  # Placeholder
        
        return {
            "period_days": days,
            "summary": {
                "total_quotes": total_quotes,
                "total_value": round(total_value, 2),
                "average_quote_value": round(avg_value, 2),
                "average_time_minutes": avg_time_minutes,
                "quotes_per_day": round(total_quotes / days, 2) if days > 0 else 0
            },
            "by_status": by_status,
            "daily_trend": daily_trend,
            "top_customers": top_customers,
            "conversion_metrics": {
                "draft": by_status.get("draft", {}).get("count", 0),
                "sent": by_status.get("sent", {}).get("count", 0),
                "accepted": by_status.get("accepted", {}).get("count", 0),
                "conversion_rate": round(
                    by_status.get("accepted", {}).get("count", 0) / total_quotes * 100, 1
                ) if total_quotes > 0 else 0
            }
        }


def get_sales_velocity_metrics() -> Dict[str, Any]:
    """Get sales velocity metrics."""
    stats = get_quote_statistics(days=30)
    
    # Calculate velocity metrics
    total_quotes = stats["summary"]["total_quotes"]
    accepted = stats["conversion_metrics"]["accepted"]
    total_value = stats["summary"]["total_value"]
    
    return {
        "velocity": {
            "quotes_per_week": round(total_quotes / 4.3, 1),
            "quotes_per_day": stats["summary"]["quotes_per_day"],
            "win_rate": stats["conversion_metrics"]["conversion_rate"],
            "avg_deal_size": stats["summary"]["average_quote_value"]
        },
        "time_savings": {
            "manual_time_per_quote": 30,  # minutes (industry average)
            "ai_time_per_quote": 5,       # minutes (with OpenMercura)
            "time_saved_per_quote": 25,   # minutes
            "total_time_saved_hours": round(total_quotes * 25 / 60, 1)
        },
        "roi": {
            "quotes_created": total_quotes,
            "quotes_won": accepted,
            "revenue_potential": round(total_value, 2),
            "efficiency_gain": "83%"  # (30-5)/30
        }
    }


def track_quote_event(quote_id: str, event_type: str, metadata: Dict[str, Any] = None):
    """Track a quote lifecycle event."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Create events table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quote_events (
                id TEXT PRIMARY KEY,
                quote_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        import uuid
        cursor.execute("""
            INSERT INTO quote_events (id, quote_id, event_type, metadata, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            quote_id,
            event_type,
            json.dumps(metadata or {}),
            datetime.utcnow().isoformat()
        ))
        conn.commit()
