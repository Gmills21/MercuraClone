"""
Products API routes using local SQLite.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import pandas as pd
import io

from app.database_sqlite import create_product, get_product_by_sku, list_products

router = APIRouter(prefix="/products", tags=["products"])


class ProductCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    price: float
    cost: Optional[float] = None
    category: Optional[str] = None
    competitor_sku: Optional[str] = None


class ProductResponse(BaseModel):
    id: str
    sku: str
    name: str
    description: Optional[str]
    price: float
    cost: Optional[float]
    category: Optional[str]
    competitor_sku: Optional[str]
    created_at: str
    updated_at: str


@router.post("/", response_model=ProductResponse)
async def create_product_endpoint(product: ProductCreate):
    """Create a new product."""
    now = datetime.utcnow().isoformat()
    product_id = str(uuid.uuid4())
    
    product_data = {
        "id": product_id,
        "sku": product.sku,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "cost": product.cost,
        "category": product.category,
        "competitor_sku": product.competitor_sku,
        "created_at": now,
        "updated_at": now
    }
    
    if create_product(product_data):
        return ProductResponse(**product_data)
    raise HTTPException(status_code=400, detail="Failed to create product (SKU may exist)")


@router.get("/", response_model=List[ProductResponse])
async def list_products_endpoint(limit: int = 100, offset: int = 0):
    """List all products."""
    products = list_products(limit, offset)
    return [ProductResponse(**p) for p in products]


@router.get("/sku/{sku}", response_model=ProductResponse)
async def get_product_by_sku_endpoint(sku: str):
    """Get product by SKU."""
    product = get_product_by_sku(sku)
    if product:
        return ProductResponse(**product)
    raise HTTPException(status_code=404, detail="Product not found")


@router.post("/upload")
async def upload_products(file: UploadFile = File(...)):
    """Upload products from CSV/Excel."""
    try:
        contents = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Invalid file format. Upload CSV or Excel.")
        
        # Normalize columns
        df.columns = [str(c).lower().strip() for c in df.columns]
        
        created = 0
        skipped = 0
        
        for _, row in df.iterrows():
            sku = row.get('sku') or row.get('item number') or row.get('part number')
            name = row.get('name') or row.get('item name') or row.get('product name')
            price = row.get('price') or row.get('unit_price') or row.get('cost') or 0
            
            if pd.isna(sku) or pd.isna(name):
                skipped += 1
                continue
            
            # Clean price
            try:
                if isinstance(price, str):
                    price = float(price.replace('$', '').replace(',', '').strip())
                price = float(price)
            except:
                price = 0.0
            
            now = datetime.utcnow().isoformat()
            product_data = {
                "id": str(uuid.uuid4()),
                "sku": str(sku).strip(),
                "name": str(name).strip(),
                "description": str(row.get('description')) if pd.notna(row.get('description')) else None,
                "price": price,
                "cost": float(row.get('cost')) if pd.notna(row.get('cost')) else None,
                "category": str(row.get('category')) if pd.notna(row.get('category')) else None,
                "competitor_sku": str(row.get('competitor_sku')) if pd.notna(row.get('competitor_sku')) else None,
                "created_at": now,
                "updated_at": now
            }
            
            if create_product(product_data):
                created += 1
            else:
                skipped += 1
        
        return {"message": f"Created {created} products, skipped {skipped}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
