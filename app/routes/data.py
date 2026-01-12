"""
Data API routes for querying emails and line items.
"""

from fastapi import APIRouter, HTTPException, Query
from app.database import db
from app.models import EmailStatus
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data", tags=["data"])


@router.get("/emails")
async def get_emails(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    Get list of inbound emails.
    
    Query parameters:
    - status: Filter by processing status (pending/processing/processed/failed)
    - limit: Maximum number of results (max 100)
    - offset: Pagination offset
    """
    try:
        if status:
            emails = await db.get_emails_by_status(status, limit)
        else:
            # Get all recent emails (implement in database.py if needed)
            emails = await db.get_emails_by_status(EmailStatus.PROCESSED, limit)
        
        return {
            "emails": emails,
            "count": len(emails),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error fetching emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emails/{email_id}")
async def get_email_details(email_id: str):
    """
    Get detailed information about a specific email.
    
    Includes:
    - Email metadata
    - All extracted line items
    - Processing status and timestamps
    """
    try:
        email = await db.get_email_by_id(email_id)
        
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Get line items
        line_items = await db.get_line_items_by_email(email_id)
        
        return {
            "email": email,
            "line_items": line_items,
            "item_count": len(line_items)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching email details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/line-items")
async def get_line_items(
    email_id: Optional[str] = Query(None, description="Filter by email ID"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(default=100, le=1000)
):
    """
    Get line items with optional filters.
    
    Query parameters:
    - email_id: Get items from specific email
    - start_date: Filter items extracted after this date
    - end_date: Filter items extracted before this date
    - limit: Maximum number of results
    """
    try:
        if email_id:
            items = await db.get_line_items_by_email(email_id)
        elif start_date and end_date:
            items = await db.get_line_items_by_date_range(start_date, end_date)
        else:
            # Default: last 7 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)
            items = await db.get_line_items_by_date_range(start_date, end_date)
        
        # Apply limit
        items = items[:limit]
        
        return {
            "line_items": items,
            "count": len(items),
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error fetching line items: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_statistics(
    days: int = Query(default=30, le=365, description="Number of days to analyze")
):
    """
    Get processing statistics.
    
    Returns:
    - Total emails processed
    - Total line items extracted
    - Average confidence score
    - Success rate
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all emails in date range
        processed_emails = await db.get_emails_by_status(EmailStatus.PROCESSED, 10000)
        failed_emails = await db.get_emails_by_status(EmailStatus.FAILED, 10000)
        
        # Filter by date
        processed_emails = [
            e for e in processed_emails
            if start_date <= datetime.fromisoformat(e['received_at'].replace('Z', '+00:00')) <= end_date
        ]
        
        failed_emails = [
            e for e in failed_emails
            if start_date <= datetime.fromisoformat(e['received_at'].replace('Z', '+00:00')) <= end_date
        ]
        
        total_emails = len(processed_emails) + len(failed_emails)
        
        # Get line items
        line_items = await db.get_line_items_by_date_range(start_date, end_date)
        
        # Calculate average confidence
        confidence_scores = [
            item['confidence_score']
            for item in line_items
            if item.get('confidence_score') is not None
        ]
        
        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores else 0
        )
        
        return {
            "period_days": days,
            "total_emails": total_emails,
            "processed_emails": len(processed_emails),
            "failed_emails": len(failed_emails),
            "success_rate": (
                len(processed_emails) / total_emails
                if total_emails > 0 else 0
            ),
            "total_line_items": len(line_items),
            "average_confidence": round(avg_confidence, 2),
            "items_per_email": (
                len(line_items) / len(processed_emails)
                if processed_emails else 0
            )
        }
        
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
