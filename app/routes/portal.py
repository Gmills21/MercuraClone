"""
Customer Portal API routes.
Allows customers to view their quotes and approve/reject them.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.database_sqlite import get_quote_with_items, get_customer_by_id, update_customer
from app.analytics import track_quote_event

router = APIRouter(prefix="/portal", tags=["portal"])


class QuoteResponse(BaseModel):
    id: str
    token: str
    status: str
    customer_name: str
    items: list
    subtotal: float
    tax_rate: float
    tax_amount: float
    total: float
    notes: Optional[str]
    created_at: str
    expires_at: Optional[str]


class QuoteActionRequest(BaseModel):
    action: str  # 'accept', 'reject', 'request_revision'
    comment: Optional[str] = None


@router.get("/quote/{token}")
async def get_customer_quote(token: str):
    """
    Get quote details by token (public access for customers).
    No authentication required - this is the customer-facing view.
    """
    from app.database_sqlite import get_db
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quotes WHERE token = ?", (token,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        quote = get_quote_with_items(row["id"])
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Get customer name
        customer = get_customer_by_id(quote["customer_id"])
        customer_name = customer["name"] if customer else "Unknown"
        
        # Track view event
        track_quote_event(quote["id"], "viewed_by_customer", {"portal": True})
        
        return {
            "id": quote["id"],
            "token": quote["token"],
            "status": quote["status"],
            "customer_name": customer_name,
            "items": quote.get("items", []),
            "subtotal": quote["subtotal"],
            "tax_rate": quote["tax_rate"],
            "tax_amount": quote["tax_amount"],
            "total": quote["total"],
            "notes": quote.get("notes"),
            "created_at": quote["created_at"],
            "expires_at": quote.get("expires_at"),
            "can_accept": quote["status"] in ["draft", "sent"],
            "can_reject": quote["status"] in ["draft", "sent"]
        }


@router.post("/quote/{token}/action")
async def quote_action(token: str, request: QuoteActionRequest):
    """
    Customer action on quote (accept/reject/request revision).
    Public access via token.
    """
    from app.database_sqlite import get_db
    from datetime import datetime
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quotes WHERE token = ?", (token,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        quote_id = row["id"]
        current_status = row["status"]
        
        # Validate action
        if request.action not in ["accept", "reject", "request_revision"]:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        # Map action to status
        status_map = {
            "accept": "accepted",
            "reject": "rejected",
            "request_revision": "revision_requested"
        }
        new_status = status_map[request.action]
        
        # Update quote status
        now = datetime.utcnow().isoformat()
        cursor.execute("""
            UPDATE quotes 
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, (new_status, now, quote_id))
        conn.commit()
        
        # Track event
        track_quote_event(quote_id, f"customer_{request.action}", {
            "comment": request.comment,
            "portal": True
        })
        
        return {
            "success": True,
            "action": request.action,
            "new_status": new_status,
            "message": f"Quote has been {new_status.replace('_', ' ')}"
        }


@router.get("/customer/{customer_id}/quotes")
async def get_customer_quotes(customer_id: str):
    """
    Get all quotes for a customer (public access via customer ID).
    In production, this should require email verification.
    """
    from app.database_sqlite import get_db, get_customer_by_id
    
    customer = get_customer_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM quotes 
            WHERE customer_id = ?
            ORDER BY created_at DESC
        """, (customer_id,))
        
        quotes = []
        for row in cursor.fetchall():
            quotes.append({
                "id": row["id"],
                "token": row["token"],
                "status": row["status"],
                "total": row["total"],
                "created_at": row["created_at"],
                "expires_at": row["expires_at"],
                "view_url": f"/portal/quote/{row['token']}"
            })
        
        return {
            "customer_name": customer["name"],
            "quotes": quotes,
            "count": len(quotes)
        }
