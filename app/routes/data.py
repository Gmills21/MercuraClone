"""
Data API routes for querying emails and line items.
Note: Email ingestion feature not implemented in SQLite version.
Returns empty results for compatibility.
"""

from fastapi import APIRouter, HTTPException, Query, Header
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data", tags=["data"])


from app.database_sqlite import list_emails, get_user_by_id
from app.middleware.organization import get_current_user_and_org
from fastapi import Depends

@router.get("/emails")
async def get_emails(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get list of inbound emails.
    """
    user_id, org_id = user_org
    emails = list_emails(organization_id=org_id, status=status, limit=limit, offset=offset)
    
    return {
        "emails": emails,
        "count": len(emails),
        "limit": limit,
        "offset": offset
    }


@router.get("/emails/{email_id}")
async def get_email_details(
    email_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get detailed information about a specific email.
    """
    user_id, org_id = user_org
    from app.database_sqlite import get_db
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inbound_emails WHERE id = ? AND organization_id = ?", (email_id, org_id))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Email not found")
        
        import json
        data = dict(row)
        data["metadata"] = json.loads(data.get("metadata", "{}"))
        return data


@router.get("/line-items")
async def get_line_items(
    email_id: Optional[str] = Query(None, description="Filter by email ID"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(default=100, le=1000)
):
    """
    Get line items with optional filters.
    """
    return {
        "line_items": [],
        "count": 0,
        "limit": limit
    }


@router.get("/stats")
async def get_statistics(
    days: int = Query(default=30, le=365, description="Number of days to analyze"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Get processing statistics.
    """
    from app.database_sqlite import list_quotes
    
    try:
        # Get quotes for basic stats
        quotes = list_quotes(limit=1000)
        
        return {
            "period_days": days,
            "total_emails": 0,
            "processed_emails": 0,
            "failed_emails": 0,
            "success_rate": 0,
            "total_line_items": 0,
            "average_confidence": 0,
            "items_per_email": 0,
            "total_quotes": len(quotes),
            "total_margin_added": 0,
            "time_saved_minutes": 0,
            "time_saved_hours": 0,
            "quotes_per_day": round(len(quotes) / days, 1) if days > 0 else 0,
            "message": "Connect email provider for full analytics"
        }
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        return {
            "period_days": days,
            "total_emails": 0,
            "processed_emails": 0,
            "failed_emails": 0,
            "success_rate": 0,
            "total_line_items": 0,
            "average_confidence": 0,
            "items_per_email": 0,
            "total_quotes": 0,
            "total_margin_added": 0,
            "time_saved_minutes": 0,
            "time_saved_hours": 0,
            "quotes_per_day": 0
        }
