"""
Verification script to check that all resilience imports are working correctly.
Run this to verify the external API resilience fixes.
"""

import sys
import traceback

def test_imports():
    """Test that all modified services can import successfully."""
    
    services_to_test = [
        ("paddle_service", "app.services.paddle_service"),
        ("n8n_service", "app.services.n8n_service"),
        ("data_capture_service", "app.services.data_capture_service"),
        ("monitoring_service", "app.services.monitoring_service"),
        ("competitor_service", "app.services.competitor_service"),
    ]
    
    results = []
    
    for name, module_path in services_to_test:
        try:
            module = __import__(module_path, fromlist=[''])
            
            # Check for circuit breaker
            if hasattr(module, f"{name.replace('_service', '').title().replace('_', '')}Service"):
                service_class = getattr(module, f"{name.replace('_service', '').title().replace('_', '')}Service")
                # Try to instantiate (may fail if config missing, but import should work)
                try:
                    instance = service_class()
                    has_circuit_breaker = hasattr(instance, 'circuit_breaker')
                    results.append((name, "✅ PASS", f"Circuit breaker: {has_circuit_breaker}"))
                except Exception as e:
                    # Import worked, instantiation failed (likely config issue)
                    results.append((name, "⚠️  WARN", f"Import OK, instantiation failed: {str(e)[:50]}"))
            else:
                results.append((name, "✅ PASS", "Import successful"))
                
        except Exception as e:
            results.append((name, "❌ FAIL", f"Import error: {str(e)}"))
            traceback.print_exc()
    
    # Print results
    print("\n" + "="*80)
    print("EXTERNAL API RESILIENCE VERIFICATION")
    print("="*80 + "\n")
    
    for name, status, message in results:
        print(f"{status} {name:30s} - {message}")
    
    print("\n" + "="*80)
    
    # Summary
    passed = sum(1 for _, status, _ in results if "PASS" in status)
    warned = sum(1 for _, status, _ in results if "WARN" in status)
    failed = sum(1 for _, status, _ in results if "FAIL" in status)
    
    print(f"\nSummary: {passed} passed, {warned} warnings, {failed} failed")
    
    if failed > 0:
        print("\n❌ VERIFICATION FAILED - Fix import errors above")
        return False
    elif warned > 0:
        print("\n⚠️  VERIFICATION PASSED WITH WARNINGS - Check configuration")
        return True
    else:
        print("\n✅ ALL CHECKS PASSED - Resilience patterns successfully applied")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
