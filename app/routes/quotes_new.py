"""
Quotes API routes using local SQLite.
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from app.database_sqlite import (
    create_quote, add_quote_item, get_quote_with_items, list_quotes,
    get_customer_by_id, get_product_by_sku, get_quote_by_token, get_inbound_email
)
from fastapi import Depends
from app.middleware.organization import get_current_user_and_org
from app.posthog_utils import capture_event

# In-memory idempotency key store (use Redis in production)
_idempotency_keys: Dict[str, datetime] = {}
_IDEMPOTENCY_TTL_SECONDS = 300  # 5 minutes


def _check_idempotency(key: str) -> bool:
    """Check if idempotency key was already used. Returns True if duplicate."""
    from app.utils.observability import logger
    
    now = datetime.utcnow()
    
    # Clean expired keys
    expired = [k for k, v in _idempotency_keys.items() if (now - v).seconds > _IDEMPOTENCY_TTL_SECONDS]
    for k in expired:
        del _idempotency_keys[k]
    
    # Check if key exists
    if key in _idempotency_keys:
        logger.info(f"Duplicate idempotency key detected: {key[:16]}...")
        return True
    
    # Store key
    _idempotency_keys[key] = now
    return False

router = APIRouter(prefix="/quotes", tags=["quotes"])


class QuoteItemCreate(BaseModel):
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    quantity: float = Field(default=1, gt=0, description="Quantity must be greater than 0")
    unit_price: float = Field(ge=0, description="Unit price must be non-negative")

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v

    @field_validator('unit_price')
    @classmethod
    def validate_unit_price(cls, v):
        if v < 0:
            raise ValueError('Unit price cannot be negative')
        return v


class QuoteCreate(BaseModel):
    customer_id: str
    project_id: Optional[str] = None
    assignee_id: Optional[str] = None
    inbound_email_id: Optional[str] = None
    items: List[QuoteItemCreate]
    tax_rate: float = Field(default=0.0, ge=0, le=100, description="Tax rate must be between 0 and 100")
    notes: Optional[str] = None
    expires_days: int = Field(default=30, ge=1, le=365, description="Expiration must be between 1 and 365 days")
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('tax_rate')
    @classmethod
    def validate_tax_rate(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Tax rate must be between 0 and 100')
        return v

    @field_validator('expires_days')
    @classmethod
    def validate_expires_days(cls, v):
        if v < 1 or v > 365:
            raise ValueError('Expiration days must be between 1 and 365')
        return v


class QuoteItemResponse(BaseModel):
    id: str
    quote_id: str
    product_id: Optional[str]
    product_name: Optional[str]
    sku: Optional[str]
    description: Optional[str]
    quantity: float
    unit_price: float
    total_price: float


class QuoteResponse(BaseModel):
    id: str
    customer_id: str
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    customer_name: Optional[str] = None
    assigned_user_id: Optional[str] = None
    assignee_name: Optional[str] = None
    status: str
    items: List[QuoteItemResponse]
    subtotal: float
    tax_rate: float
    tax_amount: float
    total: float
    notes: Optional[str]
    token: str
    created_at: str
    updated_at: str
    expires_at: Optional[str]
    metadata: Optional[Dict[str, Any]] = None


@router.post("/", response_model=QuoteResponse)
async def create_quote_endpoint(
    quote: QuoteCreate,
    user_org: tuple = Depends(get_current_user_and_org),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key")
):
    """Create a new quote. Supports idempotency via X-Idempotency-Key header."""
    
    # Check idempotency key to prevent duplicate submissions
    if x_idempotency_key and _check_idempotency(x_idempotency_key):
        raise HTTPException(
            status_code=409, 
            detail="Duplicate submission detected. This quote has already been processed."
        )
    """Create a new quote."""
    user_id, org_id = user_org
    # Validate customer exists
    customer = get_customer_by_id(quote.customer_id, organization_id=org_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    now = datetime.utcnow()
    quote_id = str(uuid.uuid4())
    token = str(uuid.uuid4())[:12]  # Short token for sharing
    
    # Calculate totals
    subtotal = 0
    items_data = []
    
    for item in quote.items:
        total_price = item.quantity * item.unit_price
        subtotal += total_price
        
        item_data = {
            "id": str(uuid.uuid4()),
            "quote_id": quote_id,
            "product_id": item.product_id,
            "product_name": item.product_name,
            "sku": item.sku,
            "description": item.description,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total_price": total_price
        }
        items_data.append(item_data)
    
    tax_amount = subtotal * (quote.tax_rate / 100)
    total = subtotal + tax_amount
    
    # --- Time-to-Quote Calculation ---
    metadata = quote.metadata or {}
    start_time = None
    source_type = 'manual'
    
    if quote.inbound_email_id:
        email = get_inbound_email(quote.inbound_email_id)
        if email and email.get('received_at'):
            try:
                start_time = datetime.fromisoformat(email['received_at'].replace('Z', '+00:00'))
                source_type = 'email'
            except Exception as e:
                print(f"Error parsing email time: {e}")

    elif metadata.get('request_received_at'):
        try:
            start_time = datetime.fromisoformat(metadata['request_received_at'].replace('Z', '+00:00'))
            source_type = 'upload'
        except Exception:
            pass
            
    if start_time:
        # Ensure timezone awareness compatibility
        if start_time.tzinfo:
            end_time = datetime.now(start_time.tzinfo)
        else:
            end_time = datetime.utcnow()
            
        duration = (end_time - start_time).total_seconds()
        metadata['time_to_quote_seconds'] = duration
        metadata['quote_source'] = source_type
        
        # Track in PostHog
        capture_event(
            distinct_id=user_id,
            event_name='quote_created_with_impact',
            properties={
                'time_to_quote_seconds': duration,
                'source': source_type,
                'quote_amount': total,
                'organization_id': org_id,
                'items_count': len(quote.items)
            },
            groups={'organization': org_id}
        )

    quote_data = {
        "id": quote_id,
        "organization_id": org_id,
        "customer_id": quote.customer_id,
        "project_id": quote.project_id,
        "assigned_user_id": quote.assignee_id,
        "status": "draft",
        "subtotal": subtotal,
        "tax_rate": quote.tax_rate,
        "tax_amount": tax_amount,
        "total": total,
        "notes": quote.notes,
        "token": token,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "expires_at": (now + timedelta(days=quote.expires_days)).isoformat(),
        "metadata": metadata
    }
    
    # Save quote and items
    if create_quote(quote_data):
        for item_data in items_data:
            add_quote_item(item_data)
        
        # Return with items
        result = get_quote_with_items(quote_id)
        return QuoteResponse(**result)
    
    raise HTTPException(status_code=500, detail="Failed to create quote")


@router.get("/", response_model=List[QuoteResponse])
async def list_quotes_endpoint(
    limit: int = 100, 
    offset: int = 0,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """List all quotes."""
    user_id, org_id = user_org
    quotes = list_quotes(organization_id=org_id, limit=limit, offset=offset)
    # Load items for each quote
    results = []
    for q in quotes:
        quote_with_items = get_quote_with_items(q["id"], organization_id=org_id)
        if quote_with_items:
            results.append(QuoteResponse(**quote_with_items))
    return results


@router.get("/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    quote_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Get quote by ID."""
    user_id, org_id = user_org
    quote = get_quote_with_items(quote_id, organization_id=org_id)
    if quote:
        return QuoteResponse(**quote)
    raise HTTPException(status_code=404, detail="Quote not found")


