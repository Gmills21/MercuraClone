import json

with open('api_test_results.json') as f:
    data = json.load(f)
    
print('='*60)
print('TEST SUMMARY')
print('='*60)
print(f"Total: {data['summary']['total']}")
print(f"Passed: {data['summary']['passed']}")
print(f"Failed: {data['summary']['failed']}")

print('\n--- All Tests ---')
for t in data['tests']:
    status = 'PASS' if t['success'] else 'FAIL'
    print(f"[{status}] {t['test']}: HTTP {t['status']}")
    if not t['success'] and 'response' in t:
        resp = t['response']
        if isinstance(resp, dict) and 'detail' in resp:
            print(f"      Detail: {resp['detail']}")
