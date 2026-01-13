from fastapi import APIRouter, HTTPException, Query, Header
from app.database import db
from app.models import Customer
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("/")
async def create_customer(
    customer: Customer,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Create a new customer."""
    try:
        customer.user_id = x_user_id
        customer_id = await db.create_customer(customer)
        return {"id": customer_id, "message": "Customer created successfully"}
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_customers(
    x_user_id: str = Header(..., alias="X-User-ID"),
    limit: int = Query(100, le=500)
):
    """List customers for a user."""
    try:
        customers = await db.get_customers(x_user_id, limit)
        return customers
    except Exception as e:
        logger.error(f"Error listing customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))
