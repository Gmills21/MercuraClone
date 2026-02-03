#!/usr/bin/env python3
"""
Phase 3 Testing - End-to-End API Testing
Simulates real customer journey through all features
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:8001"
results = []

def log_test(name, status, details=""):
    """Log test result"""
    results.append({"name": name, "status": status, "details": details})
    icon = "[PASS]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[INFO]"
    print(f"  {icon} {name}: {details}")

def test_health_check():
    """Test 1: API Health Check"""
    print("\n" + "="*60)
    print("TEST 1: API Health Check")
    print("="*60)
    try:
        r = requests.get(f"{BASE_URL}/", timeout=5)
        if r.status_code == 200:
            data = r.json()
            log_test("Root Endpoint", "PASS", f"Status: {data.get('status', 'unknown')}")
            log_test("QuickBooks Status", "INFO", f"Connected: {data.get('quickbooks_connected', False)}")
        else:
            log_test("Root Endpoint", "FAIL", f"Status: {r.status_code}")
    except Exception as e:
        log_test("Root Endpoint", "FAIL", str(e))

def test_auth():
    """Test 2: Authentication"""
    print("\n" + "="*60)
    print("TEST 2: Authentication")
    print("="*60)
    try:
        # Login with default credentials
        r = requests.post(f"{BASE_URL}/auth/login", json={
            "email": "admin@openmercura.local",
            "password": "admin123"
        })
        if r.status_code == 200:
            log_test("Login", "PASS", "Default admin credentials work")
        else:
            log_test("Login", "FAIL", f"Status: {r.status_code}")
    except Exception as e:
        log_test("Login", "FAIL", str(e))

def test_customers():
    """Test 3: Customer Management"""
    print("\n" + "="*60)
    print("TEST 3: Customer Management")
    print("="*60)
    try:
        # List customers
        r = requests.get(f"{BASE_URL}/customers/")
        if r.status_code == 200:
            customers = r.json()
            log_test("List Customers", "PASS", f"Found {len(customers)} customers")
        else:
            log_test("List Customers", "FAIL", f"Status: {r.status_code}")
        
        # Create test customer
        r = requests.post(f"{BASE_URL}/customers/", json={
            "name": "Test Customer Inc",
            "email": "test@example.com",
            "company": "TestCo",
            "phone": "555-1234"
        })
        if r.status_code == 200:
            customer = r.json()
            log_test("Create Customer", "PASS", f"ID: {customer.get('id')}")
        else:
            log_test("Create Customer", "FAIL", f"Status: {r.status_code}")
            
    except Exception as e:
        log_test("Customer Management", "FAIL", str(e))

def test_products():
    """Test 4: Product Management"""
    print("\n" + "="*60)
    print("TEST 4: Product Management")
    print("="*60)
    try:
        # List products
        r = requests.get(f"{BASE_URL}/products/")
        if r.status_code == 200:
            products = r.json()
            log_test("List Products", "PASS", f"Found {len(products)} products")
        else:
            log_test("List Products", "FAIL", f"Status: {r.status_code}")
        
        # Create test product
        r = requests.post(f"{BASE_URL}/products/", json={
            "sku": "TEST-001",
            "name": "Test Ball Valve",
            "description": "2-inch stainless steel ball valve",
            "price": 45.99,
            "cost": 25.00,
            "category": "valves"
        })
        if r.status_code == 200:
            product = r.json()
            log_test("Create Product", "PASS", f"SKU: {product.get('sku')}")
        else:
            log_test("Create Product", "FAIL", f"Status: {r.status_code}")
            
    except Exception as e:
        log_test("Product Management", "FAIL", str(e))

def test_quotes():
    """Test 5: Quote Creation"""
    print("\n" + "="*60)
    print("TEST 5: Quote Creation & Management")
    print("="*60)
    try:
        # List quotes
        r = requests.get(f"{BASE_URL}/quotes/")
        if r.status_code == 200:
            quotes = r.json()
            log_test("List Quotes", "PASS", f"Found {len(quotes)} quotes")
        else:
            log_test("List Quotes", "FAIL", f"Status: {r.status_code}")
        
        # Create test quote - get a real customer_id first
        cust_r = requests.get(f"{BASE_URL}/customers/")
        if cust_r.status_code == 200:
            customers = cust_r.json()
            if customers:
                customer_id = customers[0].get('id', 'cust-001')
            else:
                customer_id = 'cust-001'
        else:
            customer_id = 'cust-001'
        
        r = requests.post(f"{BASE_URL}/quotes/", json={
            "customer_id": customer_id,
            "items": [
                {"sku": "TEST-001", "quantity": 5, "unit_price": 45.99}
            ],
            "notes": "Test quote for Phase 3 testing"
        })
        if r.status_code == 200:
            quote = r.json()
            log_test("Create Quote", "PASS", f"ID: {quote.get('id')}")
        else:
            log_test("Create Quote", "FAIL", f"Status: {r.status_code} - {r.text[:100]}")
            
    except Exception as e:
        log_test("Quote Management", "FAIL", str(e))

def test_smart_quote_extraction():
    """Test 6: Smart Quote Extraction (AI RFQ parsing)"""
    print("\n" + "="*60)
    print("TEST 6: Smart Quote Extraction")
    print("="*60)
    
    rfq_text = """Subject: Request for Quotation: Ball Valves Needed

