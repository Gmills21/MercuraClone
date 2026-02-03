
import asyncio
import os
import sys

# Add app to path
sys.path.append(os.getcwd())

from app.services.extraction_engine import extraction_engine

async def test_extraction():
    try:
        # Load ball valves text
        with open("test_materials/product_docs/ball_valves.txt", "r") as f:
            text = f.read()
        
        print("--- Input Text Preview ---")
        print(text[:200] + "...")
        print("\n--- Running Extraction ---")
        
        result = await extraction_engine.extract_from_text(text, source_type="email_test")
        
        print("\n--- Extraction Result ---")
        import json
        print(json.dumps(result, indent=2))
        
        # Check specific "Zero-Error" requirements
        data = result.get("structured_data", {})
        items = data.get("line_items", [])
        
        print("\n--- Stress Test Assessment ---")
        if not items:
            print("[FAIL] No items extracted.")
        else:
            print(f"[INFO] Extracted {len(items)} items.")
            # Check for specific item logic
            for item in items:
                print(f"- Qty: {item['quantity']}, Item: {item['item_name']}")
                
    except Exception as e:
        with open("extraction_log.txt", "a") as f:
            f.write(f"[CRITICAL FAIL] Execution error: {e}\n")
        print(f"[CRITICAL FAIL] Execution error: {e}")

if __name__ == "__main__":
    # Redirect stdout to file
    import sys
    sys.stdout = open("extraction_log.txt", "w")
    asyncio.run(test_extraction())
