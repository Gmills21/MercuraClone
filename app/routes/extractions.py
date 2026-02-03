"""
Extractions API routes - Intelligent Data Capture (Free CRM).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.database_sqlite import save_extraction, list_extractions
from app.services.extraction_engine import extraction_engine

router = APIRouter(prefix="/extractions", tags=["extractions"])


class ExtractionRequest(BaseModel):
    text: str
    source_type: str = "text"  # text, csv, email


class ExtractionResponse(BaseModel):
    id: str
    source_type: str
    parsed_data: Dict[str, Any]
    confidence_score: float
    status: str
    created_at: str


@router.post("/parse", response_model=ExtractionResponse)
async def parse_text(request: ExtractionRequest):
    """
    Parse unstructured text into structured data.
    Uses unified extraction engine with DeepSeek AI.
    """
    # Use the new unified extraction engine
    result = await extraction_engine.extract_from_text(request.text, request.source_type)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Parsing failed"))
    
    now = datetime.utcnow().isoformat()
    extraction_id = str(uuid.uuid4())
    
    # Map new extraction format to old response format for compatibility
    structured_data = result.get("structured_data", {})
    parsed_data = {
        "line_items": structured_data.get("line_items", []),
        "document_type": request.source_type,
        "vendor": structured_data.get("customer_name"),
        "date": structured_data.get("delivery_date"),
        "total_amount": None,
        "currency": "USD",
        "contact_email": structured_data.get("contact_email"),
        "contact_phone": structured_data.get("contact_phone"),
        "delivery_location": structured_data.get("delivery_location"),
        "special_instructions": structured_data.get("special_instructions"),
    }
    
    extraction_data = {
        "id": extraction_id,
        "source_type": request.source_type,
        "source_content": request.text[:1000],  # Store preview
        "parsed_data": parsed_data,
        "confidence_score": result.get("confidence", 0.5),
        "status": "completed",
        "created_at": now
    }
    
    save_extraction(extraction_data)
    
    return ExtractionResponse(
        id=extraction_id,
        source_type=request.source_type,
        parsed_data=parsed_data,
        confidence_score=result.get("confidence", 0.5),
        status="completed",
        created_at=now
    )


@router.get("/", response_model=List[ExtractionResponse])
async def list_extractions_endpoint(status: Optional[str] = None):
    """List all extractions."""
    extractions = list_extractions(status)
    return [
        ExtractionResponse(
            id=e["id"],
            source_type=e["source_type"],
            parsed_data=e["parsed_data"],
            confidence_score=e.get("confidence_score", 0),
            status=e["status"],
            created_at=e["created_at"]
        )
        for e in extractions
    ]


@router.post("/csv/upload")
async def upload_csv(file: bytes):
    """Upload and parse CSV data."""
    import csv
    import io
    
    try:
        content = file.decode('utf-8')
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        
        extraction_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        extraction_data = {
            "id": extraction_id,
            "source_type": "csv",
            "source_content": f"CSV with {len(rows)} rows",
            "parsed_data": {"rows": rows},
            "confidence_score": 1.0,
            "status": "completed",
            "created_at": now
        }
        
        save_extraction(extraction_data)
        
        return {
            "id": extraction_id,
            "row_count": len(rows),
            "status": "completed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {e}")
