"""
CSV Import API Routes
Drag-and-drop import for products, customers, and competitor mappings.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from app.services.csv_import_service import import_service
from app.middleware.organization import get_current_user_and_org
from app.posthog_utils import capture_event

router = APIRouter(prefix="/import", tags=["import"])


class ImportPreviewResponse(BaseModel):
    """Import preview response."""
    success: bool
    headers: List[str]
    detected_columns: Dict[str, str]
    sample_rows: List[Dict[str, Any]]
    total_rows: int
    validation_issues: List[str]
    ready_to_import: bool
    error: Optional[str] = None


class ImportRequest(BaseModel):
    """Import execution request."""
    column_mapping: Optional[Dict[str, str]] = None
    skip_first_row: bool = True  # Header row


class ImportResponse(BaseModel):
    """Import execution response."""
    success: bool
    imported_count: int
    failed_count: int
    errors: List[str]
    warnings: List[str]


@router.post("/preview/{import_type}", response_model=ImportPreviewResponse)
async def preview_import(
    import_type: str,  # products, customers, competitors
    file: UploadFile = File(...),
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Preview a CSV import before actually importing.
    
    Shows:
    - Detected columns
    - Sample rows
    - Validation issues
    - Total row count
    
    Use this to verify the import will work before committing.
    """
    user_id, org_id = user_org
    
    # Validate file type
    filename = file.filename or ""
    if not any(filename.lower().endswith(ext) for ext in ['.csv', '.txt', '.tsv']):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files supported for preview. Use .csv, .txt, or .tsv"
        )
    
    try:
        content = await file.read()
        result = import_service.preview_import(content, import_type)
        
        capture_event(
            distinct_id=user_id,
            event_name="import_preview",
            properties={
                "import_type": import_type,
                "success": result.get("success"),
                "total_rows": result.get("total_rows", 0),
                "organization_id": org_id
            }
        )
        
        return ImportPreviewResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products", response_model=ImportResponse)
async def import_products(
    file: UploadFile = File(...),
    column_mapping: Optional[Dict[str, str]] = Body(None),
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Import products from CSV file.
    
    Auto-detects columns for:
    - SKU (sku, part_number, item_code)
    - Name (name, product_name, description)
    - Price (price, cost, unit_price)
    - Category, Manufacturer, etc.
    
    Example CSV:
    ```
    SKU,Name,Price,Category
    ABC-123,Widget Pro,99.99,Widgets
    XYZ-456,Gadget Max,149.99,Gadgets
    ```
    """
    user_id, org_id = user_org
    
    try:
        content = await file.read()
        result = import_service.import_products(content, org_id, column_mapping)
        
        capture_event(
            distinct_id=user_id,
            event_name="products_imported",
            properties={
                "imported_count": result.imported_count,
                "failed_count": result.failed_count,
                "organization_id": org_id
            }
        )
        
        return ImportResponse(
            success=result.success,
            imported_count=result.imported_count,
            failed_count=result.failed_count,
            errors=result.errors,
            warnings=result.warnings
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customers", response_model=ImportResponse)
async def import_customers(
    file: UploadFile = File(...),
    column_mapping: Optional[Dict[str, str]] = Body(None),
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Import customers from CSV file.
    
    Auto-detects columns for:
    - Name (name, company_name, organization)
    - Email (email, contact_email)
    - Phone (phone, telephone)
    - Address fields
    
    Example CSV:
    ```
    Name,Email,Phone,Address
    Acme Corp,contact@acme.com,555-1234,123 Main St
    Tech Inc,sales@tech.com,555-5678,456 Oak Ave
    ```
    """
    user_id, org_id = user_org
    
    try:
        content = await file.read()
        result = import_service.import_customers(content, org_id, column_mapping)
        
        capture_event(
            distinct_id=user_id,
            event_name="customers_imported",
            properties={
                "imported_count": result.imported_count,
                "failed_count": result.failed_count,
                "organization_id": org_id
            }
        )
        
        return ImportResponse(
            success=result.success,
            imported_count=result.imported_count,
            failed_count=result.failed_count,
            errors=result.errors,
            warnings=result.warnings
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_type}")
async def download_template(template_type: str):
    """
    Download a CSV template for importing.
    
    Templates available:
    - products: Product catalog template
    - customers: Customer list template
    - competitors: Competitor SKU mapping template
    """
    import csv
    from io import StringIO
    from fastapi.responses import StreamingResponse
    
    if template_type == "products":
        headers = ["sku", "name", "description", "price", "cost_price", "category", "manufacturer"]
        sample = [
            ["ABC-123", "Widget Pro", "Professional grade widget", "99.99", "60.00", "Widgets", "Acme Mfg"],
            ["XYZ-456", "Gadget Max", "Maximum performance gadget", "149.99", "90.00", "Gadgets", "TechCorp"]
        ]
        filename = "products_template.csv"
        
    elif template_type == "customers":
        headers = ["name", "email", "phone", "address", "city", "state", "zip"]
        sample = [
            ["Acme Corporation", "contact@acme.com", "555-123-4567", "123 Main St", "Springfield", "IL", "62701"],
            ["Tech Industries", "sales@techind.com", "555-987-6543", "456 Oak Avenue", "Madison", "WI", "53703"]
        ]
        filename = "customers_template.csv"
        
    elif template_type == "competitors":
        headers = ["your_sku", "competitor_sku", "competitor_name", "confidence"]
        sample = [
            ["ABC-123", "COMP-456", "CompetitorCo", "0.95"],
            ["XYZ-789", "RIVAL-321", "RivalBrand", "0.88"]
        ]
        filename = "competitor_mapping_template.csv"
        
    else:
        raise HTTPException(status_code=400, detail=f"Unknown template type: {template_type}")
    
    # Generate CSV
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(sample)
    
    return StreamingResponse(
        iter([output.getvalue().encode()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/status")
async def import_status():
    """Check import service status."""
    return {
        "available": True,
        "supported_types": ["products", "customers", "competitors"],
        "max_rows": import_service.max_import_rows,
        "features": [
            "auto_column_detection",
            "preview_before_import",
            "error_reporting",
            "template_downloads"
        ]
    }
