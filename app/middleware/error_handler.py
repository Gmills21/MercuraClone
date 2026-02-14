"""
Global Error Handler Middleware

Catches all unhandled exceptions and converts them to user-friendly responses.
Prevents stack traces from leaking to clients.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
import traceback
import time

from app.errors import (
    AppError, MercuraException, classify_exception,
    ErrorCategory, ErrorSeverity, internal_error
)
from app.utils.resilience import CircuitBreakerOpen, TimeoutError, RetryExhausted


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global error handling middleware.
    
    Catches all exceptions and:
    1. Converts to user-friendly AppError format
    2. Logs appropriately based on severity
    3. Returns structured error response
    4. Never leaks stack traces or internal details
    """
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            return response
            
        except MercuraException as exc:
            # Our custom exceptions - convert directly
            app_error = exc.to_app_error()
            self._log_error(request, app_error, exc.original_exception)
            return self._build_response(app_error)
            
        except CircuitBreakerOpen as exc:
            # Circuit breaker pattern
            app_error = AppError(
                category=ErrorCategory.THIRD_PARTY_API,
                code="SERVICE_TEMPORARILY_UNAVAILABLE",
                message=f"{exc.service_name} is temporarily unavailable due to high error rates.",
                severity=ErrorSeverity.WARNING,
                http_status=status.HTTP_503_SERVICE_UNAVAILABLE,
                retryable=True,
                retry_after_seconds=int(exc.retry_after),
                suggested_action="Please try again in a few minutes. The service should recover automatically."
            )
            self._log_error(request, app_error)
            return self._build_response(app_error)
            
        except TimeoutError as exc:
            # Timeout errors
            app_error = AppError(
                category=ErrorCategory.NETWORK_ERROR,
                code="REQUEST_TIMEOUT",
                message="The operation took too long to complete. Please try again.",
                severity=ErrorSeverity.WARNING,
                http_status=status.HTTP_504_GATEWAY_TIMEOUT,
                retryable=True,
                retry_after_seconds=10,
                suggested_action="Try again with a smaller request or check your connection."
            )
            self._log_error(request, app_error)
            return self._build_response(app_error)
            
        except RetryExhausted as exc:
            # All retries failed
            app_error = AppError(
                category=ErrorCategory.THIRD_PARTY_API,
                code="SERVICE_UNAVAILABLE",
                message="The service is experiencing issues. Please try again later.",
                detail=f"Failed after {exc.attempts} attempts",
                severity=ErrorSeverity.ERROR,
                http_status=status.HTTP_503_SERVICE_UNAVAILABLE,
                retryable=True,
                retry_after_seconds=60,
                suggested_action="Try again in a minute. If the issue persists, check our status page."
            )
            self._log_error(request, app_error, exc.last_exception)
            return self._build_response(app_error)
            
        except RequestValidationError as exc:
            # Validation errors from Pydantic/FastAPI
            errors = exc.errors()
            field_errors = []
            for error in errors:
                loc = ".".join(str(l) for l in error.get("loc", []))
                msg = error.get("msg", "Invalid value")
                field_errors.append(f"{loc}: {msg}")
            
            app_error = AppError(
                category=ErrorCategory.VALIDATION_ERROR,
                code="VALIDATION_ERROR",
                message="Invalid request data. Please check your input.",
                detail="; ".join(field_errors),
                severity=ErrorSeverity.INFO,
                http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                retryable=False,
                suggested_action="Check the error details and fix the invalid fields."
            )
            self._log_error(request, app_error)
            return self._build_response(app_error)
            
        except Exception as exc:
            # Catch-all for unexpected errors
            # Convert to AppError using classification logic
            app_error = classify_exception(exc)
            
            # Log full stack trace for debugging
            self._log_error(request, app_error, exc, include_traceback=True)
            
            return self._build_response(app_error)
    
    def _build_response(self, app_error: AppError) -> JSONResponse:
        """Build JSON response from AppError."""
        return JSONResponse(
            status_code=app_error.http_status,
            content=app_error.to_dict(include_detail=False)
        )
    
    def _log_error(
        self,
        request: Request,
        app_error: AppError,
        original_exception: Exception = None,
        include_traceback: bool = False
    ):
        """Log error with appropriate level and context."""
        
        # Build context
        context = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "client": request.client.host if request.client else None,
            "error_category": app_error.category.value,
            "error_code": app_error.code,
        }
        
        if app_error.context:
            context.update(app_error.context)
        
        # Log message
        log_msg = f"[{app_error.code}] {app_error.message}"
        if app_error.detail:
            log_msg += f" | Detail: {app_error.detail[:200]}"
        
        # Log with appropriate severity
        if app_error.severity == ErrorSeverity.DEBUG:
            logger.debug(log_msg, extra=context)
        elif app_error.severity == ErrorSeverity.INFO:
            logger.info(log_msg, extra=context)
        elif app_error.severity == ErrorSeverity.WARNING:
            logger.warning(log_msg, extra=context)
        elif app_error.severity == ErrorSeverity.ERROR:
            if include_traceback and original_exception:
                logger.error(
                    f"{log_msg}\n{traceback.format_exc()}",
                    extra=context
                )
            else:
                logger.error(log_msg, extra=context)
        elif app_error.severity == ErrorSeverity.CRITICAL:
            logger.critical(
                f"{log_msg}\n{traceback.format_exc() if original_exception else ''}",
                extra=context
            )
            
            # TODO: Send alert to on-call for critical errors
            # alert_service.send_critical_alert(app_error)


class APIErrorHandler:
    """
    Helper for route handlers to convert exceptions to AppError responses.
    
    Usage in routes:
        @router.get("/data")
        async def get_data():
            try:
                return await fetch_data()
            except Exception as e:
                raise APIErrorHandler.handle(e, "Failed to fetch data")
    """
    
    @staticmethod
    def handle(
        exc: Exception,
        user_message: str = None,
        category: ErrorCategory = None
    ) -> MercuraException:
        """
        Convert any exception to a MercuraException.
        
        Args:
            exc: The original exception
            user_message: Optional user-friendly message override
            category: Optional category override
            
        Returns:
            MercuraException ready to be raised
        """
        from app.errors import MercuraException
        
        # If already our exception type, return as-is
        if isinstance(exc, MercuraException):
            return exc
        
        # Classify the exception
        app_error = classify_exception(exc)
        
        # Override with custom message if provided
        if user_message:
            app_error.message = user_message
        
        # Override category if provided
        if category:
            app_error.category = category
        
        return MercuraException(app_error, exc)
    
    @staticmethod
    def not_found(resource: str = "Resource") -> MercuraException:
        """Create a not found exception."""
        from app.errors import not_found
        return MercuraException(not_found(resource))
    
    @staticmethod
    def validation_error(field: str, message: str) -> MercuraException:
        """Create a validation error exception."""
        from app.errors import validation_error
        return MercuraException(validation_error(field, message))
    
    @staticmethod
    def unauthorized() -> MercuraException:
        """Create an unauthorized exception."""
        from app.errors import unauthorized
        return MercuraException(unauthorized())
    
    @staticmethod
    def forbidden() -> MercuraException:
        """Create a forbidden exception."""
        from app.errors import forbidden
        return MercuraException(forbidden())
