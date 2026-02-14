"""
Observability & Telemetry Module

Production-grade observability with:
- Structured logging (JSON format for Datadog/CloudWatch/Logtail)
- Sentry error tracking integration
- Performance monitoring (API latency, DB query times)
- Distributed tracing support
"""

import json
import os
import sys
import asyncio
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Callable
from functools import wraps
from contextlib import contextmanager

from loguru import logger
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings


# =============================================================================
# STRUCTURED LOGGING
# =============================================================================

class StructuredLogFormatter:
    """
    JSON formatter for structured logging.
    
    Outputs logs in JSON format compatible with:
    - Datadog
    - AWS CloudWatch
    - Logtail
    - Splunk
    - ELK Stack
    """
    
    @staticmethod
    def format_record(record: dict) -> str:
        """Format a log record as JSON."""
        log_entry = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "message": record["message"],
            "source": {
                "file": record["file"].path,
                "line": record["line"],
                "function": record["function"],
            },
            "service": settings.app_name.lower(),
            "environment": settings.app_env,
            "host": getattr(settings, "host", "unknown"),
        }
        
        # Add extra fields if present
        if "extra" in record and record["extra"]:
            log_entry["context"] = dict(record["extra"])
        
        # Add exception info if present
        if record["exception"]:
            log_entry["exception"] = {
                "type": record["exception"].type.__name__ if record["exception"].type else None,
                "value": str(record["exception"].value) if record["exception"].value else None,
                "traceback": record["exception"].traceback if hasattr(record["exception"], "traceback") else None,
            }
        
        return json.dumps(log_entry, default=str)


def setup_structured_logging():
    """
    Configure structured JSON logging for production.
    
    Call this in main.py to enable structured logging output.
    """
    # Remove default handler
    logger.remove()
    
    # Add structured JSON handler for production
    if settings.app_env == "production":
        logger.add(
            sys.stderr,
            format=StructuredLogFormatter.format_record,
            level=settings.log_level,
            serialize=True,
        )
        # Also add file output with structured format
        logger.add(
            settings.log_file,
            format=StructuredLogFormatter.format_record,
            level=settings.log_level,
            rotation="500 MB",
            retention="10 days",
            serialize=True,
        )
    else:
        # Development: human-readable format
        logger.add(
            sys.stderr,
            level=settings.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        )
        logger.add(
            settings.log_file,
            rotation="500 MB",
            retention="10 days",
            level=settings.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
        )


# =============================================================================
# SENTRY ERROR TRACKING
# =============================================================================

class SentryManager:
    """
    Sentry integration for error tracking.
    
    Captures exceptions with:
    - Stack traces
    - User context
    - Request context
    - Tags and extra data
    """
    
    def __init__(self):
        self.enabled = False
        self.sentry_sdk = None
        self._init_sentry()
    
    def _init_sentry(self):
        """Initialize Sentry SDK if DSN is configured."""
        dsn = getattr(settings, "sentry_dsn", None) or os.getenv("SENTRY_DSN")
        
        if not dsn:
            return
        
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlite import SqliteIntegration
            
            sentry_sdk.init(
                dsn=dsn,
                environment=settings.app_env,
                release=getattr(settings, "app_version", "1.0.0"),
                integrations=[
                    FastApiIntegration(),
                    SqliteIntegration(),
                ],
                traces_sample_rate=0.1,  # 10% of requests for performance monitoring
                profiles_sample_rate=0.01,  # 1% for profiling
                before_send=self._before_send,
            )
            
            self.sentry_sdk = sentry_sdk
            self.enabled = True
            logger.info("Sentry error tracking initialized")
            
        except ImportError:
            logger.warning("Sentry SDK not installed. Run: pip install sentry-sdk[fastapi]")
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")
    
    def _before_send(self, event, hint):
        """Filter events before sending to Sentry."""
        # Filter out certain errors (e.g., 404s, validation errors)
        if "exception" in event:
            exceptions = event["exception"].get("values", [])
            for exc in exceptions:
                exc_type = exc.get("type", "")
                # Skip common non-actionable errors
                if exc_type in ["HTTPException", "StarletteHTTPException"]:
                    if exc.get("value", "").startswith("404"):
                        return None
        
        return event
    
    def capture_exception(self, exc: Exception, context: Optional[Dict] = None):
        """Capture an exception with optional context."""
        if not self.enabled or not self.sentry_sdk:
            return
        
        with self.sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_extra(key, value)
            
            self.sentry_sdk.capture_exception(exc)
    
    def capture_message(self, message: str, level: str = "info", context: Optional[Dict] = None):
        """Capture a message with optional context."""
        if not self.enabled or not self.sentry_sdk:
            return
        
        with self.sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_extra(key, value)
            
            self.sentry_sdk.capture_message(message, level=level)
    
    def set_user(self, user_id: str, email: Optional[str] = None, **kwargs):
        """Set user context for subsequent events."""
        if not self.enabled or not self.sentry_sdk:
            return
        
        user = {"id": user_id}
        if email:
            user["email"] = email
        user.update(kwargs)
        
        self.sentry_sdk.set_user(user)
    
    def clear_user(self):
        """Clear user context."""
        if not self.enabled or not self.sentry_sdk:
            return
        
        self.sentry_sdk.set_user(None)


