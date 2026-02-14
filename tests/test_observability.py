#!/usr/bin/env python3
"""
Observability & Telemetry Tests

Tests all observability features:
1. Structured logging (JSON format)
2. Sentry error tracking
3. Performance monitoring (timing, metrics)
4. Request tracing
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.observability import (
    StructuredLogFormatter,
    PerformanceMetrics,
    timed_operation,
    timed,
    get_request_id,
    log_user_action,
    ObservabilityHealthChecker,
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
# TEST 1: Structured Logging
# =============================================================================

def test_structured_logging():
    """Test structured JSON logging formatter."""
    test_section("TEST 1: Structured Logging")
    
    # Test 1a: Log record formatting
    try:
        from loguru import logger
        from datetime import datetime
        
        # Create a mock record
        class MockRecord:
            def __init__(self):
                self.time = datetime.utcnow()
                self.level = type('Level', (), {'name': 'INFO'})()
                self.message = "Test message"
                self.file = type('File', (), {'path': '/test/file.py'})()
                self.line = 42
                self.function = "test_function"
                self.exception = None
                self.extra = {"user_id": "123", "action": "test"}
        
        record = MockRecord()
        formatted = StructuredLogFormatter.format_record(record.__dict__)
        
        # Verify it's valid JSON
        import json
        parsed = json.loads(formatted)
        
        assert "timestamp" in parsed
        assert "level" in parsed
        assert "message" in parsed
        assert "source" in parsed
        assert "context" in parsed
        assert parsed["context"]["user_id"] == "123"
        
        test_pass("JSON log record formatting")
    except Exception as e:
        test_fail("JSON log record formatting", e)
    
    # Test 1b: Log with exception
    try:
        class MockException:
            def __init__(self):
                self.type = ValueError
                self.value = ValueError("Test error")
                self.traceback = "Traceback line 1\nTraceback line 2"
        
        class MockRecordWithExc:
            def __init__(self):
                self.time = datetime.utcnow()
                self.level = type('Level', (), {'name': 'ERROR'})()
                self.message = "Error occurred"
                self.file = type('File', (), {'path': '/test/file.py'})()
                self.line = 50
                self.function = "error_function"
                self.exception = MockException()
                self.extra = {}
        
        record = MockRecordWithExc()
        formatted = StructuredLogFormatter.format_record(record.__dict__)
        parsed = json.loads(formatted)
        
        assert "exception" in parsed
        assert parsed["exception"]["type"] == "ValueError"
        
        test_pass("JSON log with exception")
    except Exception as e:
        test_fail("JSON log with exception", e)


# =============================================================================
# TEST 2: Performance Metrics
# =============================================================================

def test_performance_metrics():
    """Test performance metrics collection."""
    test_section("TEST 2: Performance Metrics")
    
    # Test 2a: Record and retrieve metrics
    try:
        metrics = PerformanceMetrics()
        metrics.max_samples = 100  # Small for testing
        
        # Record some values
        for i in range(10):
            metrics.record("api_request", 100.0 + i * 10, "ms")
        
        stats = metrics.get_stats("api_request")
        
        assert stats is not None
        assert stats["count"] == 10
        assert stats["min"] == 100.0
        assert stats["max"] == 190.0
        assert stats["unit"] == "ms"
        
        test_pass("Record and retrieve metrics")
    except Exception as e:
        test_fail("Record and retrieve metrics", e)
    
    # Test 2b: Percentile calculations
    try:
        metrics = PerformanceMetrics()
        
        # Record values 1-100
        for i in range(1, 101):
            metrics.record("test_metric", float(i), "ms")
        
        stats = metrics.get_stats("test_metric")
        
        # p50 should be ~50, p95 should be ~95, p99 should be ~99
        assert 45 <= stats["p50"] <= 55, f"p50 out of range: {stats['p50']}"
        assert 90 <= stats["p95"] <= 100, f"p95 out of range: {stats['p95']}"
        assert 95 <= stats["p99"] <= 100, f"p99 out of range: {stats['p99']}"
        
        test_pass("Percentile calculations")
    except Exception as e:
        test_fail("Percentile calculations", e)
    
    # Test 2c: Max samples limit
    try:
        metrics = PerformanceMetrics()
        metrics.max_samples = 10
        
        # Record more than max_samples
        for i in range(20):
            metrics.record("limited_metric", float(i), "ms")
        
        assert len(metrics.metrics["limited_metric"]) == 10
        
        # Should only have the last 10 values (10-19)
        values = [m["value"] for m in metrics.metrics["limited_metric"]]
        assert values[0] == 10.0
        assert values[-1] == 19.0
        
        test_pass("Max samples limit enforced")
    except Exception as e:
        test_fail("Max samples limit", e)


# =============================================================================
# TEST 3: Timed Operations
# =============================================================================

async def test_timed_operations():
    """Test timing context manager and decorator."""
    test_section("TEST 3: Timed Operations")
    
    # Test 3a: timed_operation context manager
    try:
        from app.utils.observability import performance_metrics as pm
        
        # Clear previous metrics
        pm.metrics = {}
        
        with timed_operation("test_operation", {"context": "value"}):
            await asyncio.sleep(0.05)  # 50ms
        
        stats = pm.get_stats("test_operation")
        
        assert stats is not None
        assert stats["count"] == 1
        assert stats["min"] >= 50  # Should be at least 50ms
        
        test_pass("timed_operation context manager")
    except Exception as e:
        test_fail("timed_operation context manager", e)
    
    # Test 3b: timed decorator (async)
    try:
        pm.metrics = {}
        
        @timed
        async def async_function():
            await asyncio.sleep(0.02)
            return "result"
        
        result = await async_function()
        
        # Metric should be recorded with module.name format
        # The actual module name will be the test file name
        found_metric = False
        for metric_name in pm.metrics.keys():
            if "async_function" in metric_name:
                stats = pm.get_stats(metric_name)
                found_metric = True
                break
        
        assert result == "result"
        assert found_metric, f"Metric not found. Available: {list(pm.metrics.keys())}"
        
        test_pass("timed decorator (async)")
    except Exception as e:
        test_fail("timed decorator (async)", e)
    
    # Test 3c: timed decorator (sync)
    try:
        pm.metrics = {}
        
        @timed
        def sync_function():
            time.sleep(0.01)
            return "sync_result"
        
        result = sync_function()
        
        # The actual module name will be the test file name
        found_metric = False
        for metric_name in pm.metrics.keys():
            if "sync_function" in metric_name:
                stats = pm.get_stats(metric_name)
                found_metric = True
                break
        
        assert result == "sync_result"
        assert found_metric, f"Metric not found. Available: {list(pm.metrics.keys())}"
        
        test_pass("timed decorator (sync)")
    except Exception as e:
        test_fail("timed decorator (sync)", e)


# =============================================================================
# TEST 4: Health Checks
# =============================================================================

def test_health_checks():
    """Test observability health checks."""
    test_section("TEST 4: Health Checks")
    
    # Test 4a: Observability health
    try:
        health = ObservabilityHealthChecker.get_health()
        
        assert "status" in health
        assert "timestamp" in health
        assert "observability" in health
        assert "performance" in health
        
        obs = health["observability"]
        assert "sentry_enabled" in obs
        assert "structured_logging" in obs
        assert "metrics_collected" in obs
        
        test_pass("Observability health check")
    except Exception as e:
        test_fail("Observability health check", e)


# =============================================================================
# TEST 5: Utility Functions
# =============================================================================

def test_utility_functions():
    """Test utility functions."""
    test_section("TEST 5: Utility Functions")
    
    # Test 5a: log_user_action
    try:
        # This should not raise any errors
        log_user_action("user_123", "test_action", {"detail": "value"})
        test_pass("log_user_action")
    except Exception as e:
        test_fail("log_user_action", e)


# =============================================================================
# MAIN
# =============================================================================

async def main():
    print("\n" + "=" * 70)
    print("  OBSERVABILITY & TELEMETRY TESTS")
    print("  Testing production-grade observability features")
    print("=" * 70)
    
    # Run all tests
    test_structured_logging()
    test_performance_metrics()
    await test_timed_operations()
    test_health_checks()
    test_utility_functions()
    
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
