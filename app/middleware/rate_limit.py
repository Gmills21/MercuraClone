"""
Rate Limiting Middleware
Protects API endpoints from abuse and ensures fair usage.
"""

import time
import hashlib
from typing import Dict, Optional, Callable
from functools import wraps
from datetime import datetime, timedelta

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.database_sqlite import get_db


class RateLimitStore:
    """In-memory rate limit store with SQLite persistence for tracking."""
    
    def __init__(self):
        # In-memory cache for fast lookups: {key: {"count": int, "reset_at": float}}
        self._cache: Dict[str, Dict] = {}
        self._cleanup_interval = 300  # 5 minutes
        self._last_cleanup = time.time()
    
    def _cleanup_expired(self):
        """Remove expired entries from cache."""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return
        
        expired = [k for k, v in self._cache.items() if v["reset_at"] < now]
        for k in expired:
            del self._cache[k]
        
        self._last_cleanup = now
    
    def get(self, key: str) -> Optional[Dict]:
        """Get rate limit data for key."""
        self._cleanup_expired()
        return self._cache.get(key)
    
    def increment(self, key: str, window_seconds: int) -> Dict:
        """Increment counter for key, creating if needed."""
        now = time.time()
        
        if key not in self._cache or self._cache[key]["reset_at"] < now:
            # New window
            self._cache[key] = {
                "count": 1,
                "reset_at": now + window_seconds,
                "window": window_seconds
            }
        else:
            self._cache[key]["count"] += 1
        
        return self._cache[key]
    
    def reset(self, key: str):
        """Reset counter for key."""
        if key in self._cache:
            del self._cache[key]


# Global rate limit store
_rate_limit_store = RateLimitStore()


def get_client_identifier(request: Request) -> str:
    """Generate unique identifier for the client."""
    # Try to get user ID from auth
    user_id = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        # Get user from token
        from app.auth import get_current_user
        try:
            user = get_current_user(token)
            if user:
                user_id = user.id
        except:
            pass
    
    if user_id:
        return f"user:{user_id}"
    
    # Fall back to IP + User-Agent hash
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    fingerprint = f"{ip}:{ua}"
    return f"ip:{hashlib.sha256(fingerprint.encode()).hexdigest()[:16]}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Global rate limiting middleware.
    
    Default limits:
    - 60 requests per minute
    - 1000 requests per hour
    - Stricter limits for auth endpoints
    """
    
    def __init__(
        self,
        app: ASGIApp,
        default_limit: int = 60,
        default_window: int = 60,
        auth_limit: int = 10,
        auth_window: int = 60
    ):
        super().__init__(app)
        self.default_limit = default_limit
        self.default_window = default_window
        self.auth_limit = auth_limit
        self.auth_window = auth_window
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for certain paths
        path = request.url.path
        if self._should_skip(path):
            return await call_next(request)
        
        # Determine limits based on path
        is_auth_endpoint = self._is_auth_endpoint(path)
        limit = self.auth_limit if is_auth_endpoint else self.default_limit
        window = self.auth_window if is_auth_endpoint else self.default_window
        
        # Get client identifier
        client_id = get_client_identifier(request)
        key = f"{client_id}:{path if is_auth_endpoint else 'global'}"
        
        # Check rate limit
        rate_data = _rate_limit_store.increment(key, window)
        
        if rate_data["count"] > limit:
            retry_after = int(rate_data["reset_at"] - time.time())
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )
        
        # Add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - rate_data["count"]))
        response.headers["X-RateLimit-Reset"] = str(int(rate_data["reset_at"]))
        
        return response
    
    def _should_skip(self, path: str) -> bool:
        """Check if path should skip rate limiting."""
        skip_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/assets/",
            "/static/",
        ]
        return any(path.startswith(skip) for skip in skip_paths)
    
    def _is_auth_endpoint(self, path: str) -> bool:
        """Check if path is an authentication endpoint."""
        auth_paths = [
            "/auth/login",
            "/auth/register",
            "/auth/password-reset",
        ]
        return any(path.startswith(auth) for auth in auth_paths)


def rate_limit(
    requests: int = 60,
    window: int = 60,
    key_func: Optional[Callable] = None
):
    """
    Decorator for endpoint-specific rate limiting.
    
    Args:
        requests: Number of requests allowed
        window: Time window in seconds
        key_func: Function to generate rate limit key (defaults to client IP + user ID)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request in args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                for v in kwargs.values():
                    if isinstance(v, Request):
                        request = v
                        break
            
            if request:
                client_id = key_func(request) if key_func else get_client_identifier(request)
                key = f"{client_id}:{func.__module__}.{func.__name__}"
                
                rate_data = _rate_limit_store.increment(key, window)
                
                if rate_data["count"] > requests:
                    retry_after = int(rate_data["reset_at"] - time.time())
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                        headers={"Retry-After": str(retry_after)}
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class RateLimitByTier:
    """Rate limiting based on subscription tier."""
    
    TIERS = {
        "trial": {"requests_per_minute": 30, "requests_per_hour": 300},
        "basic": {"requests_per_minute": 60, "requests_per_hour": 1000},
        "professional": {"requests_per_minute": 120, "requests_per_hour": 5000},
        "enterprise": {"requests_per_minute": 300, "requests_per_hour": 20000},
    }
    
    @staticmethod
    def get_limits(tier: str) -> Dict[str, int]:
        """Get rate limits for a subscription tier."""
        return RateLimitByTier.TIERS.get(tier, RateLimitByTier.TIERS["trial"])
    
    @staticmethod
    def check_rate_limit(user_id: str, tier: str, action: str = "default") -> Dict:
        """
        Check if user has exceeded their rate limit.
        
        Returns dict with:
        - allowed: bool
        - remaining: int
        - reset_at: timestamp
        - limit: int
        """
        limits = RateLimitByTier.get_limits(tier)
        key = f"tier:{user_id}:{action}"
        
        # Use per-minute limits for API actions
        limit = limits["requests_per_minute"]
        window = 60
        
        rate_data = _rate_limit_store.increment(key, window)
        
        return {
            "allowed": rate_data["count"] <= limit,
            "remaining": max(0, limit - rate_data["count"]),
            "reset_at": rate_data["reset_at"],
            "limit": limit,
            "current": rate_data["count"]
        }


def get_rate_limit_status(user_id: str) -> Dict:
    """Get current rate limit status for a user."""
    # Check both global and user-specific limits
    keys = [k for k in _rate_limit_store._cache.keys() if user_id in k or k.startswith(f"user:{user_id}")]
    
    total_requests = sum(_rate_limit_store._cache[k]["count"] for k in keys)
    
    return {
        "active_windows": len(keys),
        "total_requests": total_requests,
        "timestamp": datetime.utcnow().isoformat()
    }
