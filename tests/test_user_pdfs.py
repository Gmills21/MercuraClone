#!/usr/bin/env python3
"""Quick test of PDF text extraction using available libraries"""

import sys
from pathlib import Path

def main():
    battery_pdf = Path("test_materials/Battery.pdf")
    automation_pdf = Path("test_materials/AutomationDirect-Summary.pdf")
    
    # Check files exist
    print("FILE CHECK:")
    print(f"  Battery.pdf: {battery_pdf.exists()} ({battery_pdf.stat().st_size / 1024:.1f} KB)")
    print(f"  AutomationDirect-Summary.pdf: {automation_pdf.exists()} ({automation_pdf.stat().st_size / 1024 / 1024:.1f} MB)")
    
    # Try to use our extraction engine
    print("\n" + "="*60)
    print("Testing with extraction engine (OCR fallback for PDFs)")
    print("="*60)
    
    # For PDFs, we need OCR or pdf extraction
    # Let's check what's available
    try:
        import pypdf
        print("pypdf is available")
        
        reader = pypdf.PdfReader(battery_pdf)
        print(f"\nBattery.pdf has {len(reader.pages)} pages")
        
        # Extract text from first page
        page_text = reader.pages[0].extract_text()
        print(f"Extracted {len(page_text)} characters from page 1")
        print("\nFirst 1000 characters:")
        print("-" * 60)
        print(page_text[:1000])
        print("-" * 60)
        
        # Test AutomationDirect
        print("\n" + "="*60)
        print("AutomationDirect-Summary.pdf")
        print("="*60)
        reader2 = pypdf.PdfReader(automation_pdf)
        print(f"Total pages: {len(reader2.pages)}")
        print("This is a large catalog - sampling first 3 pages...")
        
        for i in range(min(3, len(reader2.pages))):
            text = reader2.pages[i].extract_text()
            print(f"\nPage {i+1}: {len(text)} chars")
            if i == 0:
                print("Sample:", text[:500])
                
    except ImportError as e:
        print(f"Library not available: {e}")
        print("\nAttempting with available tools...")
        
        # Try using our existing services
        try:
            sys.path.insert(0, '.')
            from app.services.extraction_engine import extraction_engine
            
            print("Using extraction_engine...")
            # Note: extraction_engine expects images for OCR
            # For PDFs, we'd need to convert pages to images first
            print("PDF extraction requires OCR preprocessing (convert pages to images)")
            
        except Exception as e2:
            print(f"Extraction engine error: {e2}")
    
    print("\n" + "="*60)
    print("RECOMMENDATION")
    print("="*60)
    print("""
For these PDFs, you have options:

1. OCR Approach (Camera Capture workflow):
   - Convert PDF pages to images
   - Use extraction_engine with image_data
   - Best for scanned documents

2. Text Extraction (for native PDFs):
   - Install: pip install pypdf pdfplumber
   - Extract text directly
   - Better for digitally-created PDFs

3. Knowledge Base Ingestion:
   - Upload PDFs to /knowledge/ingest
   - Service extracts text and creates embeddings
   - Query with natural language
""")

if __name__ == "__main__":
    main()
