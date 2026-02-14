"""
Customers API routes using local SQLite.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict
from datetime import datetime
import uuid

from app.database_sqlite import (
    create_customer, get_customer_by_id, list_customers, update_customer
)
from fastapi import Depends
from app.middleware.organization import get_current_user_and_org

router = APIRouter(prefix="/customers", tags=["customers"])


class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Customer name is required")
    email: Optional[str] = Field(None, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Customer name cannot be empty')
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.strip().lower()
            if len(v) > 255:
                raise ValueError('Email too long')
        return v


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class CustomerResponse(BaseModel):
    id: str
    name: str
    email: Optional[str]
    company: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    created_at: str
    updated_at: str
    organization_id: Optional[str] = None


# In-memory dedup cache for customer creation (use Redis in production)
_customer_creation_cache: Dict[str, datetime] = {}
_CUSTOMER_DEDUP_TTL_SECONDS = 30  # 30 seconds


def _is_duplicate_customer_creation(org_id: str, name: str, email: Optional[str]) -> bool:
    """Check if this appears to be a duplicate customer creation request."""
    from app.utils.observability import logger
    
    # Create a key based on org + normalized name + email
    key_parts = [org_id, name.lower().strip()]
    if email:
        key_parts.append(email.lower().strip())
    key = "|".join(key_parts)
    
    now = datetime.utcnow()
    
    # Clean expired entries
    expired = [k for k, v in _customer_creation_cache.items() if (now - v).seconds > _CUSTOMER_DEDUP_TTL_SECONDS]
    for k in expired:
        del _customer_creation_cache[k]
    
    # Check if this exact request was made recently
    if key in _customer_creation_cache:
        logger.info(f"Potential duplicate customer creation detected: {name[:30]}...")
        return True
    
    # Cache this request
    _customer_creation_cache[key] = now
    return False


@router.post("/", response_model=CustomerResponse)
async def create_customer_endpoint(
    customer: CustomerCreate,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Create a new customer."""
    user_id, org_id = user_org
    
    # Check for rapid duplicate submissions (race condition protection)
    if _is_duplicate_customer_creation(org_id, customer.name, customer.email):
        # Wait a moment and check if customer was just created
        import time
        time.sleep(0.5)
        
        # Try to find existing customer with same name/email in this org
        from app.database_sqlite import get_db
        with get_db() as conn:
            cursor = conn.cursor()
            if customer.email:
                cursor.execute(
                    "SELECT id FROM customers WHERE organization_id = ? AND (name = ? OR email = ?) ORDER BY created_at DESC LIMIT 1",
                    (org_id, customer.name, customer.email)
                )
            else:
                cursor.execute(
                    "SELECT id FROM customers WHERE organization_id = ? AND name = ? ORDER BY created_at DESC LIMIT 1",
                    (org_id, customer.name)
                )
            row = cursor.fetchone()
            if row:
                # Return existing customer
                existing = get_customer_by_id(row['id'], organization_id=org_id)
                if existing:
                    return CustomerResponse(**existing)
    
    now = datetime.utcnow().isoformat()
    customer_id = str(uuid.uuid4())
    
    customer_data = {
        "id": customer_id,
        "organization_id": org_id,
        "name": customer.name,
        "email": customer.email,
        "company": customer.company,
        "phone": customer.phone,
        "address": customer.address,
        "created_at": now,
        "updated_at": now
    }
    
    if create_customer(customer_data):
        return CustomerResponse(**customer_data)
    raise HTTPException(status_code=400, detail="Failed to create customer (email may exist)")


@router.get("/", response_model=List[CustomerResponse])
async def list_customers_endpoint(
    limit: int = 100, 
    offset: int = 0,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """List all customers."""
    user_id, org_id = user_org
    customers = list_customers(organization_id=org_id, limit=limit, offset=offset)
    return [CustomerResponse(**c) for c in customers]


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Get customer by ID."""
    user_id, org_id = user_org
    customer = get_customer_by_id(customer_id, organization_id=org_id)
    if customer:
        return CustomerResponse(**customer)
    raise HTTPException(status_code=404, detail="Customer not found")


@router.patch("/{customer_id}")
async def update_customer_endpoint(
    customer_id: str, 
    updates: CustomerUpdate,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Update customer."""
    user_id, org_id = user_org
    update_dict = updates.model_dump(exclude_unset=True)
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    if update_customer(customer_id, update_dict, organization_id=org_id):
        customer = get_customer_by_id(customer_id, organization_id=org_id)
        return CustomerResponse(**customer)
    raise HTTPException(status_code=404, detail="Customer not found")
