#!/usr/bin/env python3
"""
Error Handling Framework Tests

Tests all error scenarios to verify the production-grade error handling works:
1. Error types and user-friendly messages
2. Retry logic with exponential backoff
3. Circuit breaker pattern
4. Timeout protection
5. Middleware integration
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.errors import (
    AppError, ErrorCategory, ErrorSeverity, MercuraException,
    ai_service_unavailable, ai_rate_limited, ai_extraction_failed,
    erp_connection_failed, erp_sync_failed, email_send_failed, email_not_configured,
    database_error, network_timeout, validation_error, not_found,
    unauthorized, forbidden, quota_exceeded, internal_error, classify_exception
)
from app.utils.resilience import (
    RetryConfig, with_retry, retry, RetryExhausted,
    CircuitBreaker, CircuitBreakerConfig, CircuitBreakerOpen, CircuitState,
    TimeoutError, with_timeout,
    with_fallback, FallbackResult,
    DegradationManager, get_degradation_manager,
    HealthChecker, get_health_checker
)

# Test results
results = []


def test_section(name):
    """Print test section header."""
    print(f"\n{'=' * 70}")
    print(f"  {name}")
    print(f"{'=' * 70}")


def test_pass(name):
    """Record passing test."""
    results.append(("PASS", name))
    print(f"  [PASS] {name}")


def test_fail(name, error):
    """Record failing test."""
    results.append(("FAIL", name, str(error)))
    print(f"  [FAIL] {name}: {error}")


# =============================================================================
# TEST 1: Error Types
# =============================================================================

def test_error_types():
    """Test all predefined error types."""
    test_section("TEST 1: Error Types")
    
    errors_to_test = [
        ("AI Service Unavailable", ai_service_unavailable("Gemini")),
        ("AI Rate Limited", ai_rate_limited("Gemini")),
        ("AI Extraction Failed", ai_extraction_failed("extract text")),
        ("ERP Connection Failed", erp_connection_failed("QuickBooks")),
        ("ERP Sync Failed", erp_sync_failed("QuickBooks", "timeout")),
        ("Email Send Failed", email_send_failed("customer@example.com")),
        ("Email Not Configured", email_not_configured()),
        ("Database Error", database_error("connection refused")),
        ("Network Timeout", network_timeout("Gemini API")),
        ("Validation Error", validation_error("email", "Invalid email format")),
        ("Not Found", not_found("Customer")),
        ("Unauthorized", unauthorized()),
        ("Forbidden", forbidden()),
        ("Quota Exceeded", quota_exceeded("extraction")),
        ("Internal Error", internal_error("unexpected null")),
    ]
    
    for name, error in errors_to_test:
        try:
            # Verify error has required fields
            assert error.category in ErrorCategory, f"Invalid category: {error.category}"
            assert error.code, "Missing error code"
            assert error.message, "Missing error message"
            assert error.severity in ErrorSeverity, f"Invalid severity: {error.severity}"
            assert isinstance(error.http_status, int), "Invalid HTTP status"
            assert isinstance(error.retryable, bool), "Invalid retryable flag"
            
            # Verify dict conversion works
            error_dict = error.to_dict()
            assert error_dict["success"] is False
            assert "error" in error_dict
            
            # Verify HTTP exception conversion works
            http_exc = error.to_http_exception()
            assert http_exc.status_code == error.http_status
            
            test_pass(name)
        except Exception as e:
            test_fail(name, e)


# =============================================================================
# TEST 2: Retry Logic
# =============================================================================

async def test_retry_logic():
    """Test retry logic with exponential backoff."""
    test_section("TEST 2: Retry Logic")
    
    # Test 2a: Retry config calculation
    try:
        config = RetryConfig(max_attempts=3, base_delay=1.0, max_delay=60.0)
        
        # Test delay calculation (without jitter for predictability)
        config.jitter = False
        delay0 = config.calculate_delay(0)
        delay1 = config.calculate_delay(1)
        delay2 = config.calculate_delay(2)
        
        assert delay0 == 1.0, f"Expected delay 1.0, got {delay0}"
        assert delay1 == 2.0, f"Expected delay 2.0, got {delay1}"
        assert delay2 == 4.0, f"Expected delay 4.0, got {delay2}"
        
        # Test max delay cap
        delay10 = config.calculate_delay(10)
        assert delay10 == 60.0, f"Expected max delay 60.0, got {delay10}"
        
        test_pass("Retry config delay calculation")
    except Exception as e:
        test_fail("Retry config delay calculation", e)
    
    # Test 2b: Retry decorator
    attempt_count = 0
    
    @retry(max_attempts=3, base_delay=0.1, retryable_exceptions=[ValueError])
    async def failing_function():
        nonlocal attempt_count
        attempt_count += 1
        raise ValueError("Intentional failure")
    
    try:
        await failing_function()
        test_fail("Retry decorator - should have raised RetryExhausted", "No exception raised")
    except RetryExhausted as e:
        if attempt_count == 3:
            test_pass("Retry decorator - exhausts after 3 attempts")
        else:
            test_fail(f"Retry decorator - wrong attempt count", f"Expected 3, got {attempt_count}")
    except Exception as e:
        test_fail("Retry decorator", e)
    
    # Test 2c: Retry with eventual success
    success_attempt = 0
    
    @retry(max_attempts=5, base_delay=0.1, retryable_exceptions=[RuntimeError])
    async def eventual_success():
        nonlocal success_attempt
        success_attempt += 1
        if success_attempt < 3:
            raise RuntimeError("Not yet")
        return "success"
    
    try:
        result = await eventual_success()
        if result == "success" and success_attempt == 3:
            test_pass("Retry with eventual success")
        else:
            test_fail("Retry with eventual success", f"Wrong result or attempts: {result}, {success_attempt}")
    except Exception as e:
        test_fail("Retry with eventual success", e)


# =============================================================================
# TEST 3: Circuit Breaker
# =============================================================================

async def test_circuit_breaker():
    """Test circuit breaker pattern."""
    test_section("TEST 3: Circuit Breaker")
    
    # Create circuit breaker with short timeout for testing
    cb = CircuitBreaker(
        "test_service",
        CircuitBreakerConfig(failure_threshold=3, recovery_timeout=1.0)
    )
    
    # Reset state
    cb.state = CircuitState.CLOSED
    cb.failures = 0
    cb.successes = 0
    
    # Test 3a: Normal operation (closed circuit)
    try:
        assert not cb.is_open, "Circuit should be closed initially"
        test_pass("Circuit starts closed")
    except Exception as e:
        test_fail("Circuit starts closed", e)
    
    # Test 3b: Record failures and open circuit
    try:
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED, "Should still be closed after 2 failures"
        
        cb.record_failure()  # Third failure - should open
        assert cb.state == CircuitState.OPEN, f"Should be open after 3 failures, got {cb.state}"
        assert cb.is_open, "is_open should return True"
        
        test_pass("Circuit opens after threshold failures")
    except Exception as e:
        test_fail("Circuit opens after threshold failures", e)
    
    # Test 3c: Circuit breaker open exception
    try:
        @cb.protect
        async def protected_function():
            return "success"
        
        await protected_function()
        test_fail("Protected function should raise CircuitBreakerOpen", "No exception raised")
    except CircuitBreakerOpen as e:
        if e.service_name == "test_service" and e.retry_after == 1.0:
            test_pass("CircuitBreakerOpen exception raised correctly")
        else:
            test_fail("CircuitBreakerOpen exception", f"Wrong attributes: {e.service_name}, {e.retry_after}")
    except Exception as e:
        test_fail("Circuit breaker open exception", e)
    
    # Test 3d: Circuit recovery (half-open)
    try:
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Check if circuit transitioned to half-open
        is_open = cb.is_open  # This triggers state transition
        
        if cb.state == CircuitState.HALF_OPEN:
            test_pass("Circuit enters half-open after recovery timeout")
        else:
            test_fail("Circuit recovery", f"Expected HALF_OPEN, got {cb.state}")
    except Exception as e:
        test_fail("Circuit recovery", e)
    
    # Test 3e: Record success and close circuit
    try:
        # Reset and test success recording
        cb.state = CircuitState.HALF_OPEN
        cb.successes = 0
        cb.failures = 3
        
        cb.record_success()
        cb.record_success()
        
        assert cb.state == CircuitState.CLOSED, f"Should be closed after 2 successes, got {cb.state}"
        assert cb.failures == 0, "Failures should be reset"
        
        test_pass("Circuit closes after success threshold")
    except Exception as e:
        test_fail("Circuit closes after success threshold", e)


# =============================================================================
# TEST 4: Timeout Protection
# =============================================================================

async def test_timeout():
    """Test timeout protection."""
    test_section("TEST 4: Timeout Protection")
    
    # Test 4a: Operation within timeout
    try:
        async def quick_operation():
            await asyncio.sleep(0.1)
            return "completed"
        
        result = await with_timeout(quick_operation(), 1.0)
        if result == "completed":
            test_pass("Operation within timeout succeeds")
        else:
            test_fail("Operation within timeout", f"Wrong result: {result}")
    except Exception as e:
        test_fail("Operation within timeout", e)
    
    # Test 4b: Operation exceeding timeout
    try:
        async def slow_operation():
            await asyncio.sleep(2.0)
            return "completed"
        
        await with_timeout(slow_operation(), 0.5, "Custom timeout message")
        test_fail("Slow operation should raise TimeoutError", "No exception raised")
    except TimeoutError as e:
        if "Custom timeout message" in str(e):
            test_pass("TimeoutError raised with custom message")
        else:
            test_fail("TimeoutError message", f"Wrong message: {e}")
    except Exception as e:
        test_fail("Timeout protection", e)


# =============================================================================
# TEST 5: Fallback/Degradation
# =============================================================================

async def test_fallback():
    """Test fallback and graceful degradation."""
    test_section("TEST 5: Fallback & Degradation")
    
    # Test 5a: Fallback when primary fails
    async def primary_func():
        raise ValueError("Primary failed")
    
    async def fallback_func():
        return "fallback_result"
    
    try:
        result = await with_fallback(primary_func, fallback_func)
        
        if result.value == "fallback_result" and result.is_fallback and "Primary failed" in result.fallback_reason:
            test_pass("Fallback returns fallback value on primary failure")
        else:
            test_fail("Fallback result", f"Wrong result: {result}")
    except Exception as e:
        test_fail("Fallback on failure", e)
    
    # Test 5b: Primary succeeds (no fallback)
    async def working_primary():
        return "primary_result"
    
    try:
        result = await with_fallback(working_primary, fallback_func)
        
        if result.value == "primary_result" and not result.is_fallback:
            test_pass("Primary success - no fallback used")
        else:
            test_fail("Primary success", f"Wrong result: {result}")
    except Exception as e:
        test_fail("Primary success", e)
    
    # Test 5c: Degradation manager
    try:
        dm = DegradationManager()
        
        dm.mark_degraded("ai_extraction", "Gemini API rate limited", fallback_available=True)
        
        assert dm.is_degraded("ai_extraction"), "Feature should be marked degraded"
        
        info = dm.get_degradation_info("ai_extraction")
        assert info["reason"] == "Gemini API rate limited"
        assert info["fallback_available"] is True
        
        degraded = dm.get_all_degraded()
        assert "ai_extraction" in degraded
        
        dm.restore("ai_extraction")
        assert not dm.is_degraded("ai_extraction"), "Feature should be restored"
        
        test_pass("Degradation manager tracks and restores features")
    except Exception as e:
        test_fail("Degradation manager", e)


# =============================================================================
# TEST 6: Exception Classification
# =============================================================================

def test_exception_classification():
    """Test automatic exception classification."""
    test_section("TEST 6: Exception Classification")
    
    import sqlite3
    
    # Test 6a: SQLite IntegrityError
    try:
        exc = sqlite3.IntegrityError("UNIQUE constraint failed")
        error = classify_exception(exc)
        
        if error.category == ErrorCategory.DATABASE_ERROR and error.code == "INTEGRITY_ERROR":
            test_pass("SQLite IntegrityError classified correctly")
        else:
            test_fail("SQLite IntegrityError", f"Wrong classification: {error.category}, {error.code}")
    except Exception as e:
        test_fail("SQLite IntegrityError classification", e)
    
    # Test 6b: SQLite OperationalError
    try:
        exc = sqlite3.OperationalError("database is locked")
        error = classify_exception(exc)
        
        if error.category == ErrorCategory.DATABASE_ERROR and error.code == "DATABASE_ERROR":
            test_pass("SQLite OperationalError classified correctly")
        else:
            test_fail("SQLite OperationalError", f"Wrong classification: {error.category}, {error.code}")
    except Exception as e:
        test_fail("SQLite OperationalError classification", e)
    
    # Test 6c: Unknown exception defaults to internal error
    try:
        exc = RuntimeError("Something unexpected")
        error = classify_exception(exc)
        
        if error.category == ErrorCategory.INTERNAL_ERROR and error.code == "INTERNAL_ERROR":
            test_pass("Unknown exception defaults to internal error")
        else:
            test_fail("Unknown exception", f"Wrong classification: {error.category}, {error.code}")
    except Exception as e:
        test_fail("Unknown exception classification", e)


# =============================================================================
# TEST 7: MercuraException
# =============================================================================

def test_mercura_exception():
    """Test MercuraException wrapping."""
    test_section("TEST 7: MercuraException")
    
    try:
        original = ValueError("Original error")
        app_error = ai_service_unavailable("TestAI")
        
        exc = MercuraException(app_error, original)
        
        assert str(exc) == app_error.message, f"Exception message should be '{app_error.message}'"
        assert exc.app_error == app_error
        assert exc.original_exception == original
        
        # Test to_app_error returns the wrapped error
        returned_error = exc.to_app_error()
        assert returned_error == app_error
        
        test_pass("MercuraException wraps and unwraps correctly")
    except Exception as e:
        test_fail("MercuraException", e)


# =============================================================================
# MAIN
# =============================================================================

async def main():
    print("\n" + "=" * 70)
    print("  ERROR HANDLING FRAMEWORK TESTS")
    print("  Testing production-grade error handling scenarios")
    print("=" * 70)
    
    # Run all tests
    test_error_types()
    await test_retry_logic()
    await test_circuit_breaker()
    await test_timeout()
    await test_fallback()
    test_exception_classification()
    test_mercura_exception()
    
    # Print summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for r in results if r[0] == "PASS")
    failed = sum(1 for r in results if r[0] == "FAIL")
    
    print(f"\n  Total: {len(results)} tests")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    
    if failed > 0:
        print("\n  Failed tests:")
        for r in results:
            if r[0] == "FAIL":
                print(f"    - {r[1]}: {r[2]}")
    
    print("\n" + "=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
