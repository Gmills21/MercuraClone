"""
Export API routes.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from app.models import ExportRequest
from app.services.export_service import export_service
from datetime import datetime
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/export", tags=["export"])


@router.post("/csv")
async def export_csv(request: ExportRequest):
    """
    Export line items to CSV file.
    
    Filters:
    - email_ids: List of specific email IDs
    - start_date/end_date: Date range filter
    - include_metadata: Include additional metadata columns
    """
    try:
        filepath = await export_service.export_to_csv(
            email_ids=request.email_ids,
            start_date=request.start_date,
            end_date=request.end_date,
            include_metadata=request.include_metadata
        )
        
        return FileResponse(
            path=filepath,
            media_type='text/csv',
            filename=filepath.split('/')[-1]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/excel")
async def export_excel(request: ExportRequest):
    """
    Export line items to Excel file.
    
    Filters:
    - email_ids: List of specific email IDs
    - start_date/end_date: Date range filter
    - include_metadata: Include additional metadata columns
    """
    try:
        filepath = await export_service.export_to_excel(
            email_ids=request.email_ids,
            start_date=request.start_date,
            end_date=request.end_date,
            include_metadata=request.include_metadata
        )
        
        return FileResponse(
            path=filepath,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=filepath.split('/')[-1]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Excel export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/google-sheets")
async def export_google_sheets(request: ExportRequest):
    """
    Export line items to Google Sheets.
    
    Requires:
    - google_sheet_id: The ID of the Google Sheet to update
    
    Filters:
    - email_ids: List of specific email IDs
    - start_date/end_date: Date range filter
    - include_metadata: Include additional metadata columns
    """
    try:
        if not request.google_sheet_id:
            raise HTTPException(
                status_code=400,
                detail="google_sheet_id is required for Google Sheets export"
            )
        
        result = await export_service.export_to_google_sheets(
            sheet_id=request.google_sheet_id,
            email_ids=request.email_ids,
            start_date=request.start_date,
            end_date=request.end_date,
            include_metadata=request.include_metadata
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Google Sheets export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_export_history(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0)
):
    """Get export history (placeholder for future implementation)."""
    return {
        "exports": [],
        "total": 0,
        "limit": limit,
        "offset": offset
    }
