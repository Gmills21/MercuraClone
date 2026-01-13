from fastapi import APIRouter, HTTPException, Query, Header
from app.database import db
from app.models import Quote, QuoteStatus
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.post("/")
async def create_quote(
    quote: Quote,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Create a new quote."""
    try:
        quote.user_id = x_user_id
        quote_id = await db.create_quote(quote)
        return {"id": quote_id, "message": "Quote created successfully"}
    except Exception as e:
        logger.error(f"Error creating quote: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_quotes(
    x_user_id: str = Header(..., alias="X-User-ID"),
    limit: int = Query(50, le=100)
):
    """List quotes for a user."""
    try:
        quotes = await db.list_quotes(x_user_id, limit)
        return quotes
    except Exception as e:
        logger.error(f"Error listing quotes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{quote_id}")
async def get_quote(quote_id: str):
    """Get a quote by ID."""
    try:
        quote = await db.get_quote(quote_id)
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        return quote
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quote: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{quote_id}/status")
async def update_quote_status(
    quote_id: str,
    status: QuoteStatus
):
    """Update quote status."""
    try:
        await db.update_quote_status(quote_id, status)
        return {"message": "Quote status updated"}
    except Exception as e:
        logger.error(f"Error updating quote status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
