"""
PDF Generation API Routes
Generate and download professional PDF quotes.
"""

from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
from typing import Optional

from app.services.pdf_service import pdf_service, PDFConfig
from app.middleware.organization import get_current_user_and_org
from app.posthog_utils import capture_event

router = APIRouter(prefix="/pdf", tags=["pdf"])


@router.get("/quote/{quote_id}")
async def download_quote_pdf(
    quote_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Download a quote as a professional PDF.
    
    The PDF includes:
    - Company branding (logo, colors)
    - Customer information
    - Line items with descriptions
    - Pricing breakdown (subtotal, tax, total)
    - Terms and conditions
    """
    user_id, org_id = user_org
    
    if not pdf_service:
        raise HTTPException(
            status_code=503,
            detail="PDF generation not available. Install reportlab: pip install reportlab"
        )
    
    try:
        # Generate PDF
        pdf_bytes = pdf_service.generate_quote_pdf(
            quote_id=quote_id,
            organization_id=org_id
        )
        
        # Track download
        capture_event(
            distinct_id=user_id,
            event_name="quote_pdf_downloaded",
            properties={
                "quote_id": quote_id,
                "organization_id": org_id
            }
        )
        
        # Return as download
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="quote_{quote_id}.pdf"'
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/quote/{quote_id}/preview")
async def preview_quote_pdf(
    quote_id: str,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Preview a quote PDF in the browser (inline display).
    """
    user_id, org_id = user_org
    
    if not pdf_service:
        raise HTTPException(
            status_code=503,
            detail="PDF generation not available"
        )
    
    try:
        pdf_bytes = pdf_service.generate_quote_pdf(
            quote_id=quote_id,
            organization_id=org_id
        )
        
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="quote_{quote_id}.pdf"'
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/status")
async def pdf_status():
    """Check PDF generation service status."""
    return {
        "available": pdf_service is not None,
        "service": "reportlab",
        "features": [
            "branded_quotes",
            "line_items_table",
            "tax_calculations",
            "terms_conditions"
        ]
    }
