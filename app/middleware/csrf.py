"""
CSRF Protection Middleware for FastAPI.
Generates and validates CSRF tokens for state-changing operations.
"""

import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import os


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware.
    
    - Generates CSRF tokens for authenticated users
    - Validates tokens on state-changing operations (POST, PUT, PATCH, DELETE)
    - Exempts safe methods (GET, HEAD, OPTIONS)
    - Exempts specific paths (webhooks, public endpoints)
    """
    
    def __init__(
        self,
        app: ASGIApp,
        secret_key: Optional[str] = None,
        cookie_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        exempt_paths: Optional[list] = None,
        token_expiry_hours: int = 24
    ):
        super().__init__(app)
        self.secret_key = secret_key or os.getenv("CSRF_SECRET_KEY") or os.getenv("JWT_SECRET_KEY") or "dev-secret-key-change-in-production"
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.exempt_paths = exempt_paths or [
            "/auth/login",
            "/auth/register",
            "/auth/logout",
            "/webhooks/",
            "/quotes/token/",  # Public quote access
            "/quotes/public/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/monitoring/",
            "/health",
        ]
        self.token_expiry_hours = token_expiry_hours
        
    def _generate_token(self, session_id: str) -> str:
        """Generate a CSRF token for the session."""
        timestamp = datetime.utcnow().isoformat()
        data = f"{session_id}:{timestamp}"
        token = hmac.new(
            self.secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()[:32]
        return f"{token}:{timestamp}"
    
    def _validate_token(self, token: str, session_id: str) -> bool:
        """Validate a CSRF token."""
        if not token or ":" not in token:
            return False
            
        try:
            token_hash, timestamp_str = token.rsplit(":", 1)
            timestamp = datetime.fromisoformat(timestamp_str)
            
            # Check expiry
            if datetime.utcnow() - timestamp > timedelta(hours=self.token_expiry_hours):
                return False
            
            # Regenerate expected token
            data = f"{session_id}:{timestamp_str}"
            expected = hmac.new(
                self.secret_key.encode(),
                data.encode(),
                hashlib.sha256
            ).hexdigest()[:32]
            
            return hmac.compare_digest(token_hash, expected)
        except Exception:
            return False
    
    def _is_exempt(self, request: Request) -> bool:
        """Check if request is exempt from CSRF validation."""
        path = request.url.path
        
        # Check exempt paths
        for exempt in self.exempt_paths:
            if path.startswith(exempt):
                return True
        
        # Safe methods don't require CSRF
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
            
        return False
    
    def _get_session_id(self, request: Request) -> str:
        """Get or create session identifier from request."""
        # Use authorization token as session identifier
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]  # Return token as session ID
        
        # Fall back to IP + User-Agent (for non-authenticated but still protected requests)
        ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "")
        return hashlib.sha256(f"{ip}:{user_agent}".encode()).hexdigest()[:32]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip CSRF for exempt requests
        if self._is_exempt(request):
            response = await call_next(request)
            
            # Still set CSRF cookie for GET requests to provide token for subsequent requests
            if request.method == "GET" and not any(request.url.path.startswith(p) for p in ["/docs", "/redoc", "/openapi"]):
                session_id = self._get_session_id(request)
                token = self._generate_token(session_id)
                response.set_cookie(
                    self.cookie_name,
                    token,
                    httponly=False,  # Must be accessible by JavaScript
                    secure=os.getenv("APP_ENV") == "production",
                    samesite="lax",
                    max_age=86400,  # 24 hours
                    path="/"
                )
            
            return response
        
        # Validate CSRF token for state-changing operations
        session_id = self._get_session_id(request)
        
        # Get token from header (preferred) or cookie
        header_token = request.headers.get(self.header_name, "")
        cookie_token = request.cookies.get(self.cookie_name, "")
        
        token = header_token or cookie_token
        
        if not token:
            return Response(
                content='{"detail": "CSRF token missing. Please refresh the page and try again."}',
                status_code=403,
                media_type="application/json"
            )
        
        if not self._validate_token(token, session_id):
            return Response(
                content='{"detail": "CSRF token invalid or expired. Please refresh the page and try again."}',
                status_code=403,
                media_type="application/json"
            )
        
        # Token is valid, proceed
        response = await call_next(request)
        return response


def get_csrf_token(request: Request) -> Optional[str]:
    """Helper function to get CSRF token from request."""
    return request.cookies.get("csrf_token") or request.headers.get("X-CSRF-Token")
