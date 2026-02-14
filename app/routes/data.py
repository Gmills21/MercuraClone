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


@router.post("/demo-data")
async def load_demo_data(user_org: tuple = Depends(get_current_user_and_org)):
    """
    Load demo data for testing. Creates sample customers, products, and quotes.
    """
    import uuid
    import secrets
    from app.database_sqlite import create_customer, create_product, create_quote, add_quote_item
    
    user_id, org_id = user_org
    now = datetime.utcnow().isoformat()
    
    created = {
        "customers": 0,
        "products": 0,
        "quotes": 0
    }
    
    # Demo customers
    demo_customers = [
        {"name": "Metro HVAC Systems", "email": "procurement@metrohvac.com", "company": "Metro HVAC Systems", "phone": "555-0101"},
        {"name": "Industrial Supply Co.", "email": "orders@industrialsupply.com", "company": "Industrial Supply Co.", "phone": "555-0102"},
        {"name": "Premier Plumbing", "email": "sales@premierplumbing.com", "company": "Premier Plumbing Inc.", "phone": "555-0103"},
        {"name": "Commercial Electric", "email": "buyers@commercialelectric.com", "company": "Commercial Electric", "phone": "555-0104"},
    ]
    
    customer_ids = {}
    for cust in demo_customers:
        cust_id = str(uuid.uuid4())
        customer_ids[cust["name"]] = cust_id
        create_customer({
            "id": cust_id,
            "organization_id": org_id,
            "name": cust["name"],
            "email": cust["email"],
            "company": cust["company"],
            "phone": cust["phone"],
            "created_at": now,
            "updated_at": now
        })
        created["customers"] += 1
    
    # Demo products
    demo_products = [
        {"sku": "PVC-6-SCH40", "name": "6\" PVC Schedule 40 Pipe", "description": "6 inch PVC Schedule 40 pressure pipe", "price": 12.50, "cost": 8.75, "category": "Pipe & Fittings"},
        {"sku": "BV-2-BRONZE", "name": "Ball Valve 2\" Bronze", "description": "2 inch bronze ball valve, threaded", "price": 45.00, "cost": 28.50, "category": "Valves"},
        {"sku": "PG-100-PSI", "name": "Pressure Gauge 0-100 PSI", "description": "0-100 PSI pressure gauge, 2.5\" dial", "price": 18.50, "cost": 11.25, "category": "Instrumentation"},
        {"sku": "CPVC-1-COIL", "name": "1\" CPVC Coil", "description": "1 inch CPVC coil, 100ft length", "price": 89.00, "cost": 62.00, "category": "Pipe & Fittings"},
        {"sku": "CHECK-3-BRASS", "name": "Check Valve 3\" Brass", "description": "3 inch brass swing check valve", "price": 125.00, "cost": 78.00, "category": "Valves"},
        {"sku": "TEF-TAPE-PTFE", "name": "Teflon Tape PTFE", "description": "Professional grade PTFE thread seal tape", "price": 2.50, "cost": 0.85, "category": "Accessories"},
    ]
    
    product_ids = {}
    for prod in demo_products:
        prod_id = str(uuid.uuid4())
        product_ids[prod["sku"]] = prod_id
        create_product({
            "id": prod_id,
            "organization_id": org_id,
            "sku": prod["sku"],
            "name": prod["name"],
            "description": prod["description"],
            "price": prod["price"],
            "cost": prod["cost"],
            "category": prod["category"],
            "created_at": now,
            "updated_at": now
        })
        created["products"] += 1
    
    # Demo quotes
    demo_quotes = [
        {
            "customer": "Metro HVAC Systems",
            "status": "sent",
            "items": [
                {"sku": "PVC-6-SCH40", "name": "6\" PVC Schedule 40 Pipe", "qty": 240, "price": 12.50},
                {"sku": "BV-2-BRONZE", "name": "Ball Valve 2\" Bronze", "qty": 12, "price": 45.00},
            ]
        },
        {
            "customer": "Industrial Supply Co.",
            "status": "draft",
            "items": [
                {"sku": "PG-100-PSI", "name": "Pressure Gauge 0-100 PSI", "qty": 6, "price": 18.50},
                {"sku": "TEF-TAPE-PTFE", "name": "Teflon Tape PTFE", "qty": 100, "price": 2.50},
            ]
        },
        {
            "customer": "Premier Plumbing",
            "status": "approved",
            "items": [
                {"sku": "CPVC-1-COIL", "name": "1\" CPVC Coil", "qty": 5, "price": 89.00},
                {"sku": "CHECK-3-BRASS", "name": "Check Valve 3\" Brass", "qty": 3, "price": 125.00},
            ]
        }
    ]
    
    for q in demo_quotes:
        quote_id = str(uuid.uuid4())
        token = secrets.token_urlsafe(32)
        
        items = []
        subtotal = 0
        for item in q["items"]:
            total = item["qty"] * item["price"]
            subtotal += total
            items.append({
                "id": str(uuid.uuid4()),
                "quote_id": quote_id,
                "product_id": product_ids.get(item["sku"]),
                "product_name": item["name"],
                "sku": item["sku"],
                "description": item["name"],
                "quantity": item["qty"],
                "unit_price": item["price"],
                "total_price": total
            })
        
        tax_rate = 0.08
        tax_amount = subtotal * tax_rate
        total = subtotal + tax_amount
        
        quote = create_quote({
            "id": quote_id,
            "organization_id": org_id,
            "customer_id": customer_ids.get(q["customer"]),
            "assigned_user_id": user_id,
            "status": q["status"],
            "subtotal": subtotal,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "total": total,
            "token": token,
            "created_at": now,
            "updated_at": now
        })
        
        if quote:
            for item in items:
                add_quote_item(item)
            created["quotes"] += 1
    
    return {
        "success": True,
        "message": "Demo data loaded successfully",
        "created": created
    }