# Global Sentry manager instance
sentry_manager = SentryManager()


# =============================================================================
# PERFORMANCE MONITORING
# =============================================================================

class PerformanceMetrics:
    """
    Performance metrics collector.
    
    Tracks:
    - API response times
    - Database query times
    - External service call latencies
    """
    
    def __init__(self):
        self.metrics: Dict[str, list] = {}
        self.max_samples = 1000
    
    def record(self, metric_name: str, value: float, unit: str = "ms"):
        """Record a metric value."""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        self.metrics[metric_name].append({
            "value": value,
            "unit": unit,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # Keep only recent samples
        if len(self.metrics[metric_name]) > self.max_samples:
            self.metrics[metric_name] = self.metrics[metric_name][-self.max_samples:]
    
    def get_stats(self, metric_name: str, last_n: int = 100) -> Optional[Dict]:
        """Get statistics for a metric."""
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return None
        
        values = [m["value"] for m in self.metrics[metric_name][-last_n:]]
        
        if not values:
            return None
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "p50": sorted(values)[len(values) // 2],
            "p95": sorted(values)[int(len(values) * 0.95)] if len(values) >= 20 else max(values),
            "p99": sorted(values)[int(len(values) * 0.99)] if len(values) >= 100 else max(values),
            "unit": self.metrics[metric_name][-1]["unit"],
        }
    
    def get_all_stats(self) -> Dict:
        """Get statistics for all metrics."""
        return {
            name: self.get_stats(name)
            for name in self.metrics.keys()
        }


# Global metrics instance
performance_metrics = PerformanceMetrics()


@contextmanager
def timed_operation(operation_name: str, context: Optional[Dict] = None):
    """
    Context manager for timing operations.
    
    Usage:
        with timed_operation("db_query", {"table": "users"}):
            result = await db.fetch(query)
    """
    start = time.time()
    try:
        yield
    except Exception as e:
        duration = (time.time() - start) * 1000
        logger.warning(
            f"Operation '{operation_name}' failed after {duration:.2f}ms",
            extra={"operation": operation_name, "duration_ms": duration, "error": str(e), **(context or {})}
        )
        raise
    finally:
        duration = (time.time() - start) * 1000
        performance_metrics.record(operation_name, duration, "ms")
        
        # Log slow operations (>1s)
        if duration > 1000:
            logger.warning(
                f"Slow operation detected: '{operation_name}' took {duration:.2f}ms",
                extra={"operation": operation_name, "duration_ms": duration, **(context or {})}
            )


def timed(func: Callable) -> Callable:
    """Decorator for timing function execution."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        operation_name = f"{func.__module__}.{func.__name__}"
        with timed_operation(operation_name):
            return await func(*args, **kwargs)
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        operation_name = f"{func.__module__}.{func.__name__}"
        start = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            duration = (time.time() - start) * 1000
            performance_metrics.record(operation_name, duration, "ms")
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


# =============================================================================
# REQUEST TRACING MIDDLEWARE
# =============================================================================

class RequestTracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request tracing and performance monitoring.
    
    Adds:
    - Request ID for distributed tracing
    - Response time tracking
    - Request/response logging
    - Sentry context
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/status", "/metrics"]
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request
        path = request.url.path
        method = request.method
        
        if path not in self.exclude_paths:
            logger.info(
                f"Request started: {method} {path}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "query": str(request.query_params),
                    "client": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                }
            )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = (time.time() - start_time) * 1000
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration:.2f}ms"
            
            # Record metrics
            metric_name = f"api_{method.lower()}_{path.replace('/', '_')}"
            performance_metrics.record(metric_name, duration, "ms")
            
            # Log response
            if path not in self.exclude_paths:
                logger.info(
                    f"Request completed: {method} {path} - {response.status_code} in {duration:.2f}ms",
                    extra={
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "status_code": response.status_code,
                        "duration_ms": duration,
                    }
                )
                
                # Log slow requests (> 5 seconds)
                if duration > 5000:
                    logger.warning(
                        f"Slow request detected: {method} {path} took {duration:.2f}ms",
                        extra={
                            "request_id": request_id,
                            "method": method,
                            "path": path,
                            "status_code": response.status_code,
                            "duration_ms": duration,
                        }
                    )
            
            return response
            
        except Exception as exc:
            duration = (time.time() - start_time) * 1000
            
            # Log error
            logger.error(
                f"Request failed: {method} {path} after {duration:.2f}ms",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "duration_ms": duration,
                    "error": str(exc),
                }
            )
            
            # Capture in Sentry
            sentry_manager.capture_exception(exc, context={
                "request_id": request_id,
                "method": method,
                "path": path,
            })
            
            raise


# =============================================================================
# DATABASE QUERY MONITORING
# =============================================================================

class DatabaseQueryMonitor:
    """
    Monitor database query performance.
    
    Wraps database connections to track query times.
    """
    
    @staticmethod
    def wrap_cursor(cursor, operation: str = "query"):
        """Wrap a cursor to monitor query execution time."""
        original_execute = cursor.execute
        original_executemany = cursor.executemany
        
        def monitored_execute(sql, parameters=None):
            start = time.time()
            try:
                return original_execute(sql, parameters)
            finally:
                duration = (time.time() - start) * 1000
                performance_metrics.record(f"db_{operation}", duration, "ms")
                
                # Log slow queries
                if duration > 500:
                    logger.warning(
                        f"Slow query detected ({duration:.2f}ms): {sql[:100]}...",
                        extra={
                            "query": sql[:500],
                            "duration_ms": duration,
                            "operation": operation,
                        }
                    )
        
        def monitored_executemany(sql, seq_of_parameters):
            start = time.time()
            try:
                return original_executemany(sql, seq_of_parameters)
            finally:
                duration = (time.time() - start) * 1000
                performance_metrics.record(f"db_{operation}_many", duration, "ms")
        
        cursor.execute = monitored_execute
        cursor.executemany = monitored_executemany
        return cursor


# =============================================================================
# HEALTH CHECKS WITH METRICS
# =============================================================================

class ObservabilityHealthChecker:
    """Extended health checks with observability info."""
    
    @staticmethod
    def get_health() -> Dict:
        """Get comprehensive health status including observability."""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "observability": {
                "sentry_enabled": sentry_manager.enabled,
                "structured_logging": settings.app_env == "production",
                "metrics_collected": len(performance_metrics.metrics),
            },
            "performance": performance_metrics.get_all_stats(),
        }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_request_id(request: Request) -> str:
    """Get the request ID from the request state."""
    return getattr(request.state, "request_id", "unknown")


def log_user_action(user_id: str, action: str, details: Optional[Dict] = None):
    """Log a user action for audit trail."""
    logger.info(
        f"User action: {action}",
        extra={
            "user_id": user_id,
            "action": action,
            **(details or {}),
        }
    )
