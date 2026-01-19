from fastapi import APIRouter, HTTPException, Query, Header
from app.database import db
from app.models import Quote, QuoteStatus
from app.services.export_service import export_service
from app.services.email_service import email_service
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import logging
import base64
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/quotes", tags=["quotes"])


class SendQuoteRequest(BaseModel):
    """Request model for sending a quote."""
    to_email: Optional[EmailStr] = None
    subject: Optional[str] = None
    message: Optional[str] = None



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


@router.put("/{quote_id}")
async def update_quote(
    quote_id: str,
    quote: Quote,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Update a quote and its items."""
    try:
        # Run validation
        if quote.items:
            await validate_quote_items(quote.items, x_user_id)

        # Extract data
        quote_data = quote.model_dump(exclude={'id', 'items', 'created_at', 'user_id'}, exclude_none=True)
        items_data = [item.model_dump(exclude={'id'}, exclude_none=True) for item in quote.items] if quote.items is not None else None
        
        await db.update_quote(quote_id, quote_data, items_data)
        return {"message": "Quote updated successfully"}
    except Exception as e:
        logger.error(f"Error updating quote: {e}")
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
