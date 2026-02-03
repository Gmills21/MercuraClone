import requests
import json

BASE_URL = 'http://127.0.0.1:8001'

# Test customer creation with detailed error
print("Testing Customer Creation...")
r = requests.post(f'{BASE_URL}/customers/', json={
    'name': 'Test Customer Inc',
    'email': 'test@example.com',
    'company': 'TestCo',
    'phone': '555-1234'
})
print(f'Status: {r.status_code}')
print(f'Response: {r.text}')

# Test intelligence endpoint
print("\nTesting Intelligence...")
r = requests.get(f'{BASE_URL}/intelligence/customers')
print(f'Status: {r.status_code}')
if r.status_code != 200:
    print(f'Error: {r.text}')
