"""
Quotes API routes using local SQLite.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from app.database_sqlite import (
    create_quote, add_quote_item, get_quote_with_items, list_quotes,
    get_customer_by_id, get_product_by_sku, get_quote_by_token
)
from fastapi import Depends
from app.middleware.organization import get_current_user_and_org

router = APIRouter(prefix="/quotes", tags=["quotes"])


class QuoteItemCreate(BaseModel):
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    quantity: float = 1
    unit_price: float


class QuoteCreate(BaseModel):
    customer_id: str
    items: List[QuoteItemCreate]
    tax_rate: float = 0.0
    notes: Optional[str] = None
    expires_days: int = 30


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


@router.post("/", response_model=QuoteResponse)
async def create_quote_endpoint(
    quote: QuoteCreate,
    user_org: tuple = Depends(get_current_user_and_org)
):
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
    
    quote_data = {
        "id": quote_id,
        "organization_id": org_id,
        "customer_id": quote.customer_id,
        "status": "draft",
        "subtotal": subtotal,
        "tax_rate": quote.tax_rate,
        "tax_amount": tax_amount,
        "total": total,
        "notes": quote.notes,
        "token": token,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "expires_at": (now + timedelta(days=quote.expires_days)).isoformat()
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