Hello Supplier,

My name is John Smith from ABC Manufacturing. I am reaching out to request a 
quotation for the following items:

- 10x 2-inch stainless steel ball valves (model BV-200-SS)
- 5x 3-inch carbon steel gate valves (model GV-300-CS)
- 20x 1-inch brass check valves (model CV-100-BR)

Please include your best pricing breakdown, delivery time, and payment terms.
Could you send your quotation by March 15th?

Thank you,
John Smith
Purchasing Manager
ABC Manufacturing
john.smith@abc-mfg.com"""

    try:
        r = requests.post(f"{BASE_URL}/extract/", data={
            "text": rfq_text,
            "source_type": "email"
        })
        if r.status_code == 200:
            result = r.json()
            if result.get('success'):
                data = result.get('structured_data', {})
                items = data.get('line_items', [])
                log_test("RFQ Extraction", "PASS", f"Found {len(items)} line items")
                log_test("Customer Detection", "INFO", f"Customer: {data.get('customer_name', 'N/A')}")
            else:
                log_test("RFQ Extraction", "FAIL", "Extraction returned no success")
        else:
            log_test("RFQ Extraction", "FAIL", f"Status: {r.status_code}")
    except Exception as e:
        log_test("RFQ Extraction", "FAIL", str(e))

def test_alerts():
    """Test 7: Smart Alerts"""
    print("\n" + "="*60)
    print("TEST 7: Smart Alerts")
    print("="*60)
    try:
        r = requests.get(f"{BASE_URL}/alerts/")
        if r.status_code == 200:
            alerts = r.json()
            log_test("List Alerts", "PASS", f"Found {len(alerts)} alerts")
        else:
            log_test("List Alerts", "FAIL", f"Status: {r.status_code}")
    except Exception as e:
        log_test("Alerts", "FAIL", str(e))

def test_onboarding():
    """Test 8: Onboarding Status"""
    print("\n" + "="*60)
    print("TEST 8: Onboarding Status")
    print("="*60)
    try:
        r = requests.get(f"{BASE_URL}/onboarding/checklist")
        if r.status_code == 200:
            status = r.json()
            progress = status.get('progress', {})
            completed = sum(1 for v in progress.values() if v)
            total = len(progress)
            log_test("Onboarding Checklist", "PASS", f"{completed}/{total} steps complete")
        else:
            log_test("Onboarding Checklist", "FAIL", f"Status: {r.status_code}")
    except Exception as e:
        log_test("Onboarding", "FAIL", str(e))

def test_intelligence():
    """Test 9: Customer Intelligence"""
    print("\n" + "="*60)
    print("TEST 9: Customer Intelligence")
    print("="*60)
    try:
        r = requests.get(f"{BASE_URL}/intelligence/customers")
        if r.status_code == 200:
            data = r.json()
            categories = data.get('categories', {})
            total = sum(len(v) for v in categories.values())
            log_test("Intelligence List", "PASS", f"{total} customers categorized")
        else:
            log_test("Intelligence List", "FAIL", f"Status: {r.status_code} - {r.text[:100]}")
    except Exception as e:
        log_test("Intelligence", "FAIL", str(e))

def test_impact():
    """Test 10: Business Impact"""
    print("\n" + "="*60)
    print("TEST 10: Business Impact")
    print("="*60)
    try:
        r = requests.get(f"{BASE_URL}/impact/time-summary")
        if r.status_code == 200:
            data = r.json()
            time_saved = data.get('total_hours_saved', 0)
            log_test("Business Impact (Time)", "PASS", f"{time_saved} hours saved tracked")
        else:
            log_test("Business Impact (Time)", "FAIL", f"Status: {r.status_code}")
        
        r = requests.get(f"{BASE_URL}/impact/quote-efficiency")
        if r.status_code == 200:
            data = r.json()
            quotes = data.get('quotes_created', 0)
            log_test("Business Impact (Quotes)", "PASS", f"{quotes} quotes tracked")
        else:
            log_test("Business Impact (Quotes)", "FAIL", f"Status: {r.status_code}")
            
    except Exception as e:
        log_test("Business Impact", "FAIL", str(e))

def print_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("PHASE 3 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results if r['status'] == 'PASS')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    info = sum(1 for r in results if r['status'] == 'INFO')
    
    print(f"\n  Total Tests: {len(results)}")
    print(f"  [PASS] Passed: {passed}")
    print(f"  [FAIL] Failed: {failed}")
    print(f"  [INFO] Info: {info}")
    
    if failed > 0:
        print("\n  Failed Tests:")
        for r in results:
            if r['status'] == 'FAIL':
                print(f"    - {r['name']}: {r['details']}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("OPENMERCURA CRM - PHASE 3 TESTING")
    print("Real Customer Journey Validation")
    print("="*60)
    print(f"\nTesting against: {BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_health_check()
    test_auth()
    test_customers()
    test_products()
    test_quotes()
    test_smart_quote_extraction()
    test_alerts()
    test_onboarding()
    test_intelligence()
    test_impact()
    
    print_summary()
