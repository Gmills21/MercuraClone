"""
OpenMercura Error Handling Framework

Centralized error types, user-friendly messages, and graceful degradation patterns.
"""

from enum import Enum
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
import traceback
from fastapi import HTTPException, status


class ErrorCategory(Enum):
    """Categories of errors for appropriate handling."""
    # External service errors
    AI_SERVICE_ERROR = "ai_service_error"
    ERP_ERROR = "erp_error"
    EMAIL_ERROR = "email_error"
    BILLING_ERROR = "billing_error"
    THIRD_PARTY_API = "third_party_api"
    
    # Infrastructure errors
    DATABASE_ERROR = "database_error"
    FILE_SYSTEM_ERROR = "file_system_error"
    NETWORK_ERROR = "network_error"
    
    # Application errors
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "auth_error"
    AUTHORIZATION_ERROR = "authorization_error"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RATE_LIMIT_ERROR = "rate_limit"
    
    # Business logic errors
    BUSINESS_RULE_VIOLATION = "business_rule"
    INSUFFICIENT_QUOTA = "insufficient_quota"
    
    # Unknown/Internal
    INTERNAL_ERROR = "internal_error"
    CONFIGURATION_ERROR = "configuration_error"


class ErrorSeverity(Enum):
    """Severity levels for logging and alerting."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AppError:
    """Structured application error with user-friendly messaging."""
    
    category: ErrorCategory
    code: str
    message: str
    detail: Optional[str] = None
    severity: ErrorSeverity = ErrorSeverity.ERROR
    http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    retryable: bool = False
    retry_after_seconds: Optional[int] = None
    suggested_action: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=self.http_status,
            detail={
                "error": {
                    "category": self.category.value,
                    "code": self.code,
                    "message": self.message,
                    "retryable": self.retryable,
                    "retry_after": self.retry_after_seconds,
                    "suggested_action": self.suggested_action
                }
            }
        )
    
    def to_dict(self, include_detail: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        result = {
            "success": False,
            "error": {
                "category": self.category.value,
                "code": self.code,
                "message": self.message,
                "retryable": self.retryable,
            }
        }
        if self.retry_after_seconds:
            result["error"]["retry_after"] = self.retry_after_seconds
        if self.suggested_action:
            result["error"]["suggested_action"] = self.suggested_action
        if include_detail and self.detail:
            result["error"]["detail"] = self.detail
        return result


# Pre-defined error templates
def ai_service_unavailable(provider: str = "AI", detail: Optional[str] = None) -> AppError:
    return AppError(
        category=ErrorCategory.AI_SERVICE_ERROR,
        code="AI_SERVICE_UNAVAILABLE",
        message=f"{provider} service is temporarily unavailable. We're working on restoring it.",
        detail=detail,
        severity=ErrorSeverity.ERROR,
        http_status=status.HTTP_503_SERVICE_UNAVAILABLE,
        retryable=True,
        retry_after_seconds=30,
        suggested_action="Please try again in a moment. If the issue persists, try uploading a clearer image or providing more detailed text."
    )


def ai_rate_limited(provider: str = "AI") -> AppError:
    return AppError(
        category=ErrorCategory.AI_SERVICE_ERROR,
        code="AI_RATE_LIMITED",
        message=f"{provider} service is experiencing high demand. Please wait a moment.",
        severity=ErrorSeverity.WARNING,
        http_status=status.HTTP_429_TOO_MANY_REQUESTS,
        retryable=True,
        retry_after_seconds=30,
        suggested_action="Wait 30 seconds and try again."
    )


def ai_extraction_failed(reason: str = "extraction") -> AppError:
    return AppError(
        category=ErrorCategory.AI_SERVICE_ERROR,
        code="AI_EXTRACTION_FAILED",
        message=f"We couldn't {reason} from your document. This can happen with unclear images or unusual formats.",
        severity=ErrorSeverity.WARNING,
        http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        retryable=True,
        suggested_action="Try uploading a clearer image, converting to PDF, or typing the information directly."
    )


def erp_connection_failed(provider: str = "ERP") -> AppError:
    return AppError(
        category=ErrorCategory.ERP_ERROR,
        code="ERP_CONNECTION_FAILED",
        message=f"Could not connect to {provider}. Your changes have been saved locally.",
        severity=ErrorSeverity.WARNING,
        http_status=status.HTTP_503_SERVICE_UNAVAILABLE,
        retryable=True,
        retry_after_seconds=60,
        suggested_action="Check your connection settings in Settings > Integrations, or try again later."
    )


def erp_sync_failed(provider: str = "ERP", detail: Optional[str] = None) -> AppError:
    return AppError(
        category=ErrorCategory.ERP_ERROR,
        code="ERP_SYNC_FAILED",
        message=f"Your {provider} sync failed, but all your data is safely stored.",
        detail=detail,
        severity=ErrorSeverity.WARNING,
        http_status=status.HTTP_502_BAD_GATEWAY,
        retryable=True,
        retry_after_seconds=300,
        suggested_action="Try syncing again in a few minutes from Settings > Integrations."
    )


def email_send_failed(recipient: Optional[str] = None) -> AppError:
    recipient_msg = f" to {recipient}" if recipient else ""
    return AppError(
        category=ErrorCategory.EMAIL_ERROR,
        code="EMAIL_SEND_FAILED",
        message=f"We couldn't send your email{recipient_msg}. The quote has been saved.",
        severity=ErrorSeverity.WARNING,
        http_status=status.HTTP_502_BAD_GATEWAY,
        retryable=True,
        suggested_action="Check your email settings in Settings > Email, then try sending again."
    )


def email_not_configured() -> AppError:
    return AppError(
        category=ErrorCategory.EMAIL_ERROR,
        code="EMAIL_NOT_CONFIGURED",
        message="Email sending is not configured. Please set up your email provider first.",
        severity=ErrorSeverity.INFO,
        http_status=status.HTTP_400_BAD_REQUEST,
        retryable=False,
        suggested_action="Go to Settings > Email to configure your SMTP settings."
    )


def database_error(detail: Optional[str] = None) -> AppError:
    return AppError(
        category=ErrorCategory.DATABASE_ERROR,
        code="DATABASE_ERROR",
        message="We encountered a database issue. Please try again.",
        detail=detail,
        severity=ErrorSeverity.ERROR,
        http_status=status.HTTP_503_SERVICE_UNAVAILABLE,
        retryable=True,
        retry_after_seconds=5,
        suggested_action="If this persists, contact support."
    )


def network_timeout(service: str = "external service") -> AppError:
    return AppError(
        category=ErrorCategory.NETWORK_ERROR,
        code="NETWORK_TIMEOUT",
        message=f"Connection to {service} timed out. Please check your internet connection.",
        severity=ErrorSeverity.WARNING,
        http_status=status.HTTP_504_GATEWAY_TIMEOUT,
        retryable=True,
        retry_after_seconds=10,
        suggested_action="Check your internet connection and try again."
    )


def validation_error(field: str, message: str) -> AppError:
    return AppError(
        category=ErrorCategory.VALIDATION_ERROR,
        code="VALIDATION_ERROR",
        message=message,
        severity=ErrorSeverity.INFO,
        http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        retryable=False,
        context={"field": field}
    )


def not_found(resource: str = "Resource") -> AppError:
    return AppError(
        category=ErrorCategory.NOT_FOUND,
        code="NOT_FOUND",
        message=f"{resource} not found. It may have been deleted or you may not have access.",
        severity=ErrorSeverity.INFO,
        http_status=status.HTTP_404_NOT_FOUND,
        retryable=False
    )


def unauthorized() -> AppError:
    return AppError(
        category=ErrorCategory.AUTHENTICATION_ERROR,
        code="UNAUTHORIZED",
        message="Please log in to continue.",
        severity=ErrorSeverity.INFO,
        http_status=status.HTTP_401_UNAUTHORIZED,
        retryable=False,
        suggested_action="Log in to your account and try again."
    )


def forbidden() -> AppError:
    return AppError(
        category=ErrorCategory.AUTHORIZATION_ERROR,
        code="FORBIDDEN",
        message="You don't have permission to perform this action.",
        severity=ErrorSeverity.WARNING,
        http_status=status.HTTP_403_FORBIDDEN,
        retryable=False,
        suggested_action="Contact your organization administrator if you need access."
    )


def quota_exceeded(limit_type: str = "feature") -> AppError:
    return AppError(
        category=ErrorCategory.INSUFFICIENT_QUOTA,
        code="QUOTA_EXCEEDED",
        message=f"You've reached your {limit_type} limit for your current plan.",
        severity=ErrorSeverity.INFO,
        http_status=status.HTTP_402_PAYMENT_REQUIRED,
        retryable=False,
        suggested_action="Upgrade your plan in Settings > Billing to unlock more features."
    )


def internal_error(detail: Optional[str] = None) -> AppError:
    return AppError(
        category=ErrorCategory.INTERNAL_ERROR,
        code="INTERNAL_ERROR",
        message="Something went wrong on our end. We've logged this and will investigate.",
        detail=detail,
        severity=ErrorSeverity.ERROR,
        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        retryable=True,
        retry_after_seconds=30,
        suggested_action="If this persists, please contact support with error code: INTERNAL_ERROR"
    )


# Exception Classes
class MercuraException(Exception):
    """Base exception for OpenMercura application errors."""
    
    def __init__(self, app_error: AppError, original_exception: Optional[Exception] = None):
        self.app_error = app_error
        self.original_exception = original_exception
        super().__init__(app_error.message)
    
    def to_app_error(self) -> AppError:
        return self.app_error


class AIServiceException(MercuraException):
    pass


class ERPException(MercuraException):
    pass


class EmailException(MercuraException):
    pass


class DatabaseException(MercuraException):
    pass


class ValidationException(MercuraException):
    pass


class NetworkException(MercuraException):
    pass


# Error Classification Helper
def classify_exception(exc: Exception) -> AppError:
    """Classify any exception into an appropriate AppError."""
    import sqlite3
    import httpx
    
    # httpx network errors
    if isinstance(exc, httpx.TimeoutException):
        return network_timeout()
    
    if isinstance(exc, httpx.ConnectError):
        return AppError(
            category=ErrorCategory.NETWORK_ERROR,
            code="CONNECTION_FAILED",
            message="Could not connect to external service. Please check your internet connection.",
            detail=str(exc),
            severity=ErrorSeverity.WARNING,
            http_status=status.HTTP_503_SERVICE_UNAVAILABLE,
            retryable=True,
            retry_after_seconds=30
        )
    
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        if status_code == 429:
            return ai_rate_limited()
        elif status_code >= 500:
            return AppError(
                category=ErrorCategory.THIRD_PARTY_API,
                code=f"EXTERNAL_ERROR_{status_code}",
                message="External service is experiencing issues. Please try again later.",
                detail=str(exc),
                severity=ErrorSeverity.WARNING,
                http_status=status.HTTP_502_BAD_GATEWAY,
                retryable=True,
                retry_after_seconds=60
            )
    
    # SQLite errors
    if isinstance(exc, sqlite3.IntegrityError):
        return AppError(
            category=ErrorCategory.DATABASE_ERROR,
            code="INTEGRITY_ERROR",
            message="This operation would create a duplicate or conflict with existing data.",
            detail=str(exc),
            severity=ErrorSeverity.INFO,
            http_status=status.HTTP_409_CONFLICT,
            retryable=False,
            suggested_action="Check if the resource already exists or modify your request."
        )
    
    if isinstance(exc, sqlite3.OperationalError):
        return database_error(detail=str(exc))
    
    # SMTP/Email errors
    error_str = str(exc).lower()
    if any(kw in error_str for kw in ['smtp', 'email', 'mail', 'authentication']):
        if 'authentication' in error_str:
            return AppError(
                category=ErrorCategory.EMAIL_ERROR,
                code="EMAIL_AUTH_FAILED",
                message="Email authentication failed. Please check your SMTP credentials.",
                severity=ErrorSeverity.INFO,
                http_status=status.HTTP_400_BAD_REQUEST,
                retryable=False,
                suggested_action="Update your email settings in Settings > Email."
            )
        return email_send_failed()
    
    # Default to internal error
    return internal_error(detail=f"{type(exc).__name__}: {str(exc)}\n{traceback.format_exc()}")
