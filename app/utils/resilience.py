"""
Resilience Utilities for OpenMercura

Implements retry logic, circuit breakers, timeouts, and graceful degradation patterns.
"""

import asyncio
import functools
import random
import time
from enum import Enum
from typing import Callable, Any, Optional, TypeVar, Generic, List, Type
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from loguru import logger

T = TypeVar('T')


# =============================================================================
# RETRY LOGIC WITH EXPONENTIAL BACKOFF
# =============================================================================

class RetryExhausted(Exception):
    """Raised when all retry attempts have been exhausted."""
    
    def __init__(self, attempts: int, last_exception: Optional[Exception] = None):
        self.attempts = attempts
        self.last_exception = last_exception
        super().__init__(f"Failed after {attempts} attempts")


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True  # Add randomness to prevent thundering herd
    retryable_exceptions: List[Type[Exception]] = field(default_factory=lambda: [Exception])
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt with exponential backoff."""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            # Add ±25% jitter
            jitter_amount = delay * 0.25
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, delay)


async def with_retry(
    func: Callable[..., Any],
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> Any:
    """
    Execute a function with retry logic and exponential backoff.
    
    Args:
        func: Async function to execute
        config: Retry configuration
        *args, **kwargs: Arguments to pass to func
        
    Returns:
        Result of func
        
    Raises:
        RetryExhausted: If all attempts fail
    """
    config = config or RetryConfig()
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)
        except tuple(config.retryable_exceptions) as e:
            last_exception = e
            
            if attempt < config.max_attempts - 1:
                delay = config.calculate_delay(attempt)
                logger.warning(
                    f"Attempt {attempt + 1}/{config.max_attempts} failed: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"All {config.max_attempts} attempts exhausted. Last error: {e}")
    
    raise RetryExhausted(config.max_attempts, last_exception)


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: Optional[List[Type[Exception]]] = None
):
    """
    Decorator for adding retry logic to async functions.
    
    Usage:
        @retry(max_attempts=3, retryable_exceptions=[httpx.TimeoutException])
        async def fetch_data():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            config = RetryConfig(
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                retryable_exceptions=retryable_exceptions or [Exception]
            )
            return await with_retry(func, *args, config=config, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# CIRCUIT BREAKER PATTERN
# =============================================================================

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5           # Failures before opening
    recovery_timeout: float = 60.0       # Seconds before half-open
    half_open_max_calls: int = 3         # Test calls in half-open state
    success_threshold: int = 2           # Successes to close circuit
    

class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    
    Prevents cascading failures by stopping requests to failing services.
    Automatically recovers when service comes back online.
    
    Usage:
        breaker = CircuitBreaker("quickbooks", CircuitBreakerConfig())
        
        @breaker.protect
        async def call_quickbooks():
            ...
    """
    
    _instances: dict = {}  # Singleton per service name
    
    def __new__(cls, name: str, config: Optional[CircuitBreakerConfig] = None):
        if name not in cls._instances:
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instances[name] = instance
        return cls._instances[name]
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        if self._initialized:
            return
            
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
        self._initialized = True
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open (rejecting requests)."""
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed >= self.config.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
                    return False
            return True
        return False
    
    def record_success(self):
        """Record a successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.successes += 1
            if self.successes >= self.config.success_threshold:
                self._close_circuit()
        else:
            # In closed state, just reset failures
            if self.failures > 0:
                self.failures = 0
    
    def record_failure(self):
        """Record a failed call."""
        self.failures += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.state == CircuitState.HALF_OPEN:
            # Failed during recovery test, reopen
            self._open_circuit()
        elif self.failures >= self.config.failure_threshold:
            self._open_circuit()
    
    def _open_circuit(self):
        """Open the circuit (stop requests)."""
        if self.state != CircuitState.OPEN:
            logger.error(
                f"Circuit breaker '{self.name}' OPENED after {self.failures} failures. "
                f"Recovery in {self.config.recovery_timeout}s"
            )
            self.state = CircuitState.OPEN
            self.successes = 0
            self.half_open_calls = 0
    
    def _close_circuit(self):
        """Close the circuit (normal operation)."""
        logger.info(f"Circuit breaker '{self.name}' CLOSED. Service recovered.")
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.half_open_calls = 0
        self.last_failure_time = None
    
    def protect(self, func: Callable) -> Callable:
        """
        Decorator to protect a function with circuit breaker.
        
        Raises CircuitBreakerOpen if circuit is open.
        """
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if self.is_open:
                raise CircuitBreakerOpen(self.name, self.config.recovery_timeout)
            
            # Track half-open calls
            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls >= self.config.half_open_max_calls:
                    raise CircuitBreakerOpen(self.name, self.config.recovery_timeout)
                self.half_open_calls += 1
            
            try:
                result = await func(*args, **kwargs)
                self.record_success()
                return result
            except Exception as e:
                self.record_failure()
                raise
        
        return wrapper
    
    def get_status(self) -> dict:
        """Get current circuit breaker status."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self.failures,
            "successes": self.successes,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class CircuitBreakerOpen(Exception):
    """Raised when calling a service with open circuit breaker."""
    
    def __init__(self, service_name: str, retry_after: float):
        self.service_name = service_name
        self.retry_after = retry_after
        super().__init__(f"Circuit breaker open for {service_name}. Retry after {retry_after}s")


# =============================================================================
# TIMEOUT HANDLING
# =============================================================================

class TimeoutError(Exception):
    """Custom timeout error for better handling."""
    pass


async def with_timeout(
    coro,
    timeout_seconds: float,
    timeout_message: str = "Operation timed out"
) -> Any:
    """
    Run a coroutine with a timeout.
    
    Args:
        coro: Coroutine to execute
        timeout_seconds: Maximum time to wait
        timeout_message: Message for timeout exception
        
    Returns:
        Result of coroutine
        
    Raises:
        TimeoutError: If operation exceeds timeout
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise TimeoutError(timeout_message)


# =============================================================================
# FALLBACK / DEGRADATION PATTERNS
# =============================================================================

@dataclass
class FallbackResult(Generic[T]):
    """Result from a fallback operation."""
    value: T
    is_fallback: bool = False
    fallback_reason: Optional[str] = None
    original_error: Optional[Exception] = None


async def with_fallback(
    primary_func: Callable[..., Any],
    fallback_func: Callable[..., Any],
    *args,
    **kwargs
) -> FallbackResult:
    """
    Try primary function, fall back to secondary on failure.
    
    Args:
        primary_func: First function to try
        fallback_func: Fallback if primary fails
        *args, **kwargs: Arguments for both functions
        
    Returns:
        FallbackResult with value and metadata
    """
    try:
        result = await primary_func(*args, **kwargs)
        return FallbackResult(value=result, is_fallback=False)
    except Exception as e:
        logger.warning(f"Primary failed ({e}), using fallback")
        try:
            result = await fallback_func(*args, **kwargs)
            return FallbackResult(
                value=result,
                is_fallback=True,
                fallback_reason=str(e),
                original_error=e
            )
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {fallback_error}")
            raise


class DegradationManager:
    """
    Manages graceful degradation of features.
    
    Allows the application to continue functioning with reduced capabilities
    when dependencies fail.
    
    Example:
        - AI extraction fails → Fall back to manual entry
        - QuickBooks sync fails → Store locally, sync later
        - Email fails → Queue for retry
    """
    
    def __init__(self):
        self._degraded_features: dict = {}
    
    def mark_degraded(self, feature: str, reason: str, fallback_available: bool = True):
        """Mark a feature as degraded."""
        self._degraded_features[feature] = {
            "degraded_at": datetime.utcnow().isoformat(),
            "reason": reason,
            "fallback_available": fallback_available
        }
        logger.warning(f"Feature '{feature}' degraded: {reason}")
    
    def is_degraded(self, feature: str) -> bool:
        """Check if a feature is currently degraded."""
        return feature in self._degraded_features
    
    def get_degradation_info(self, feature: str) -> Optional[dict]:
        """Get degradation info for a feature."""
        return self._degraded_features.get(feature)
    
    def restore(self, feature: str):
        """Restore a degraded feature."""
        if feature in self._degraded_features:
            del self._degraded_features[feature]
            logger.info(f"Feature '{feature}' restored")
    
    def get_all_degraded(self) -> dict:
        """Get all degraded features."""
        return self._degraded_features.copy()


# Global degradation manager
_degradation_manager: Optional[DegradationManager] = None


def get_degradation_manager() -> DegradationManager:
    """Get the global degradation manager."""
    global _degradation_manager
    if _degradation_manager is None:
        _degradation_manager = DegradationManager()
    return _degradation_manager


# =============================================================================
# HEALTH CHECK HELPERS
# =============================================================================

@dataclass
class HealthStatus:
    """Health status for a service/component."""
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    response_time_ms: float
    last_checked: datetime
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class HealthChecker:
    """Utility for checking health of external services."""
    
    def __init__(self):
        self._checks: dict = {}
    
    async def check(
        self,
        name: str,
        check_func: Callable[..., Any],
        timeout_seconds: float = 10.0,
        **kwargs
    ) -> HealthStatus:
        """Run a health check with timeout."""
        start = time.time()
        
        try:
            await with_timeout(check_func(**kwargs), timeout_seconds)
            response_time = (time.time() - start) * 1000
            
            status = HealthStatus(
                name=name,
                status="healthy",
                response_time_ms=response_time,
                last_checked=datetime.utcnow()
            )
            self._checks[name] = status
            return status
            
        except TimeoutError:
            response_time = (time.time() - start) * 1000
            status = HealthStatus(
                name=name,
                status="degraded",
                response_time_ms=response_time,
                last_checked=datetime.utcnow(),
                error=f"Health check timed out after {timeout_seconds}s"
            )
            self._checks[name] = status
            return status
            
        except Exception as e:
            response_time = (time.time() - start) * 1000
            status = HealthStatus(
                name=name,
                status="unhealthy",
                response_time_ms=response_time,
                last_checked=datetime.utcnow(),
                error=str(e)
            )
            self._checks[name] = status
            return status
    
    def get_status(self, name: Optional[str] = None) -> dict:
        """Get health status."""
        if name:
            check = self._checks.get(name)
            if check:
                return {
                    "name": check.name,
                    "status": check.status,
                    "response_time_ms": round(check.response_time_ms, 2),
                    "last_checked": check.last_checked.isoformat(),
                    "error": check.error
                }
            return {"error": f"No health check found for {name}"}
        
        return {
            name: {
                "status": check.status,
                "response_time_ms": round(check.response_time_ms, 2),
                "last_checked": check.last_checked.isoformat(),
                "error": check.error
            }
            for name, check in self._checks.items()
        }


# Global health checker
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get the global health checker."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


# =============================================================================
# COMMON CONFIGURATIONS
# =============================================================================

# Retry config for AI providers (respect rate limits)
AI_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=2.0,
    max_delay=30.0,
    retryable_exceptions=[Exception]  # Will be filtered by error type in practice
)

# Retry config for ERP integrations (longer delays)
ERP_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=5.0,
    max_delay=300.0,  # 5 minutes
    retryable_exceptions=[Exception]
)

# Retry config for email (moderate delays)
EMAIL_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    base_delay=3.0,
    max_delay=30.0,
    retryable_exceptions=[Exception]
)

# Retry config for database (quick retries)
DB_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=0.5,
    max_delay=5.0,
    retryable_exceptions=[Exception]
)
