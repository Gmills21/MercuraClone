"""
Custom Domain Middleware
Detects custom domains and sets organization context.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.services.custom_domain_service import custom_domain_service
from app.config import settings


class CustomDomainMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle custom domain routing.
    
    When a request comes in with a custom domain (not the main app domain),
    this middleware resolves the organization and sets it in the request state.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.app_domain = self._extract_app_domain()
    
    def _extract_app_domain(self) -> str:
        """Extract the main app domain from app_url config."""
        from urllib.parse import urlparse
        parsed = urlparse(settings.app_url)
        return parsed.netloc or 'openmercura.com'
    
    async def dispatch(self, request: Request, call_next):
        # Get the host from the request
        host = request.headers.get('host', '')
        
        # Skip if no host or if it's the app domain
        if not host or host == self.app_domain or host.endswith(f'.{self.app_domain}'):
            request.state.custom_domain_org = None
            return await call_next(request)
        
        # Remove port if present
        host = host.split(':')[0]
        
        # Try to resolve the organization
        org = custom_domain_service.resolve_organization_by_domain(host)
        
        if org:
            # Set the organization in request state
            request.state.custom_domain_org = org
            # Also set a header for downstream use
            request.headers.__dict__['x-organization-id'] = org['id']
        else:
            request.state.custom_domain_org = None
        
        return await call_next(request)


def get_custom_domain_org(request: Request) -> dict | None:
    """
    Get the organization resolved from custom domain (if any).
    
    Use this in routes to check if the request came via custom domain.
    """
    return getattr(request.state, 'custom_domain_org', None)
