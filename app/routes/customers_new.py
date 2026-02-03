"""
Customers API routes using local SQLite.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from app.database_sqlite import (
    create_customer, get_customer_by_id, list_customers, update_customer
)
from fastapi import Depends
from app.middleware.organization import get_current_user_and_org

router = APIRouter(prefix="/customers", tags=["customers"])


class CustomerCreate(BaseModel):
    name: str
    email: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


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


@router.post("/", response_model=CustomerResponse)
async def create_customer_endpoint(
    customer: CustomerCreate,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Create a new customer."""
    user_id, org_id = user_org
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
