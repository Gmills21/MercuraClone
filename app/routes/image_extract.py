"""
Image Upload Routes for Camera/OCR functionality
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
import base64

from app.image_extraction_service import image_extraction_service

router = APIRouter(prefix="/image-extract", tags=["image-extraction"])


@router.post("/upload")
async def upload_image_for_extraction(
    file: UploadFile = File(...),
    source: str = Form("camera")  # 'camera', 'gallery', 'upload'
):
    """
    Upload an image (from camera or file) and extract RFQ data.
    
    - **file**: Image file (JPG, PNG)
    - **source**: Where the image came from (camera, gallery, upload)
    
    Returns extracted text and structured RFQ data.
    """
    # Validate file type
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    try:
        # Read image data
        image_data = await file.read()
        
        # Check file size (max 10MB)
        if len(image_data) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large (max 10MB)")
        
        # Extract data from image
        result = await image_extraction_service.extract_from_image(
            image_data, 
            filename=file.filename
        )
        
        return {
            "success": result["success"],
            "source": source,
            "filename": file.filename,
            "extracted_text": result.get("ocr_text", ""),
            "structured_data": result.get("extracted_data"),
            "confidence": result.get("confidence", 0),
            "error": result.get("error")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/base64")
async def upload_base64_image(
    image_base64: str,
    filename: str = "camera-capture.jpg",
    source: str = "camera"
):
    """
    Upload image as base64 string (for direct camera capture from mobile).
    
    - **image_base64**: Base64 encoded image data
    - **filename**: Optional filename
    - **source**: 'camera', 'gallery', etc.
    """
    try:
        # Decode base64
        # Handle data URI format (data:image/jpeg;base64,/9j/4AAQ...)
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        
        image_data = base64.b64decode(image_base64)
        
        # Check size
        if len(image_data) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large (max 10MB)")
        
        # Extract
        result = await image_extraction_service.extract_from_image(image_data, filename)
        
        return {
            "success": result["success"],
            "source": source,
            "extracted_text": result.get("ocr_text", ""),
            "structured_data": result.get("extracted_data"),
            "confidence": result.get("confidence", 0),
            "error": result.get("error")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/create-quote")
async def create_quote_from_image(
    file: UploadFile = File(...),
    customer_id: Optional[str] = Form(None),
    notes: Optional[str] = Form("")
):
    """
    One-step process: Upload image and create a quote.
    Extracts data from image, then creates a draft quote.
    """
    from app.database_sqlite import create_quote
    
    # First extract data
    extract_result = await upload_image_for_extraction(file, source="camera")
    
    if not extract_result["success"]:
        raise HTTPException(status_code=400, detail=extract_result.get("error", "Extraction failed"))
    
    data = extract_result["structured_data"]
    
    # Build line items from extraction
    items = []
    for item in data.get("line_items", []):
        items.append({
            "product_name": item.get("item_name", "Unknown Item"),
            "sku": item.get("sku", ""),
            "quantity": item.get("quantity", 1),
            "unit_price": 0,  # User will fill in
            "total_price": 0,
            "notes": item.get("notes", "")
        })
    
    # Create quote
    quote_data = {
        "customer_id": customer_id,
        "customer_name": data.get("customer_name", "Unknown Customer"),
        "items": items,
        "notes": f"Extracted from image. {notes}\n\nOriginal text:\n{extract_result['extracted_text'][:500]}",
        "status": "draft"
    }
    
    try:
        quote = create_quote(quote_data)
        return {
            "success": True,
            "quote_id": quote["id"],
            "quote": quote,
            "extraction": extract_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quote creation failed: {str(e)}")


@router.get("/status")
async def get_image_extraction_status():
    """Check if image extraction service is available."""
    return {
        "available": True,
        "ocr_engine": "tesseract",
        "ai_enhancement": image_extraction_service.client is not None,
        "supported_formats": ["jpg", "jpeg", "png", "webp"],
        "max_file_size_mb": 10
    }
