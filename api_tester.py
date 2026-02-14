"""
OpenMercura CRM - Comprehensive Testing Report
Generated: 2026-02-14
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

class APITester:
    def __init__(self):
        self.results = []
        self.token = None
        
    def test(self, name, method, endpoint, expected_status=None, **kwargs):
        """Test an endpoint and record results"""
        url = f"{BASE_URL}{endpoint}"
        try:
            resp = requests.request(method, url, timeout=15, **kwargs)
            status = resp.status_code
            success = expected_status is None or status == expected_status
            
            # Try to get JSON
            try:
                data = resp.json()
            except:
                data = resp.text[:200]
                
            result = {
                "test": name,
                "endpoint": endpoint,
                "method": method,
                "status": status,
                "success": success,
                "response": data if isinstance(data, dict) else str(data)[:200]
            }
        except Exception as e:
            result = {
                "test": name,
                "endpoint": endpoint,
                "method": method,
                "status": 0,
                "success": False,
                "error": str(e)
            }
        
        self.results.append(result)
        status_str = "PASS" if result["success"] else "FAIL"
        print(f"[{status_str}] {name}: {result.get('status', 'ERR')}")
        return result
    
    def run_all_tests(self):
        print("="*60)
        print("OPENMERCURA CRM - API TESTING")
        print("="*60)
        
        # 1. Health & Status
        print("\n--- Health & Status ---")
        self.test("Health Check", "GET", "/health", 200)
        self.test("API Docs", "GET", "/docs", 200)
        self.test("OpenAPI Schema", "GET", "/openapi.json", 200)
        
        # 2. Authentication
        print("\n--- Authentication ---")
        login_result = self.test("Login (Admin)", "POST", "/auth/login", 200, 
            json={"email": "admin@openmercura.local", "password": "admin123"})
        
        if login_result["success"] and isinstance(login_result["response"], dict):
            self.token = login_result["response"].get("access_token")
        
        self.test("Login (Invalid)", "POST", "/auth/login", 401,
            json={"email": "admin@openmercura.local", "password": "wrongpass"})
        self.test("Login (Empty)", "POST", "/auth/login", 422, json={})
        
        # 3. Test with token
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            print(f"\n--- Authenticated Tests (Token: {self.token[:20]}...) ---")
        else:
            print("\n--- Skipping Authenticated Tests (No Token) ---")
        
        # Test routes that should work with token
        self.test("Get Current User", "GET", "/auth/me", 200, headers=headers)
        
        # These will fail due to auth inconsistency
        self.test("List Customers", "GET", "/customers", 200, headers=headers)
        self.test("List Quotes", "GET", "/quotes", 200, headers=headers)
        self.test("List Alerts", "GET", "/alerts", 200, headers=headers)
        
        # 4. Test organization routes
        self.test("List Organizations", "GET", "/organizations", 200, headers=headers)
        
        # 5. Test extraction endpoints
        self.test("Extract RFQ", "POST", "/extract", 200, headers=headers,
            json={"text": "Quote for 100 widgets at $5 each", "type": "rfq"})
        
        # 6. Test billing
        self.test("Billing Status", "GET", "/billing/status", 200, headers=headers)
        self.test("Billing Plans", "GET", "/billing/plans", 200, headers=headers)
        
        # 7. Test QuickBooks
        self.test("QB Status", "GET", "/quickbooks/status", 200, headers=headers)
        
        # 8. Test error handling
        self.test("404 Handler", "GET", "/nonexistent12345", 404)
        self.test("Method Not Allowed", "DELETE", "/health", 405)
        
        return self.results
    
    def generate_report(self):
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        total = len(self.results)
        passed = len([r for r in self.results if r["success"]])
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        
        print("\n--- Failed Tests ---")
        for r in self.results:
            if not r["success"]:
                print(f"  - {r['test']}: HTTP {r.get('status', 'ERR')}")
                if "response" in r:
                    resp = r["response"]
                    if isinstance(resp, dict) and "detail" in resp:
                        print(f"    Detail: {resp['detail']}")
        
        # Save report
        with open("api_test_results.json", "w") as f:
            json.dump({
                "summary": {"total": total, "passed": passed, "failed": failed},
                "tests": self.results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        print("\nDetailed results saved to: api_test_results.json")

if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()
    tester.generate_report()
