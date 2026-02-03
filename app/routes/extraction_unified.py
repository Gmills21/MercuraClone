"""
Unified Extraction Routes
Single endpoint for all extraction (text, image, email)
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional

from app.services.extraction_engine import extraction_engine

router = APIRouter(prefix="/extract", tags=["extraction"])


@router.post("/")
async def extract_rfq(
    text: Optional[str] = Form(None),
    source_type: str = Form("unknown"),
    file: Optional[UploadFile] = File(None)
):
    """
    Universal RFQ extraction endpoint.
    
    Accepts either:
    - text: Raw text to parse
    - file: Image to OCR and parse
    
    Returns consistent structured data regardless of source.
    """
    # Handle image upload
    if file:
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
            )
        
        # Check file size (10MB max)
        image_data = await file.read()
        if len(image_data) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large (max 10MB)")
        
        # Extract from image
        result = await extraction_engine.extract_from_image(image_data, file.filename)
        return result
    
    # Handle text extraction
    elif text:
        result = await extraction_engine.extract_from_text(text, source_type)
        return result
    
    else:
        raise HTTPException(status_code=400, detail="Provide either 'text' or 'file'")


@router.post("/create-quote")
async def extract_and_create_quote(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    customer_id: Optional[str] = Form(None),
    source_type: str = Form("unknown")
):
    """
    One-step extraction and quote creation.
    
    Extracts RFQ data and immediately creates a draft quote.
    """
    from app.database_sqlite import create_quote
    
    # Extract data
    if file:
        extract_result = await extraction_engine.extract_from_image(
            await file.read(), 
            file.filename
        )
    elif text:
        extract_result = await extraction_engine.extract_from_text(text, source_type)
    else:
        raise HTTPException(status_code=400, detail="Provide text or file")
    
    if not extract_result["success"]:
        raise HTTPException(status_code=400, detail=extract_result.get("error", "Extraction failed"))
    
    data = extract_result["structured_data"]
    
    # Generate IDs
    import uuid
    from datetime import datetime
    
    quote_id = str(uuid.uuid4())
    
    # Create quote data for database
    quote_data = {
        "id": quote_id,
        "customer_id": customer_id,
        "status": "draft",
        "subtotal": 0,
        "tax_rate": 0,
        "tax_amount": 0,
        "total": 0,
        "notes": f"Extracted via {extract_result['extraction_method']}. Customer: {data.get('customer_name', 'Unknown')}",
        "token": str(uuid.uuid4())[:8],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "expires_at": None
    }
    
    try:
        # Create the quote first
        quote = create_quote(quote_data)
        if not quote:
            raise HTTPException(status_code=500, detail="Quote creation returned None")
        
        # Add line items
        from app.database_sqlite import add_quote_item
        for item in data.get("line_items", []):
            item_data = {
                "id": str(uuid.uuid4()),
                "quote_id": quote_id,
                "product_id": None,
                "product_name": item.get("item_name", "Unknown Item"),
                "sku": item.get("sku", ""),
                "description": item.get("notes", ""),
                "quantity": item.get("quantity", 1),
                "unit_price": 0,
                "total_price": 0,
                "competitor_sku": None
            }
            add_quote_item(item_data)
        
        # Refresh quote with items
        from app.database_sqlite import get_quote_with_items
        quote = get_quote_with_items(quote_id)
        
        return {
            "success": True,
            "quote_id": quote["id"],
            "quote": quote,
            "extraction": extract_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quote creation failed: {str(e)}")


@router.get("/status")
async def get_extraction_status():
    """Check if extraction services are available."""
    return {
        "available": True,
        "ai_available": extraction_engine.client is not None,
        "ocr_available": True,  # Tesseract
        "supported_sources": ["text", "email", "image", "document"]
    }
