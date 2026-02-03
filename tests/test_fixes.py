import requests
import json

# Test 1: Check extraction engine has client
print("=== Test 1: Extraction Engine Client ===")
from app.services.extraction_engine import extraction_engine
print(f"Client initialized: {extraction_engine.client is not None}")

# Test 2: Text extraction
print("\n=== Test 2: Text Extraction ===")
url = 'http://127.0.0.1:8000/extract/'
rfq_text = """Subject: RFQ for Valves

Need quote for:
- 25 ball valves, 2-inch stainless steel
- 10 gate valves, 3-inch carbon steel

Contact: John Smith, john@test.com"""

data = {'text': rfq_text, 'source_type': 'email'}
response = requests.post(url, data=data)
result = response.json()

print(f"Success: {result.get('success')}")
print(f"Method: {result.get('extraction_method')}")
print(f"Confidence: {result.get('confidence')}")
print(f"Items found: {len(result['structured_data'].get('line_items', []))}")

# Test 3: Create Quote
print("\n=== Test 3: Create Quote ===")
url = 'http://127.0.0.1:8000/extract/create-quote'
response = requests.post(url, data=data)
result = response.json()

print(f"Success: {result.get('success')}")
if 'quote_id' in result:
    print(f"Quote ID: {result['quote_id']}")
    print(f"Items in quote: {len(result['quote'].get('items', []))}")
else:
    print(f"Error: {result.get('detail', 'Unknown error')}")

print("\n=== All Tests Complete ===")
