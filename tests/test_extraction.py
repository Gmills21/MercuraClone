"""
Test script for Gemini extraction service.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.gemini_service import gemini_service
from dotenv import load_dotenv

load_dotenv()


async def test_text_extraction():
    """Test extraction from plain text."""
    print("\n" + "="*80)
    print("TEST 1: Text Extraction")
    print("="*80)
    
    sample_text = """
    INVOICE #INV-2024-001
    Date: 2024-01-10
    Vendor: Acme Supplies Inc.
    
    Line Items:
    1. Widget A (SKU: WID-001) - Qty: 10 @ $25.00 = $250.00
    2. Gadget B (SKU: GAD-002) - Qty: 5 @ $50.00 = $250.00
    3. Tool C (SKU: TOL-003) - Qty: 2 @ $100.00 = $200.00
    
    Subtotal: $700.00
    Tax (8%): $56.00
    Total: $756.00
    """
    
    result = await gemini_service.extract_from_text(
        text=sample_text,
        context="Test invoice extraction"
    )
    
    print(f"\nSuccess: {result.success}")
    print(f"Confidence: {result.confidence_score}")
    print(f"Processing Time: {result.processing_time_ms}ms")
    print(f"Items Extracted: {len(result.line_items)}")
    
    if result.success:
        print("\nExtracted Items:")
        for i, item in enumerate(result.line_items, 1):
            print(f"\n  Item {i}:")
            print(f"    Name: {item.get('item_name')}")
            print(f"    SKU: {item.get('sku')}")
            print(f"    Quantity: {item.get('quantity')}")
            print(f"    Unit Price: ${item.get('unit_price')}")
            print(f"    Total: ${item.get('total_price')}")
    else:
        print(f"\nError: {result.error}")


async def test_purchase_order():
    """Test extraction from purchase order."""
    print("\n" + "="*80)
    print("TEST 2: Purchase Order Extraction")
    print("="*80)
    
    po_text = """
    PURCHASE ORDER
    PO Number: PO-2024-0042
    Date: January 10, 2024
    Supplier: Tech Components Ltd.
    
    Items Ordered:
    
    Part Number: CPU-I9-13900K
    Description: Intel Core i9-13900K Processor
    Quantity: 25 units
    Unit Price: $589.99
    Extended Price: $14,749.75
    
    Part Number: RAM-DDR5-32GB
    Description: 32GB DDR5 RAM Module
    Quantity: 50 units
    Unit Price: $149.99
    Extended Price: $7,499.50
    
    Part Number: SSD-2TB-NVME
    Description: 2TB NVMe SSD
    Quantity: 30 units
    Unit Price: $199.99
    Extended Price: $5,999.70
    
    Order Total: $28,248.95
    """
    
    result = await gemini_service.extract_from_text(
        text=po_text,
        context="Purchase order for computer components"
    )
    
    print(f"\nSuccess: {result.success}")
    print(f"Confidence: {result.confidence_score}")
    print(f"Items Extracted: {len(result.line_items)}")
    
    if result.success:
        print("\nExtracted Items:")
        for i, item in enumerate(result.line_items, 1):
            print(f"\n  Item {i}:")
            print(f"    Name: {item.get('item_name')}")
            print(f"    SKU: {item.get('sku')}")
            print(f"    Quantity: {item.get('quantity')}")
            print(f"    Unit Price: ${item.get('unit_price')}")
            print(f"    Total: ${item.get('total_price')}")


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("MERCURA - Gemini Extraction Service Tests")
    print("="*80)
    
    try:
        await test_text_extraction()
        await test_purchase_order()
        
        print("\n" + "="*80)
        print("All tests completed!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
