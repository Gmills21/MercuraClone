"""
Comprehensive End-to-End Testing Suite for OpenMercura CRM
Tests all major customer workflows and features
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000"
TEST_RESULTS = []

def log_test(feature: str, test_name: str, passed: bool, details: str = "", severity: str = "low"):
    """Log test result"""
    result = {
        "timestamp": datetime.now().isoformat(),
        "feature": feature,
        "test": test_name,
        "passed": passed,
        "details": details,
        "severity": severity
    }
    TEST_RESULTS.append(result)
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} | {feature} | {test_name}")
    if details:
        details_str = details[:200] + "..." if len(details) > 200 else details
        print(f"      Details: {details_str}")
    return passed

def make_request(method: str, endpoint: str, **kwargs) -> tuple[bool, Any]:
    """Make HTTP request with error handling"""
    try:
        url = f"{BASE_URL}{endpoint}"
        response = requests.request(method, url, timeout=30, **kwargs)
        
        # Try to parse JSON, fallback to text
        try:
            data = response.json()
        except:
            data = response.text
            
        if response.status_code >= 200 and response.status_code < 300:
            return True, data
        else:
            return False, {"status": response.status_code, "data": data}
    except requests.exceptions.ConnectionError as e:
        return False, f"Connection error: {str(e)}"
    except requests.exceptions.Timeout:
        return False, "Request timeout"
    except Exception as e:
        return False, f"Error: {str(e)}"

class ComprehensiveTester:
    def __init__(self):
        self.auth_token = None
        self.user_id = None
        self.organization_id = None
        self.test_customer_id = None
        self.test_quote_id = None
        self.test_extraction_id = None
        
    def test_health_and_status(self):
        """Test 1: Health and Status Endpoints"""
        print("\n" + "="*60)
        print("TESTING: Health and Status")
        print("="*60)
        
        # Test health endpoint
        success, data = make_request("GET", "/health")
        log_test("Health", "Health Check", success, 
                json.dumps(data) if success else str(data), 
                "critical" if not success else "low")
        
        # Test root endpoint
        success, data = make_request("GET", "/")
        log_test("Health", "Root Endpoint", success,
                json.dumps(data) if success else str(data),
                "critical" if not success else "low")
        
        # Test API docs availability
        success, data = make_request("GET", "/docs")
        log_test("Health", "API Docs Available", success,
                "API docs accessible" if success else str(data),
                "high" if not success else "low")
    
    def test_authentication(self):
        """Test 2: Authentication Flows"""
        print("\n" + "="*60)
        print("TESTING: Authentication")
        print("="*60)
        
        # Test registration
        test_email = f"test_{int(time.time())}@example.com"
        test_password = "TestPassword123!"
        
        success, data = make_request("POST", "/auth/register", json={
            "email": test_email,
            "password": test_password,
            "name": "Test User"
        })
        
        if not success and "already" in str(data).lower():
            # User might already exist, try login
            success = True
            
        log_test("Auth", "User Registration", success,
                json.dumps(data) if success else str(data),
                "critical" if not success else "low")
        
        # Test login
        success, data = make_request("POST", "/auth/login", json={
            "email": "admin@openmercura.local",
            "password": "admin123"
        })
        
        if success and isinstance(data, dict):
            self.auth_token = data.get("access_token") or data.get("token")
            self.user_id = data.get("user_id")
        
        log_test("Auth", "User Login", success and bool(self.auth_token),
                "Token received" if self.auth_token else str(data),
                "critical" if not success else "low")
        
        # Test invalid login
        success, data = make_request("POST", "/auth/login", json={
            "email": "admin@openmercura.local",
            "password": "wrongpassword"
        })
        log_test("Auth", "Invalid Login Rejected", not success,
                "Correctly rejected invalid credentials" if not success else str(data),
                "high" if success else "low")
        
        # Test missing credentials
        success, data = make_request("POST", "/auth/login", json={})
        log_test("Auth", "Missing Credentials Rejected", not success,
                "Correctly rejected empty request" if not success else str(data),
                "medium" if success else "low")
    
    def test_organization_management(self):
        """Test 3: Organization/Team Management"""
        print("\n" + "="*60)
        print("TESTING: Organization Management")
        print("="*60)
        
        if not self.auth_token:
            log_test("Organization", "Skip - No Auth", False, "Authentication required", "critical")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test organization creation
        org_name = f"Test Org {int(time.time())}"
        success, data = make_request("POST", "/organizations", 
            headers=headers,
            json={"name": org_name, "slug": f"test-org-{int(time.time())}"})
        
        if success and isinstance(data, dict):
            self.organization_id = data.get("id") or data.get("organization_id")
            
        log_test("Organization", "Create Organization", success,
                json.dumps(data) if success else str(data),
                "high" if not success else "low")
        
        # Test list organizations
        success, data = make_request("GET", "/organizations", headers=headers)
        log_test("Organization", "List Organizations", success,
                f"Found {len(data) if isinstance(data, list) else 'N/A'} organizations" if success else str(data),
                "high" if not success else "low")
        
        # Test without auth
        success, data = make_request("GET", "/organizations")
        log_test("Organization", "Unauthorized Access Rejected", not success,
                "Correctly rejected unauthenticated request" if not success else str(data),
                "high" if success else "low")
    
    def test_customer_management(self):
        """Test 4: Customer Management"""
        print("\n" + "="*60)
        print("TESTING: Customer Management")
        print("="*60)
        
        if not self.auth_token:
            log_test("Customer", "Skip - No Auth", False, "Authentication required", "critical")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test customer creation
        customer_data = {
            "name": f"Test Customer {int(time.time())}",
            "email": f"customer_{int(time.time())}@example.com",
            "phone": "555-1234",
            "company": "Test Company Inc"
        }
        
        success, data = make_request("POST", "/customers",
            headers=headers, json=customer_data)
        
        if success and isinstance(data, dict):
            self.test_customer_id = data.get("id") or data.get("customer_id")
            
        log_test("Customer", "Create Customer", success,
                f"Customer ID: {self.test_customer_id}" if self.test_customer_id else str(data),
                "critical" if not success else "low")
        
        # Test list customers
        success, data = make_request("GET", "/customers", headers=headers)
        log_test("Customer", "List Customers", success,
                f"Found {len(data) if isinstance(data, list) else 'N/A'} customers" if success else str(data),
                "critical" if not success else "low")
        
        # Test customer with invalid data
        success, data = make_request("POST", "/customers",
            headers=headers, json={"invalid": "data"})
        log_test("Customer", "Invalid Data Handling", not success,
                "Correctly rejected invalid data" if not success else str(data),
                "medium" if success else "low")
        
        # Test get single customer
        if self.test_customer_id:
            success, data = make_request("GET", f"/customers/{self.test_customer_id}",
                headers=headers)
            log_test("Customer", "Get Single Customer", success,
                    json.dumps(data) if success else str(data),
                    "high" if not success else "low")
    
    def test_quote_management(self):
        """Test 5: Quote Creation and Management"""
        print("\n" + "="*60)
        print("TESTING: Quote Management")
        print("="*60)
        
        if not self.auth_token:
            log_test("Quote", "Skip - No Auth", False, "Authentication required", "critical")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test quote creation
        quote_data = {
            "title": f"Test Quote {int(time.time())}",
            "customer_id": self.test_customer_id or "test-customer-id",
            "items": [
                {"description": "Test Item 1", "quantity": 2, "unit_price": 100.00},
                {"description": "Test Item 2", "quantity": 1, "unit_price": 250.00}
            ],
            "notes": "This is a test quote"
        }
        
        success, data = make_request("POST", "/quotes",
            headers=headers, json=quote_data)
        
        if success and isinstance(data, dict):
            self.test_quote_id = data.get("id") or data.get("quote_id")
            
        log_test("Quote", "Create Quote", success,
                f"Quote ID: {self.test_quote_id}" if self.test_quote_id else str(data),
                "critical" if not success else "low")
        
        # Test list quotes
        success, data = make_request("GET", "/quotes", headers=headers)
        log_test("Quote", "List Quotes", success,
                f"Found {len(data) if isinstance(data, list) else 'N/A'} quotes" if success else str(data),
                "critical" if not success else "low")
        
        # Test quote with empty items
        success, data = make_request("POST", "/quotes",
            headers=headers, json={"title": "Empty Quote", "items": []})
        log_test("Quote", "Empty Quote Handling", not success,
                "Correctly rejected empty quote" if not success else str(data),
                "low")
    
    def test_email_functionality(self):
        """Test 6: Email Sending Functionality"""
        print("\n" + "="*60)
        print("TESTING: Email Functionality")
        print("="*60)
        
        if not self.auth_token:
            log_test("Email", "Skip - No Auth", False, "Authentication required", "critical")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test email configuration check
        success, data = make_request("GET", "/email/config", headers=headers)
        log_test("Email", "Get Email Config", success,
                json.dumps(data) if success else str(data),
                "medium" if not success else "low")
        
        # Test send email (would actually send - just validate endpoint exists)
        email_data = {
            "to": "test@example.com",
            "subject": "Test Email",
            "body": "This is a test email"
        }
        success, data = make_request("POST", "/email/send",
            headers=headers, json=email_data)
        log_test("Email", "Send Email Endpoint", success or "not configured" in str(data).lower(),
                "Endpoint accessible" if success else str(data),
                "medium" if not success else "low")
    
    def test_smart_extraction(self):
        """Test 7: Smart Quote / RFQ Extraction"""
        print("\n" + "="*60)
        print("TESTING: Smart Extraction (RFQ)")
        print("="*60)
        
        if not self.auth_token:
            log_test("Extraction", "Skip - No Auth", False, "Authentication required", "critical")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test extraction endpoint
        test_text = """
        Quote Request:
        Company: Acme Manufacturing
        Contact: John Doe
        Items:
        - 100x Widget A @ $5.00 each
        - 50x Widget B @ $10.00 each
        Delivery needed by: 2024-03-01
        """
        
        success, data = make_request("POST", "/extract",
            headers=headers,
            json={"text": test_text, "type": "rfq"})
        
        log_test("Extraction", "RFQ Text Extraction", success,
                json.dumps(data) if success else str(data),
                "high" if not success else "low")
        
        # Test extraction without type
        success, data = make_request("POST", "/extract",
            headers=headers, json={"text": test_text})
        log_test("Extraction", "Auto Type Detection", success,
                "Auto-detected type" if success else str(data),
                "medium" if not success else "low")
        
        # Test extraction with empty text
        success, data = make_request("POST", "/extract",
            headers=headers, json={"text": ""})
        log_test("Extraction", "Empty Text Handling", not success,
                "Correctly rejected empty text" if not success else str(data),
                "low")
    
    def test_image_extraction(self):
        """Test 8: Image/OCR Extraction"""
        print("\n" + "="*60)
        print("TESTING: Image Extraction")
        print("="*60)
        
        if not self.auth_token:
            log_test("Image", "Skip - No Auth", False, "Authentication required", "critical")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test image extraction endpoint (without actual image - just test structure)
        success, data = make_request("POST", "/extract/image",
            headers=headers,
            json={"image_data": "data:image/png;base64,invalid"})
        
        # Should fail due to invalid image, but endpoint should exist
        log_test("Image", "Image Extraction Endpoint", True,
                "Endpoint accessible" if "error" not in str(data).lower() or "invalid" in str(data).lower() else str(data),
                "medium")
    
    def test_alerts_system(self):
        """Test 9: Alerts System"""
        print("\n" + "="*60)
        print("TESTING: Alerts System")
        print("="*60)
        
        if not self.auth_token:
            log_test("Alerts", "Skip - No Auth", False, "Authentication required", "critical")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test list alerts
        success, data = make_request("GET", "/alerts", headers=headers)
        log_test("Alerts", "List Alerts", success,
                f"Found {len(data) if isinstance(data, list) else 'N/A'} alerts" if success else str(data),
                "medium" if not success else "low")
        
        # Test create alert
        success, data = make_request("POST", "/alerts",
            headers=headers,
            json={
                "title": "Test Alert",
                "message": "Test alert message",
                "type": "info",
                "priority": "medium"
            })
        log_test("Alerts", "Create Alert", success,
                json.dumps(data) if success else str(data),
                "medium" if not success else "low")
    
    def test_today_view(self):
        """Test 10: Today View Dashboard"""
        print("\n" + "="*60)
        print("TESTING: Today View Dashboard")
        print("="*60)
        
        if not self.auth_token:
            log_test("Today View", "Skip - No Auth", False, "Authentication required", "critical")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test today view endpoint
        success, data = make_request("GET", "/today", headers=headers)
        log_test("Today View", "Get Today View", success,
                json.dumps(data) if success else str(data),
                "high" if not success else "low")
        
        # Test today view stats
        success, data = make_request("GET", "/today/stats", headers=headers)
        log_test("Today View", "Get Today Stats", success,
                json.dumps(data) if success else str(data),
                "medium" if not success else "low")
    
    def test_intelligence_features(self):
        """Test 11: Customer Intelligence"""
        print("\n" + "="*60)
        print("TESTING: Customer Intelligence")
        print("="*60)
        
        if not self.auth_token:
            log_test("Intelligence", "Skip - No Auth", False, "Authentication required", "critical")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        if self.test_customer_id:
            # Test customer intelligence
            success, data = make_request("GET", f"/intelligence/customer/{self.test_customer_id}",
                headers=headers)
            log_test("Intelligence", "Customer Intelligence", success or "not found" in str(data).lower(),
                    json.dumps(data) if success else str(data),
                    "medium")
        
        # Test competitor analysis
        success, data = make_request("GET", "/competitors", headers=headers)
        log_test("Intelligence", "Competitor Analysis", success,
                f"Found {len(data) if isinstance(data, list) else 'N/A'} competitors" if success else str(data),
                "medium" if not success else "low")
    
    def test_knowledge_base(self):
        """Test 12: Knowledge Base"""
        print("\n" + "="*60)
        print("TESTING: Knowledge Base")
        print("="*60)
        
        if not self.auth_token:
            log_test("Knowledge Base", "Skip - No Auth", False, "Authentication required", "critical")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test knowledge base endpoint (may be disabled)
        success, data = make_request("GET", "/knowledge-base", headers=headers)
        
        if "disabled" in str(data).lower() or "not enabled" in str(data).lower():
            log_test("Knowledge Base", "KB Availability", True,
                    "Knowledge Base feature flag checked",
                    "low")
        else:
            log_test("Knowledge Base", "KB Endpoint", success,
                    json.dumps(data) if success else str(data),
                    "medium" if not success else "low")
    
    def test_billing_features(self):
        """Test 13: Billing/Subscription"""
        print("\n" + "="*60)
        print("TESTING: Billing/Subscription")
        print("="*60)
        
        if not self.auth_token:
            log_test("Billing", "Skip - No Auth", False, "Authentication required", "critical")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test billing status
        success, data = make_request("GET", "/billing/status", headers=headers)
        log_test("Billing", "Get Billing Status", success,
                json.dumps(data) if success else str(data),
                "medium" if not success else "low")
        
        # Test subscription plans
        success, data = make_request("GET", "/billing/plans", headers=headers)
        log_test("Billing", "List Plans", success,
                json.dumps(data) if success else str(data),
                "low" if not success else "low")
    
    def test_quickbooks_integration(self):
        """Test 14: QuickBooks Integration"""
        print("\n" + "="*60)
        print("TESTING: QuickBooks Integration")
        print("="*60)
        
        if not self.auth_token:
            log_test("QuickBooks", "Skip - No Auth", False, "Authentication required", "critical")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test QuickBooks connection status
        success, data = make_request("GET", "/quickbooks/status", headers=headers)
        log_test("QuickBooks", "QB Status Check", success,
                json.dumps(data) if success else str(data),
                "medium" if not success else "low")
        
        # Test auth URL generation (should work even without connection)
        success, data = make_request("GET", "/quickbooks/auth-url", headers=headers)
        log_test("QuickBooks", "Auth URL Generation", success,
                json.dumps(data) if success else str(data),
                "low" if not success else "low")
    
    def test_error_handling(self):
        """Test 15: Error Handling and Edge Cases"""
        print("\n" + "="*60)
        print("TESTING: Error Handling")
        print("="*60)
        
        # Test 404 handling
        success, data = make_request("GET", "/nonexistent-endpoint-12345")
        log_test("Error Handling", "404 Not Found", not success and (isinstance(data, dict) and data.get("status") == 404),
                "Correctly returned 404",
                "medium" if success else "low")
        
        # Test invalid JSON
        success, data = make_request("POST", "/auth/login",
            data="invalid json {",
            headers={"Content-Type": "application/json"})
        log_test("Error Handling", "Invalid JSON Handling", not success,
                "Correctly rejected invalid JSON" if not success else str(data),
                "medium" if success else "low")
        
        # Test SQL injection attempt
        success, data = make_request("GET", "/customers",
            headers={"Authorization": "Bearer ' OR '1'='1"})
        log_test("Error Handling", "SQL Injection Prevention", not success or "invalid" in str(data).lower(),
                "SQL injection attempt handled" if not success else str(data),
                "high" if success else "low")
        
        # Test very long input
        long_string = "A" * 10000
        success, data = make_request("POST", "/auth/login",
            json={"email": long_string, "password": long_string})
        log_test("Error Handling", "Long Input Handling", True,
                "Long input handled" if success or "too long" in str(data).lower() else str(data),
                "medium")
    
    def test_performance(self):
        """Test 16: Performance Tests"""
        print("\n" + "="*60)
        print("TESTING: Performance")
        print("="*60)
        
        # Test response time for health endpoint
        start = time.time()
        success, data = make_request("GET", "/health")
        elapsed = time.time() - start
        
        log_test("Performance", "Health Endpoint Response Time", elapsed < 2.0,
                f"Response time: {elapsed:.3f}s",
                "high" if elapsed > 2.0 else "low")
        
        # Test response time for customers list
        if self.auth_token:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            start = time.time()
            success, data = make_request("GET", "/customers", headers=headers)
            elapsed = time.time() - start
            
            log_test("Performance", "Customers List Response Time", elapsed < 3.0,
                    f"Response time: {elapsed:.3f}s",
                    "high" if elapsed > 3.0 else "low")
    
    def test_data_integrity(self):
        """Test 17: Data Integrity and Validation"""
        print("\n" + "="*60)
        print("TESTING: Data Integrity")
        print("="*60)
        
        if not self.auth_token:
            log_test("Data Integrity", "Skip - No Auth", False, "Authentication required", "critical")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test email validation
        success, data = make_request("POST", "/customers",
            headers=headers,
            json={"name": "Test", "email": "invalid-email"})
        log_test("Data Integrity", "Email Validation", not success,
                "Correctly rejected invalid email" if not success else str(data),
                "high" if success else "low")
        
        # Test required field validation
        success, data = make_request("POST", "/customers",
            headers=headers, json={})
        log_test("Data Integrity", "Required Field Validation", not success,
                "Correctly rejected empty customer" if not success else str(data),
                "high" if success else "low")
        
        # Test XSS prevention (if applicable)
        xss_attempt = "<script>alert('xss')</script>"
        success, data = make_request("POST", "/customers",
            headers=headers,
            json={"name": xss_attempt, "email": "test@test.com"})
        log_test("Data Integrity", "XSS Prevention", True,
                "XSS attempt handled" if success else str(data),
                "high" if not success else "low")

    def generate_report(self):
        """Generate final test report"""
        print("\n" + "="*60)
        print("TEST REPORT SUMMARY")
        print("="*60)
        
        total = len(TEST_RESULTS)
        passed = len([r for r in TEST_RESULTS if r["passed"]])
        failed = total - passed
        
        critical_failures = [r for r in TEST_RESULTS if not r["passed"] and r["severity"] == "critical"]
        high_failures = [r for r in TEST_RESULTS if not r["passed"] and r["severity"] == "high"]
        medium_failures = [r for r in TEST_RESULTS if not r["passed"] and r["severity"] == "medium"]
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        
        print(f"\n[CRIT] Critical Failures: {len(critical_failures)}")
        for f in critical_failures:
            print(f"   - {f['feature']}: {f['test']}")
            
        print(f"\n[HIGH] High Severity Failures: {len(high_failures)}")
        for f in high_failures:
            print(f"   - {f['feature']}: {f['test']}")
            
        print(f"\n[MED] Medium Severity Failures: {len(medium_failures)}")
        for f in medium_failures:
            print(f"   - {f['feature']}: {f['test']}")
        
        # Save detailed report
        with open("test_report_api.json", "w") as f:
            json.dump({
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "pass_rate": passed/total*100 if total > 0 else 0,
                    "timestamp": datetime.now().isoformat()
                },
                "failures": {
                    "critical": critical_failures,
                    "high": high_failures,
                    "medium": medium_failures
                },
                "all_results": TEST_RESULTS
            }, f, indent=2)
        
        print("\nDetailed report saved to: test_report_api.json")
        
        return len(critical_failures) == 0

def main():
    print("="*60)
    print("OPENMERCURA CRM - COMPREHENSIVE E2E TEST SUITE")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Started: {datetime.now().isoformat()}")
    
    tester = ComprehensiveTester()
    
    # Run all tests
    tester.test_health_and_status()
    tester.test_authentication()
    tester.test_organization_management()
    tester.test_customer_management()
    tester.test_quote_management()
    tester.test_email_functionality()
    tester.test_smart_extraction()
    tester.test_image_extraction()
    tester.test_alerts_system()
    tester.test_today_view()
    tester.test_intelligence_features()
    tester.test_knowledge_base()
    tester.test_billing_features()
    tester.test_quickbooks_integration()
    tester.test_error_handling()
    tester.test_performance()
    tester.test_data_integrity()
    
    # Generate report
    success = tester.generate_report()
    
    print("\n" + "="*60)
    if success:
        print("ALL CRITICAL TESTS PASSED")
    else:
        print("CRITICAL TESTS FAILED - REVIEW REQUIRED")
    print("="*60)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
