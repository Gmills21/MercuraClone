"""
Custom Domain API Routes
Manage custom domains for white-label organization access.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional
from pydantic import BaseModel, Field

from app.services.custom_domain_service import custom_domain_service
from app.middleware.organization import get_current_user_and_org
from app.middleware.custom_domain import get_custom_domain_org

router = APIRouter(prefix="/custom-domains", tags=["custom-domains"])


class RegisterDomainRequest(BaseModel):
    domain: str = Field(..., description="Custom domain to register (e.g., crm.yourcompany.com)")


class DomainResponse(BaseModel):
    success: bool
    domain: Optional[dict] = None
    dns_records: Optional[list] = None
    instructions: Optional[str] = None
    error: Optional[str] = None


@router.get("/status")
async def get_domain_status(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Get the custom domain status for the current organization.
    """
    user_id, org_id = user_org
    
    status = custom_domain_service.get_domain_status(org_id)
    
    if not status:
        return {
            "has_custom_domain": False,
            "message": "No custom domain configured"
        }
    
    return {
        "has_custom_domain": True,
        **status
    }


@router.post("/register", response_model=DomainResponse)
async def register_domain(
    request: RegisterDomainRequest,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Register a new custom domain for the organization.
    
    This will generate DNS records that need to be configured.
    """
    user_id, org_id = user_org
    
    result = custom_domain_service.register_domain(org_id, request.domain)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return DomainResponse(**result)


@router.post("/verify")
async def verify_domain(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Verify the custom domain DNS configuration.
    
    Checks if the verification TXT record is correctly configured.
    """
    user_id, org_id = user_org
    
    result = custom_domain_service.verify_domain(org_id)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    
    return result


@router.post("/remove")
async def remove_domain(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """
    Remove the custom domain from the organization.
    """
    user_id, org_id = user_org
    
    result = custom_domain_service.remove_domain(org_id)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result


@router.get("/check-availability")
async def check_domain_availability(
    domain: str
):
    """
    Check if a domain is available for registration.
    
    This is a public endpoint - no authentication required.
    """
    is_available, error = custom_domain_service.check_domain_available(domain)
    
    return {
        "domain": domain,
        "available": is_available,
        "error": error if not is_available else None
    }


@router.get("/resolve")
async def resolve_domain(
    request: Request
):
    """
    Debug endpoint to check what organization (if any) is resolved
    from the current request's Host header.
    """
    org = get_custom_domain_org(request)
    host = request.headers.get('host', '')
    
    if org:
        return {
            "resolved": True,
            "host": host,
            "organization": {
                "id": org['id'],
                "name": org['name'],
                "slug": org['slug']
            }
        }
    else:
        return {
            "resolved": False,
            "host": host,
            "message": "No custom domain organization resolved"
        }