@router.get("/token/{token}", response_model=QuoteResponse)
async def get_quote_by_token_endpoint(token: str):
    """Get quote by share token (public access)."""
    # Find quote by token directly
    quote = get_quote_by_token(token)
    if quote:
        return QuoteResponse(**quote)
    raise HTTPException(status_code=404, detail="Quote not found")


@router.get("/email/{email_id}", response_model=Dict[str, List[QuoteResponse]])
async def get_quotes_by_email_endpoint(
    email_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Get quotes created from a specific email."""
    user_id, org_id = user_org
    from app.database_sqlite import get_quotes_by_email
    quotes = get_quotes_by_email(email_id, organization_id=org_id)
    
    # Map to QuoteResponse
    results = [QuoteResponse(**q) for q in quotes]
    return {"quotes": results}


class QuoteUpdate(BaseModel):
    status: Optional[str] = None
    assignee_id: Optional[str] = None
    notes: Optional[str] = None
    project_id: Optional[str] = None


@router.patch("/{quote_id}", response_model=QuoteResponse)
async def update_quote_endpoint(
    quote_id: str,
    updates: QuoteUpdate,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Update a quote."""
    user_id, org_id = user_org
    from app.database_sqlite import update_quote
    
    # Map assignee_id to assigned_user_id for DB
    db_updates = updates.dict(exclude_unset=True)
    if "assignee_id" in db_updates:
        db_updates["assigned_user_id"] = db_updates.pop("assignee_id")
        
    success = update_quote(quote_id, db_updates, organization_id=org_id)
    if success:
        result = get_quote_with_items(quote_id, organization_id=org_id)
        return QuoteResponse(**result)
    
    raise HTTPException(status_code=404, detail="Quote not found or update failed")
