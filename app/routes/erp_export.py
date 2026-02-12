"""
ERP Export API routes.
CSV exports for SAP, NetSuite, QuickBooks, and generic ERP systems.
"""

from fastapi import APIRouter, HTTPException, Response, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.posthog_utils import capture_event
from app.config import settings

from app.erp_export import get_erp_exporter
from app.services.n8n_service import n8n_service

router = APIRouter(prefix="/export", tags=["erp-export"])


class ExportQuoteRequest(BaseModel):
    quote_id: str
    format: str = "generic"  # sap, netsuite, quickbooks, generic


class ExportBatchRequest(BaseModel):
    quote_ids: List[str]
    format: str = "generic"


@router.get("/quote/{quote_id}")
async def export_single_quote(
    quote_id: str,
    format: str = "generic",
):
    """
    Export a single quote to ERP-compatible CSV format.
    
    Formats:
    - sap: SAP ERP format
    - netsuite: NetSuite format
    - quickbooks: QuickBooks format
    - generic: Universal format (works with any ERP)
    """
    
    valid_formats = ["sap", "netsuite", "quickbooks", "gaeb", "generic"]
    if format not in valid_formats:
        raise HTTPException(status_code=400, detail=f"Invalid format. Use: {valid_formats}")
    
    exporter = get_erp_exporter()
    result = exporter.export_quote(quote_id, format)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    # Handle GAEB XML export
    if format == "gaeb":
        xml_content = result.get("content", "")
        filename = f"quote_{quote_id}.x83" # Standard GAEB XML extension
        
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    # Convert to CSV
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=result.keys())
    writer.writeheader()
    writer.writerow(result)
    
    filename = f"quote_{quote_id}_{format}.csv"
    
    # Filter valid keys for metadata
    tracking_metadata = {k: v for k, v in result.items() if isinstance(v, (str, int, float, bool))}
    capture_event(
        distinct_id="anonymous", # Should ideally be the current user
        event_name="send_to_erp",
        properties={
            "quote_id": quote_id,
            "format": format,
            "success": True,
            **tracking_metadata
        }
    )
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )



@router.post("/quote/{quote_id}/send")
async def send_quote_to_erp_webhook(
    quote_id: str,
    format: str = "generic",
):
    """
    Send a single quote to the configured n8n webhook (Legacy Bridge).
    """
    if not settings.n8n_enabled:
        raise HTTPException(status_code=503, detail="n8n integration is disabled")
    
    exporter = get_erp_exporter()
    result = exporter.export_quote(quote_id, format)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    # Send to n8n
    success = await n8n_service.trigger_webhook(
        event_type="erp_export",
        payload={
            "quote_id": quote_id,
            "format": format,
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    if not success:
        raise HTTPException(status_code=502, detail="Failed to send to n8n webhook")
            
    capture_event(
        distinct_id="anonymous",
        event_name="send_to_n8n",
        properties={
            "quote_id": quote_id,
            "format": format,
            "success": True
        }
    )
    
    return {"status": "success", "message": "Quote sent to ERP via n8n"}


@router.post("/quote/batch")
async def export_quotes_batch(
    request: ExportBatchRequest,
):
    """
    Export multiple quotes to CSV.
    """
    
    valid_formats = ["sap", "netsuite", "quickbooks", "generic"]
    if request.format not in valid_formats:
        raise HTTPException(status_code=400, detail=f"Invalid format. Use: {valid_formats}")
    
    exporter = get_erp_exporter()
    csv_content = exporter.export_quotes_batch(request.quote_ids, request.format)
    
    filename = f"quotes_batch_{request.format}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/quote/{quote_id}/line-items")
async def export_line_items(
    quote_id: str,
    format: str = "generic",
):
    """
    Export all line items from a quote as separate rows.
    Best for ERPs that need one row per item.
    """
    
    exporter = get_erp_exporter()
    csv_content = exporter.export_all_line_items(quote_id, format)
    
    if csv_content.startswith("error:"):
        raise HTTPException(status_code=404, detail=csv_content.replace("error: ", ""))
    
    filename = f"quote_{quote_id}_line_items_{format}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/formats")
async def list_export_formats():
    """
    List all supported ERP export formats.
    """
    return {
        "formats": [
            {
                "id": "sap",
                "name": "SAP ERP",
                "description": "Format for SAP S/4HANA and SAP ECC",
                "documentation": "https://help.sap.com/docs/SAP_S4HANA_ON-PREMISE/"
            },
            {
                "id": "netsuite",
                "name": "NetSuite",
                "description": "Oracle NetSuite CSV import format",
                "documentation": "https://docs.oracle.com/en/cloud/saas/netsuite/"
            },
            {
                "id": "quickbooks",
                "name": "QuickBooks",
                "description": "QuickBooks Online/Desktop import format",
                "documentation": "https://quickbooks.intuit.com/learn-support/"
            },
            {
                "id": "generic",
                "name": "Universal/Generic",
                "description": "Standard CSV format compatible with most ERPs",
                "documentation": "Use this if your ERP is not listed above"
            }
        ],
        "note": "All exports are CSV format. Import using your ERP's standard CSV import tool."
    }


@router.get("/instructions/{format_id}")
async def get_import_instructions(format_id: str):
    """
    Get step-by-step instructions for importing into specific ERP.
    """
    instructions = {
        "sap": {
            "erp_name": "SAP ERP",
            "steps": [
                "Download the CSV file from OpenMercura",
                "Open SAP GUI and navigate to VA21 (Create Quotation)",
                "Or use transaction LSMW for bulk import",
                "Map CSV fields to SAP structure",
                "Execute import and verify quotations in VA22"
            ],
            "transaction_codes": ["VA21", "VA22", "LSMW"],
            "file_format": "CSV with semicolon delimiter",
            "encoding": "UTF-8"
        },
        "netsuite": {
            "erp_name": "Oracle NetSuite",
            "steps": [
                "Download the CSV file from OpenMercura",
                "Go to Setup > Import/Export > Import CSV Records",
                "Select Record Type: 'Estimate' (Quote)",
                "Upload the CSV file",
                "Map fields using NetSuite's import assistant",
                "Review and run the import"
            ],
            "import_type": "CSV Import",
            "record_type": "Estimate",
            "encoding": "UTF-8"
        },
        "quickbooks": {
            "erp_name": "QuickBooks Online/Desktop",
            "steps": [
                "Download the CSV file from OpenMercura",
                "In QBO: Go to Settings > Import Data",
                "Select 'Estimates' or 'Invoices'",
                "Upload the CSV file",
                "Match columns to QuickBooks fields",
                "Review and complete import"
            ],
            "supported_versions": ["QuickBooks Online", "QuickBooks Desktop 2020+"],
            "file_type": "CSV"
        },
        "generic": {
            "erp_name": "Universal ERP",
            "steps": [
                "Download the CSV file from OpenMercura",
                "Open your ERP's import tool (usually under Tools > Import)",
                "Select CSV as source format",
                "Map columns to your ERP's fields",
                "Preview and execute import"
            ],
            "tips": [
                "Most ERPs accept CSV with comma delimiter",
                "Date format is ISO 8601 (YYYY-MM-DD)",
                "Currency is USD by default",
                "Amounts use decimal point (not comma)"
            ]
        }
    }
    
    if format_id not in instructions:
        raise HTTPException(status_code=404, detail="Format not found")
    
    return instructions[format_id]
