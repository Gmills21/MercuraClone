#!/usr/bin/env python3
"""Test extraction from user-provided PDFs"""

import sys
from pathlib import Path

def test_pdf_extraction():
    test_dir = Path("test_materials")
    
    # Test Battery.pdf
    battery_pdf = test_dir / "Battery.pdf"
    automation_pdf = test_dir / "AutomationDirect-Summary.pdf"
    
    results = []
    
    # Try PyPDF2
    try:
        from PyPDF2 import PdfReader
        
        # Battery.pdf
        print("=" * 60)
        print("Testing Battery.pdf with PyPDF2")
        print("=" * 60)
        reader = PdfReader(battery_pdf)
        num_pages = len(reader.pages)
        print(f"Total pages: {num_pages}")
        
        # Extract first page
        if num_pages > 0:
            text = reader.pages[0].extract_text()
            print(f"\nFirst page text length: {len(text)} chars")
            print("\n--- SAMPLE (first 1000 chars) ---")
            print(text[:1000])
            print("--- END SAMPLE ---")
            results.append(("Battery.pdf", "PyPDF2", len(text) > 0, len(text)))
        
        # AutomationDirect - just check first few pages (it's huge)
        print("\n" + "=" * 60)
        print("Testing AutomationDirect-Summary.pdf with PyPDF2")
        print("=" * 60)
        reader2 = PdfReader(automation_pdf)
        num_pages2 = len(reader2.pages)
        print(f"Total pages: {num_pages2}")
        
        # Sample first 3 pages
        total_text = 0
        for i in range(min(3, num_pages2)):
            text = reader2.pages[i].extract_text()
            total_text += len(text)
            if i == 0:
                print(f"\nPage 1 sample (first 800 chars):")
                print(text[:800])
        
        print(f"\nTotal text from first 3 pages: {total_text} chars")
        results.append(("AutomationDirect-Summary.pdf", "PyPDF2", total_text > 0, total_text))
        
    except Exception as e:
        print(f"PyPDF2 Error: {e}")
        results.append(("Both", "PyPDF2", False, 0))
    
    # Try pdfplumber if available
    try:
        import pdfplumber
        print("\n" + "=" * 60)
        print("Testing with pdfplumber (often better extraction)")
        print("=" * 60)
        
        with pdfplumber.open(battery_pdf) as pdf:
            page = pdf.pages[0]
            text = page.extract_text()
            print(f"Battery.pdf page 1: {len(text)} chars")
            print("Sample:", text[:500])
            results.append(("Battery.pdf", "pdfplumber", len(text) > 0, len(text)))
            
    except ImportError:
        print("pdfplumber not installed, skipping")
    except Exception as e:
        print(f"pdfplumber error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    for filename, method, success, length in results:
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{filename} | {method} | {status} | {length} chars")
    
    return results

if __name__ == "__main__":
    test_pdf_extraction()
