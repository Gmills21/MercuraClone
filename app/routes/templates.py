"""
Industry Templates API routes.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List

from app.industry_templates import list_templates, get_template, apply_template
from app.auth import get_current_user, User, check_permission

router = APIRouter(prefix="/templates", tags=["templates"])


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str


class TemplateApplyRequest(BaseModel):
    template_id: str


class TemplateApplyResponse(BaseModel):
    success: bool
    template: str
    created: int
    skipped: int
    tax_rate: float
    currency: str


@router.get("/", response_model=List[TemplateResponse])
async def get_templates(current_user: User = Depends(get_current_user)):
    """List all available industry templates."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    templates = list_templates()
    return [TemplateResponse(**t) for t in templates]


@router.get("/{template_id}")
async def get_template_details(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a template."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    template = get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "category": template.category,
        "tax_rate": template.tax_rate,
        "currency": template.currency,
        "products_count": len(template.default_products),
        "sample_products": template.default_products[:5]
    }


@router.post("/apply", response_model=TemplateApplyResponse)
async def apply_industry_template(
    request: TemplateApplyRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Apply an industry template to create default products.
    Requires admin or manager role.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if not check_permission(current_user, "manager"):
        raise HTTPException(status_code=403, detail="Requires manager or admin role")
    
    result = apply_template(request.template_id, current_user.id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return TemplateApplyResponse(**result)
