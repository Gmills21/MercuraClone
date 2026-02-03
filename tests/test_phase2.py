import requests
import json

# Test extraction
url = 'http://127.0.0.1:8000/extract/'
rfq_text = '''Subject: RFQ - Pneumatic Cylinders

Hello,

We need pricing for:
- 5 NITRA pneumatic cylinders, 2-inch bore, double acting
- 10 cylinder mounting brackets
- 20 quick-connect fittings, 1/4 inch

Ship to: ABC Industries, Detroit, MI
Need by: February 28th

Contact: Sarah Williams
sarah.w@abcind.com
'''

data = {'text': rfq_text, 'source_type': 'email'}
response = requests.post(url, data=data)
result = response.json()

print('Extraction result:')
print(f"  Success: {result.get('success')}")
print(f"  Confidence: {result.get('confidence')}")
print(f"  Method: {result.get('extraction_method')}")
print()
print('Structured data:')
print(json.dumps(result.get('structured_data', {}), indent=2))
