from fastapi import APIRouter, HTTPException, Query, Header
from fastapi.responses import FileResponse
from app.database import db
from app.models import Quote, QuoteStatus
from app.services.export_service import export_service
from app.services.email_service import email_service
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import logging
import base64
import os
import secrets
from datetime import datetime, timedelta

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


@router.get("/email/{email_id}")
async def get_quotes_by_email(email_id: str):
    """Get quotes created from a specific email."""
    try:
        quotes = await db.get_quotes_by_email_id(email_id)
        return {"quotes": quotes}
    except Exception as e:
        logger.error(f"Error fetching quotes by email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{quote_id}/generate-export")
async def generate_quote_export(
    quote_id: str,
    format: str = Query("excel", regex="^(excel|pdf)$")
):
    """Generate quote export file (Excel or PDF)."""
    try:
        quote = await db.get_quote(quote_id)
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        if format == "excel":
            filepath = await export_service.export_quote_to_excel(quote)
            return FileResponse(
                path=filepath,
                media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                filename=filepath.split('/')[-1] if '/' in filepath else filepath.split('\\')[-1]
            )
        else:
            # PDF generation would go here
            raise HTTPException(status_code=400, detail="PDF export not yet implemented")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating quote export: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{quote_id}/draft-reply")
async def draft_reply_email(
    quote_id: str,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Generate a draft reply email for a quote."""
    try:
        quote = await db.get_quote(quote_id)
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Get email details if available
        email_id = quote.get('inbound_email_id')
        sender_email = quote.get('metadata', {}).get('source_sender', 'customer@example.com')
        
        # Generate draft email content
        subject = f"Re: Quote {quote.get('quote_number', '')}"
        
        customer_name = quote.get('customers', {}).get('name', 'Valued Customer') if quote.get('customers') else 'Valued Customer'
        
        email_body = f"""Dear {customer_name},

Thank you for your quote request. Please find attached our quotation for your review.

Quote Number: {quote.get('quote_number', '')}
Total Amount: ${quote.get('total_amount', 0):,.2f}
Valid Until: {quote.get('valid_until', '30 days from date of quote')}

The quote includes the following items:
"""
        
        for item in quote.get('items', []):
            email_body += f"\n- {item.get('description', 'Item')} (Qty: {item.get('quantity', 1)}) - ${item.get('unit_price', 0):,.2f} each"
        
        email_body += f"""

Please let us know if you have any questions or require any modifications to this quote.

Best regards,
Your Sales Team
"""
        
        return {
            "to_email": sender_email,
            "subject": subject,
            "body": email_body,
            "quote_id": quote_id,
            "quote_number": quote.get('quote_number', '')
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error drafting reply email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{quote_id}/generate-link")
async def generate_quote_link(
    quote_id: str,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Generate a shareable link for a quote that customers can view and approve."""
    try:
        quote = await db.get_quote(quote_id)
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Verify user owns this quote
        if quote.get('user_id') != x_user_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Generate a secure token
        share_token = secrets.token_urlsafe(32)
        
        # Store token in quote metadata with expiration (90 days)
        metadata = quote.get('metadata', {})
        metadata['share_token'] = share_token
        metadata['share_token_created_at'] = datetime.utcnow().isoformat()
        metadata['share_token_expires_at'] = (datetime.utcnow() + timedelta(days=90)).isoformat()
        
        # Update quote with token
        await db.update_quote(quote_id, {'metadata': metadata}, None)
        
        # Generate the public URL
        # In production, this should use your actual frontend URL from settings
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        public_url = f"{frontend_url}/quote/{share_token}"
        
        return {
            "quote_id": quote_id,
            "share_token": share_token,
            "public_url": public_url,
            "expires_at": metadata['share_token_expires_at'],
            "message": "Quote link generated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating quote link: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/public/{token}")
async def get_public_quote(token: str):
    """Get a quote by share token (read-only customer view)."""
    try:
        quote = await db.get_quote_by_share_token(token)
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found or link invalid")
        
        # Check expiration
        metadata = quote.get('metadata', {})
        expires_at_str = metadata.get('share_token_expires_at')
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                if datetime.utcnow() > expires_at:
                    raise HTTPException(status_code=410, detail="Quote link has expired")
            except ValueError:
                # Invalid date format, skip expiration check
                pass
        
        # Return read-only view (exclude sensitive data)
        return {
            "quote_number": quote.get('quote_number'),
            "total_amount": quote.get('total_amount'),
            "valid_until": quote.get('valid_until'),
            "created_at": quote.get('created_at'),
            "items": quote.get('items', []),
            "customer": quote.get('customers'),
            "status": quote.get('status'),
            "is_public": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching public quote: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ConfirmQuoteRequest(BaseModel):
    """Request model for customer quote confirmation."""
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = None
    notes: Optional[str] = None
    approved_items: Optional[List[Dict[str, Any]]] = None  # Optional: allow partial approval


@router.post("/public/{token}/confirm")
async def confirm_quote(
    token: str,
    request: ConfirmQuoteRequest
):
    """Handle customer confirmation/order for a quote."""
    try:
        quote = await db.get_quote_by_share_token(token)
        
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found or link invalid")
        
        # Check expiration
        metadata = quote.get('metadata', {})
        expires_at_str = metadata.get('share_token_expires_at')
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                if datetime.utcnow() > expires_at:
                    raise HTTPException(status_code=410, detail="Quote link has expired")
            except ValueError:
                pass
        
        quote_id = quote['id']
        
        # Update quote status to ACCEPTED
        await db.update_quote_status(quote_id, QuoteStatus.ACCEPTED)
        
        # Update quote metadata with confirmation details
        metadata['customer_confirmation'] = {
            "confirmed_at": datetime.utcnow().isoformat(),
            "customer_name": request.customer_name,
            "customer_email": request.customer_email,
            "customer_phone": request.customer_phone,
            "notes": request.notes,
            "approved_items": request.approved_items
        }
        
        await db.update_quote(quote_id, {'metadata': metadata}, None)
        
        # TODO: Trigger webhook/notification to sales team
        # TODO: Send confirmation email to customer
        
        return {
            "status": "success",
            "message": "Quote confirmed successfully",
            "quote_id": quote_id,
            "quote_number": quote.get('quote_number')
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming quote: {e}")
        raise HTTPException(status_code=500, detail=str(e))
