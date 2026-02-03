import asyncio
import os

# Test if OpenRouter client works
os.environ['OPENROUTER_API_KEY'] = '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'

from app.services.extraction_engine import extraction_engine

async def test_ai():
    print(f"Client initialized: {extraction_engine.client is not None}")
    print(f"API Key present: {bool(os.environ.get('OPENROUTER_API_KEY'))}")
    
    if extraction_engine.client:
        print("Testing AI extraction...")
        text = """Subject: RFQ for Valves

Need quote for:
- 25 ball valves, 2-inch stainless steel
- 10 gate valves, 3-inch carbon steel

Contact: John Smith, john@test.com"""
        
        result = await extraction_engine.extract_from_text(text, "email")
        print(f"\nExtraction method: {result.get('extraction_method')}")
        print(f"Confidence: {result.get('confidence')}")
        print(f"Customer: {result['structured_data'].get('customer_name')}")
        print(f"Items: {len(result['structured_data'].get('line_items', []))}")
        for item in result['structured_data'].get('line_items', []):
            print(f"  - {item['quantity']} x {item['item_name']}")
    else:
        print("Client not initialized - check OPENROUTER_API_KEY")

asyncio.run(test_ai())
