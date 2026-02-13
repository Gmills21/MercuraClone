from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from typing import Optional, Dict, Any
import os
import uuid
from datetime import datetime

from app.services.extraction_engine import extraction_engine
from app.database_sqlite import save_extraction, get_extraction
from app.middleware.organization import get_current_user_and_org

router = APIRouter(prefix="/extract", tags=["extraction"])


@router.post("/")
async def extract_rfq(
    text: Optional[str] = Form(None),
    source_type: str = Form("unknown"),
    file: Optional[UploadFile] = File(None),
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Universal RFQ extraction endpoint.
    
    Accepts text, images, PDFs, and Excel files.
    """
    user_id, org_id = user_org
    
    # Handle file upload
    if file:
        # Validate file type
        allowed_extensions = [
            '.jpg', '.jpeg', '.png', '.webp', 
            '.pdf', '.xlsx', '.xls', '.csv',
            '.docx', '.pptx', '.html', '.htm', '.txt', '.md'
        ]
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Check file size (20MB max for documents)
        file_data = await file.read()
        if len(file_data) > 20 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 20MB)")
        
        # Universal extraction (handles image, pdf, xlsx)
        result = await extraction_engine.extract(
            file_data=file_data, 
            filename=file.filename,
            source_type=source_type
        )
    
    # Handle text extraction
    elif text:
        result = await extraction_engine.extract_from_text(text, source_type)
    
    else:
        raise HTTPException(status_code=400, detail="Provide either 'text' or 'file'")

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Extraction failed"))

    # Save extraction to database for history/analytics
    extraction_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    # Map structured data to the shared data format
    structured_data = result.get("structured_data", {})
    
    extraction_data = {
        "id": extraction_id,
        "organization_id": org_id,
        "source_type": source_type if not file else f"file:{file_ext[1:]}",
        "source_content": text[:1000] if text else f"File: {file.filename}",
        "parsed_data": structured_data,
        "confidence_score": result.get("confidence", 0.5),
        "status": "completed",
        "created_at": now
    }
    
    save_extraction(extraction_data)
    
    # Add extraction_id to response
    result["id"] = extraction_id
    return result


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
        for idx, item in enumerate(data.get("line_items", [])):
            item_data = {
                "id": str(uuid.uuid4()),
                "quote_id": quote_id,
                "product_id": None,
                "product_name": item.get("item_name", "Unknown Item"),
                "sku": item.get("sku", ""),
                "description": item.get("item_name", ""),  # Use item_name as description
                "quantity": item.get("quantity", 1),
                "unit_price": 0,
                "total_price": 0,
                "competitor_sku": None,
                "metadata": {
                    "original_extraction": {
                        "item_name": item.get("item_name"),
                        "quantity": item.get("quantity"),
                        "sku": item.get("sku"),
                        "confidence_score": item.get("extraction_confidence", 0.7)
                    },
                    "source_location": item.get("source_location"),
                    "extraction_method": extract_result.get("extraction_method"),
                    "item_index": idx
                }
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


@router.get("/{extraction_id}/visualize")
async def visualize_extraction(
    extraction_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get interactive HTML visualization for an extraction.
    """
    user_id, org_id = user_org
    extraction = get_extraction(extraction_id, org_id)
    
    if not extraction:
        raise HTTPException(status_code=404, detail="Extraction not found")
        
    html = extraction["parsed_data"].get("visualization_html")
    if not html:
        return HTMLResponse(content="<html><body><h1>No visualization available</h1></body></html>")
        
    return HTMLResponse(content=html)


@router.get("/{extraction_id}")
async def get_extraction_details(
    extraction_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get full extraction details including parsed data.
    """
    user_id, org_id = user_org
    extraction = get_extraction(extraction_id, org_id)
    
    if not extraction:
        raise HTTPException(status_code=404, detail="Extraction not found")
        
    return extraction


@router.get("/status")
async def get_extraction_status():
    """Check if extraction services are available."""
    # Check if AI service is configured
    ai_status = False
    try:
        if extraction_engine.ai_service:
            ai_status = True
    except:
        pass
        
    return {
        "available": True,
        "ai_available": ai_status,
        "ocr_available": True,
        "supported_sources": ["text", "email", "image", "document", "spreadsheet"]
    }
