
import requests
import os
import sys

BASE_URL = "http://localhost:8000"
FILE_PATH = r"c:\Users\graha\MercuraClone\test_materials\NPC-Nitra-Pneumatic-Cylinders.pdf"

def main():
    print(f"Testing Knowledge Base Ingestion with {FILE_PATH}...")
    
    if not os.path.exists(FILE_PATH):
        print(f"Error: File not found at {FILE_PATH}")
        return

    # Step 1: Ingest
    url = f"{BASE_URL}/knowledge/ingest"
    try:
        files = {'file': open(FILE_PATH, 'rb')}
        data = {
            'doc_type': 'catalog',
            'supplier': 'Nitra',
            'notes': 'Test upload'
        }
        print(f"Uploading to {url}...")
        response = requests.post(url, files=files, data=data)
        
        print(f"Ingest Status Code: {response.status_code}")
        print(f"Ingest Response: {response.text}")
        
        if response.status_code != 200:
            print("Ingestion failed. Stopping test.")
            return

    except Exception as e:
        print(f"Exception during ingestion: {e}")
        return

    # Step 2: Query
    print("\nTesting Query: 'What is the pressure rating for Nitra cylinders?'")
    query_url = f"{BASE_URL}/knowledge/query"
    try:
        data = {
            'question': 'What is the pressure rating for Nitra cylinders?',
            'use_ai': True
        }
        response = requests.post(query_url, data=data)
        
        print(f"Query Status Code: {response.status_code}")
        try:
            print(f"Query Response: {response.json()}")
        except:
            print(f"Query Response (Raw): {response.text}")

    except Exception as e:
        print(f"Exception during query: {e}")

if __name__ == "__main__":
    main()
