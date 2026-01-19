from fastapi import APIRouter, HTTPException, Query, Header, UploadFile, File, Body
from app.database import db
from app.models import Catalog, SuggestionRequest, SuggestionResponse, CatalogMatch, CompetitorMap
from typing import List, Dict, Any
import logging
import pandas as pd
import io
import math

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

@router.post("/upload")
async def upload_catalog(
    file: UploadFile = File(...),
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Upload catalog from CSV/Excel."""
    try:
        contents = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Invalid file format. Please upload CSV or Excel.")

        # Normalize columns
        df.columns = [str(c).lower().strip() for c in df.columns]
        
        # Map columns to Catalog model
        # Expected: sku, name/item_name, price/unit_price, category, supplier
        
        catalogs = []
        for _, row in df.iterrows():
            # Basic mapping logic
            sku = row.get('sku') or row.get('item number') or row.get('part number')
            name = row.get('name') or row.get('item name') or row.get('description') or row.get('product name')
            price = row.get('price') or row.get('unit price') or row.get('cost')
            category = row.get('category')
            supplier = row.get('supplier') or row.get('vendor')
            
            if pd.isna(sku) or pd.isna(name):
                continue # Skip invalid rows
                
            # Clean price
            try:
                if isinstance(price, str):
                    price = float(price.replace('$', '').replace(',', '').strip())
                elif pd.isna(price):
                    price = 0.0
                else:
                    price = float(price)
            except:
                price = 0.0
                
            catalog = Catalog(
                user_id=x_user_id,
                sku=str(sku).strip(),
                item_name=str(name).strip(),
                expected_price=price,
                category=str(category) if pd.notna(category) else None,
                supplier=str(supplier) if pd.notna(supplier) else None
            )
            
            # Generate embedding for semantic search
            try:
                text_to_embed = f"{catalog.item_name} {catalog.category or ''} {catalog.supplier or ''}".strip()
                embedding = await gemini_service.generate_embedding(text_to_embed)
                catalog.embedding = embedding
            except Exception as e:
                logger.warning(f"Failed to generate embedding for {catalog.sku}: {e}")
                
            catalogs.append(catalog)
            
        if not catalogs:
             raise HTTPException(status_code=400, detail="No valid items found in file.")
             
        count = await db.bulk_upsert_catalog(catalogs)
        return {"message": f"Successfully imported {count} items."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading catalog: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/competitor-maps/upload")
async def upload_competitor_maps(
    file: UploadFile = File(...),
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Upload competitor maps from CSV/Excel."""
    try:
        contents = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Invalid file format. Please upload CSV or Excel.")

        # Normalize columns
        df.columns = [str(c).lower().strip() for c in df.columns]
        
        # Map columns to CompetitorMap model
        # Expected: competitor_sku, our_sku, competitor_name
        
        maps = []
        for _, row in df.iterrows():
            comp_sku = row.get('competitor sku') or row.get('competitor_sku') or row.get('competitor part')
            our_sku = row.get('our sku') or row.get('our_sku') or row.get('internal sku') or row.get('sku')
            comp_name = row.get('competitor name') or row.get('competitor_name') or row.get('competitor')
            
            if pd.isna(comp_sku) or pd.isna(our_sku):
                continue # Skip invalid rows
            
            # Clean SKUs
            comp_sku = str(comp_sku).strip()
            our_sku = str(our_sku).strip()
            
            comp_map = CompetitorMap(
                user_id=x_user_id,
                competitor_sku=comp_sku,
                our_sku=our_sku,
                competitor_name=str(comp_name).strip() if pd.notna(comp_name) else None
            )
            maps.append(comp_map)
            
        if not maps:
             raise HTTPException(status_code=400, detail="No valid mappings found in file.")
             
        count = await db.upsert_competitor_map(maps)
        return {"message": f"Successfully imported {count} competitor mappings."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading competitor maps: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suggest", response_model=SuggestionResponse)
async def suggest_products(
    request: SuggestionRequest,
    x_user_id: str = Header(..., alias="X-User-ID")
):
    """Get product suggestions for line items."""
    try:
        results = {}
        
        for idx, item in enumerate(request.items):
            query_sku = str(item.get('sku') or '').strip()
            query_desc = str(item.get('description') or '').strip()
            
            matches = []
            seen_ids = set()
            
            # 1. Search by SKU if present
            if query_sku and len(query_sku) > 2:
                # 1a. Check Competitor Map
                comp_map = await db.get_competitor_map(x_user_id, query_sku)
                if comp_map:
                    our_sku = comp_map['our_sku']
                    # Fetch our catalog item
                    cat_items = await db.search_catalog(x_user_id, our_sku)
                    for res in cat_items:
                        if res['sku'].lower() == our_sku.lower():
                            matches.append(CatalogMatch(
                                catalog_item=Catalog(**res),
                                score=0.95,
                                match_type='competitor_xref'
                            ))
                            seen_ids.add(res['id'])

                # 1b. Direct Search
                sku_results = await db.search_catalog(x_user_id, query_sku)
                for res in sku_results:
                    if res['id'] in seen_ids: continue
                    
                    score = 0.0
                    match_type = 'fuzzy'
                    
                    # Calculate score
                    db_sku = str(res.get('sku', '')).lower()
                    q_sku = query_sku.lower()
                    
                    if db_sku == q_sku:
                        score = 1.0
                        match_type = 'sku_exact'
                    elif q_sku in db_sku:
                        score = 0.8
                        match_type = 'sku_partial'
                    else:
                        score = 0.5
                        
                    matches.append(CatalogMatch(
                        catalog_item=Catalog(**res),
                        score=score,
                        match_type=match_type
                    ))
                    seen_ids.add(res['id'])
            
            # 2. Search by Description (First 3 words)
            if query_desc:
                tokens = [t for t in query_desc.split() if len(t) > 2][:3]
                if tokens:
                    desc_query = " ".join(tokens)
                    desc_results = await db.search_catalog(x_user_id, desc_query)
                    
                    for res in desc_results:
                        if res['id'] in seen_ids: continue
                        
                        # Simple overlap score
                        db_name = str(res.get('item_name', '')).lower()
                        q_desc = query_desc.lower()
                        
                        score = 0.4 # Base score for desc match
                        if db_name in q_desc or q_desc in db_name:
                            score = 0.6
                            match_type = 'name_overlap'
                        else:
                            match_type = 'fuzzy'
                            
                        matches.append(CatalogMatch(
                            catalog_item=Catalog(**res),
                            score=score,
                            match_type=match_type
                        ))
                        seen_ids.add(res['id'])
            
            # 3. Vector Search (Semantic) if top score is low
            top_score = max([m.score for m in matches]) if matches else 0.0
            
            if query_desc and top_score < 0.8:
                try:
                    embedding = await gemini_service.generate_embedding(query_desc)
                    if embedding:
                        vector_results = await db.search_catalog_vector(x_user_id, embedding)
                        for res in vector_results:
                            if res['id'] in seen_ids: continue
                            
                            matches.append(CatalogMatch(
                                catalog_item=Catalog(**res),
                                score=res.get('similarity', 0.7),
                                match_type='semantic'
                            ))
                            seen_ids.add(res['id'])
                except Exception as e:
                    logger.error(f"Vector search failed: {e}")

            # Sort by score descending and take top 5
            matches.sort(key=lambda x: x.score, reverse=True)
            results[idx] = matches[:5]
            
        return SuggestionResponse(suggestions=results)
        
    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
