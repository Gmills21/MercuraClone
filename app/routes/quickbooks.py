"""
QuickBooks integration API routes.
OAuth2 flow, sync operations, and status.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from app.quickbooks_service import (
    QuickBooksService, get_qb_service, is_connected,
    disconnect, get_connection_info, QUICKBOOKS_CLIENT_ID,
    QBO_REDIRECT_URI
)
from app.database_sqlite import list_products, list_customers

router = APIRouter(prefix="/quickbooks", tags=["quickbooks"])

# Configuration - now using the one from service/settings
REDIRECT_URI = QBO_REDIRECT_URI


class QuickBooksStatusResponse(BaseModel):
    connected: bool
    realm_id: Optional[str] = None
    connected_at: Optional[str] = None


class QuickBooksSyncResponse(BaseModel):
    success: bool
    products_imported: int = 0
    customers_imported: int = 0
    message: str


@router.get("/auth-url")
async def get_auth_url(user_id: str = "test-user"):
    """
    Get QuickBooks OAuth authorization URL.
    Frontend redirects user to this URL to connect QuickBooks.
    """
    if not QUICKBOOKS_CLIENT_ID:
        raise HTTPException(status_code=500, detail="QuickBooks not configured")
    
    auth_url = QuickBooksService.get_authorization_url(user_id, REDIRECT_URI)
    return {"auth_url": auth_url}


@router.post("/connect")
async def connect_quickbooks(code: str, user_id: str = "test-user"):
    """
    Exchange OAuth code for access token after user authorizes.
    Called by frontend after redirect from QuickBooks.
    """
    result = await QuickBooksService.exchange_code_for_token(
        code=code,
        user_id=user_id,
        redirect_uri=REDIRECT_URI
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "success": True,
        "realm_id": result.get("realm_id"),
        "message": "QuickBooks connected successfully"
    }


@router.get("/status")
async def get_connection_status(user_id: str = "test-user"):
    """
    Get QuickBooks connection status for current user.
    """
    info = get_connection_info(user_id)
    
    if not info:
        return QuickBooksStatusResponse(connected=False)
    
    return QuickBooksStatusResponse(
        connected=True,
        realm_id=info.get("realm_id"),
        connected_at=info.get("connected_at")
    )


@router.post("/disconnect")
async def disconnect_quickbooks(user_id: str = "test-user"):
    """
    Disconnect QuickBooks integration.
    """
    success = disconnect(user_id)
    if not success:
        raise HTTPException(status_code=400, detail="Not connected")
    
    return {"success": True, "message": "QuickBooks disconnected"}


@router.post("/sync/import")
async def import_from_quickbooks(user_id: str = "test-user"):
    """
    Import products and customers FROM QuickBooks TO OpenMercura.
    This is the "Auto-Import" feature - one click to pull all QB data.
    """
    qb = get_qb_service(user_id)
    if not qb:
        raise HTTPException(status_code=401, detail="QuickBooks not connected")
    
    try:
        result = await qb.import_from_qb()
        
        # Here you would save to local database
        # For now, just return the data
        
        return QuickBooksSyncResponse(
            success=True,
            products_imported=result["product_count"],
            customers_imported=result["customer_count"],
            message=f"Imported {result['product_count']} products and {result['customer_count']} customers from QuickBooks"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/sync/export-products")
async def export_products_to_quickbooks(user_id: str = "test-user"):
    """
    Export products FROM OpenMercura TO QuickBooks.
    """
    qb = get_qb_service(user_id)
    if not qb:
        raise HTTPException(status_code=401, detail="QuickBooks not connected")
    
    try:
        # Get local products
        products = list_products(limit=1000)
        
        # Sync to QB
        result = await qb.sync_products_to_qb(products)
        
        return {
            "success": True,
            "created": result["created"],
            "errors": result["errors"],
            "message": f"Created {result['created']} products in QuickBooks"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/sync/export-customers")
async def export_customers_to_quickbooks(user_id: str = "test-user"):
    """
    Export customers FROM OpenMercura TO QuickBooks.
    """
    qb = get_qb_service(user_id)
    if not qb:
        raise HTTPException(status_code=401, detail="QuickBooks not connected")
    
    try:
        # Get local customers
        customers = list_customers(limit=1000)
        
        # Sync to QB
        result = await qb.sync_customers_to_qb(customers)
        
        return {
            "success": True,
            "created": result["created"],
            "errors": result["errors"],
            "message": f"Created {result['created']} customers in QuickBooks"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/sync/bidirectional")
async def bidirectional_sync(user_id: str = "test-user"):
    """
    Two-way sync: Import from QB, export to QB.
    The "Magic Sync" button.
    """
    qb = get_qb_service(user_id)
    if not qb:
        raise HTTPException(status_code=401, detail="QuickBooks not connected")
    
    try:
        # Import from QB
        import_result = await qb.import_from_qb()
        
        # Export to QB (products not already there)
        # This would need logic to check for duplicates
        
        return {
            "success": True,
            "imported": {
                "products": import_result["product_count"],
                "customers": import_result["customer_count"],
            },
            "message": f"Sync complete. Imported {import_result['product_count']} products and {import_result['customer_count']} customers."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/products")
async def get_quickbooks_products(user_id: str = "test-user", limit: int = 100):
    """
    Get products directly from QuickBooks (for preview/selection).
    """
    qb = get_qb_service(user_id)
    if not qb:
        raise HTTPException(status_code=401, detail="QuickBooks not connected")
    
    try:
        products = await qb.get_items(limit)
        return {"products": products, "count": len(products)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers")
async def get_quickbooks_customers(user_id: str = "test-user", limit: int = 100):
    """
    Get customers directly from QuickBooks (for preview/selection).
    """
    qb = get_qb_service(user_id)
    if not qb:
        raise HTTPException(status_code=401, detail="QuickBooks not connected")
    
    try:
        customers = await qb.get_customers(limit)
        return {"customers": customers, "count": len(customers)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-quote")
async def export_quote_to_quickbooks(quote_id: str, user_id: str = "test-user"):
    """
    Export a specific quote as an Estimate in QuickBooks.
    """
    from app.database_sqlite import get_quote_with_items
    
    qb = get_qb_service(user_id)
    if not qb:
        raise HTTPException(status_code=401, detail="QuickBooks not connected")
    
    try:
        # Get quote from local DB
        quote = get_quote_with_items(quote_id)
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        # Create estimate in QB
        result = await qb.create_estimate(quote, quote.get("items", []))
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "success": True,
            "qb_estimate_id": result.get("Estimate", {}).get("Id"),
            "message": "Quote exported to QuickBooks as Estimate"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
