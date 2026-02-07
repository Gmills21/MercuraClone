#!/usr/bin/env python3
"""
Test 2: Smart Quote Extraction - "Value Core" / Velocity Grade
Tests extraction from test_rfq.txt and ball_valves RFQ-style input.
"""
import time
import requests
import os

API_URL = "http://localhost:8000/extract/"
TEST_USER_ID = "3d4df718-47c3-4903-b09e-711090412204"

# Expected from test_rfq.txt
EXPECTED_ITEMS = [
    {"qty": 25, "desc_contains": "ball valve"},
    {"qty": 10, "desc_contains": "gate valve"},
    {"qty": 50, "desc_contains": "pipe fitting"},
    {"qty": 100, "desc_contains": ["pvc", "pipe"]},
]

def run_extraction(text: str, source_type: str = "email"):
    """Call extraction API and return result + elapsed time."""
    start = time.perf_counter()
    r = requests.post(
        API_URL,
        data={"text": text, "source_type": source_type},
        headers={"X-User-ID": TEST_USER_ID},
        timeout=60,
    )
    elapsed = time.perf_counter() - start
    r.raise_for_status()
    return r.json(), elapsed

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Test 1: test_rfq.txt (proper RFQ)
    rfq_path = os.path.join(project_root, "tests", "test_rfq.txt")
    with open(rfq_path) as f:
        rfq_text = f.read()
    
    print("=" * 60)
    print("TEST 2: Smart Quote Extraction - 'Value Core'")
    print("=" * 60)
    print("\n[1] Extracting from test_rfq.txt (RFQ format)...")
    
    try:
        result, elapsed = run_extraction(rfq_text, "email")
    except Exception as e:
        print(f"FAIL: {e}")
        return 1
    
    items = result.get("structured_data", {}).get("line_items", [])
    confidence = result.get("confidence", 0)
    
    print(f"   Time: {elapsed:.2f}s")
    print(f"   Confidence: {confidence:.2f}")
    print(f"   Line items extracted: {len(items)}")
    
    for i, item in enumerate(items):
        name = item.get("item_name", "")
        qty = item.get("quantity", 0)
        print(f"   - {qty}x {name[:60]}...")
    
    # Grade
    grade = "F"
    if elapsed < 30 and len(items) >= 4:
        qty_ok = len(items) >= 4 and all(
            item.get("quantity") == exp["qty"]
            for item, exp in zip(items[:4], EXPECTED_ITEMS)
        )
        if qty_ok and confidence >= 0.7:
            grade = "A"
        else:
            grade = "B"
    elif elapsed < 60 and len(items) >= 2:
        grade = "B"
    elif elapsed < 300 and len(items) >= 1:
        grade = "C"
    elif len(items) == 0:
        grade = "F"
    
    print(f"\n   GRADE: {grade}")
    print("\n[2] Extracting from ball_valves.txt (Spec Sheet - expect empty line_items)...")
    
    ball_path = os.path.join(project_root, "test_materials", "product_docs", "ball_valves.txt")
    with open(ball_path) as f:
        ball_text = f.read()
    
    try:
        result2, elapsed2 = run_extraction(ball_text, "document")
    except Exception as e:
        print(f"   Skip: {e}")
    else:
        items2 = result2.get("structured_data", {}).get("line_items", [])
        si = result2.get("structured_data", {}).get("special_instructions", "")
        print(f"   Time: {elapsed2:.2f}s")
        print(f"   Line items: {len(items2)} (expected 0 for spec sheet)")
        if si:
            print(f"   Note: {si[:80]}...")
    
    print("\n" + "=" * 60)
    return 0

if __name__ == "__main__":
    exit(main())
