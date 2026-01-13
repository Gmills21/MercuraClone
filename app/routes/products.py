from fastapi import APIRouter, HTTPException, Query, Header
from app.database import db
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/products", tags=["products"])


@router.get("/search")
async def search_products(
    query: str = Query(..., min_length=1),
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Search products (catalogs) by name or SKU."""
    try:
        products = await db.search_catalog(x_user_id, query)
        return products
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        raise HTTPException(status_code=500, detail=str(e))
