"""
Image Extraction Service
Extract RFQ data from uploaded images (photos of emails, handwritten notes, etc.)
Uses OCR and AI to convert images to structured quote data
"""

import os
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional, List
import base64
import io

from PIL import Image
import pytesseract
from loguru import logger

# Try to import OpenRouter for AI extraction
try:
    from openai import AsyncOpenAI
    OPENROUTER_AVAILABLE = True
except ImportError:
    OPENROUTER_AVAILABLE = False

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")


class ImageExtractionService:
    """Extract RFQ data from images using OCR + AI."""
    
    def __init__(self):
        from app.deepseek_service import get_deepseek_service
        self.ai = get_deepseek_service()
    
    async def extract_from_image(self, image_data: bytes, filename: str = "image.jpg") -> Dict[str, Any]:
        """
        Extract RFQ data from an image.
        
        Flow:
        1. Save/process image
        2. Run OCR to extract text
        3. Use AI to parse structured data from OCR text
        4. Return formatted RFQ data
        """
        try:
            # Step 1: Process image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Step 2: Run OCR
            logger.info("Running OCR on image...")
            ocr_text = pytesseract.image_to_string(image)
            
            if not ocr_text.strip():
                return {
                    "success": False,
                    "error": "No text found in image. Try a clearer photo.",
                    "ocr_text": ""
                }
            
            # Step 3: Use AI to parse structured data
            structured_data = await self._parse_with_ai(ocr_text)
            
            return {
                "success": True,
                "ocr_text": ocr_text,
                "extracted_data": structured_data,
                "confidence": structured_data.get("confidence", 0.5)
            }
            
        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "ocr_text": ""
            }
    
    async def _parse_with_ai(self, ocr_text: str) -> Dict[str, Any]:
        """Use AI to parse structured RFQ data from OCR text."""
        schema = {
            "customer_name": "string",
            "contact_email": "string",
            "contact_phone": "string",
            "line_items": [
                {
                    "item_name": "string",
                    "quantity": "number",
                    "sku": "string",
                    "notes": "string"
                }
            ],
            "delivery_date": "string",
            "delivery_location": "string",
            "special_instructions": "string",
            "confidence": "number"
        }
        
        instructions = "Extract RFQ (Request for Quote) information from this OCR text."
        
        result = await self.ai.extract_structured_data(ocr_text, schema, instructions)
        
        if result["success"]:
            return result["data"]
        else:
            logger.warning(f"AI parsing failed, using basic extraction: {result.get('error')}")
            return self._basic_extraction(ocr_text)
    
    def _basic_extraction(self, ocr_text: str) -> Dict[str, Any]:
        """Basic extraction without AI - regex-based fallback."""
        import re
        
        lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
        
        # Try to find quantities and items
        line_items = []
        for line in lines:
            # Look for patterns like "25x Widget" or "Widget - 25 units"
            qty_match = re.search(r'(\d+)\s*(x|pcs|units|ea|each)?', line, re.IGNORECASE)
            if qty_match:
                qty = int(qty_match.group(1))
                # Remove quantity from line to get item name
                item_name = re.sub(r'\d+\s*(x|pcs|units|ea|each)?[.:\s]*', '', line, flags=re.IGNORECASE).strip()
                if item_name and len(item_name) > 2:
                    line_items.append({
                        "item_name": item_name,
                        "quantity": qty,
                        "sku": None,
                        "notes": None
                    })
        
        # Try to find email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', ocr_text)
        email = email_match.group(0) if email_match else None
        
        # Try to find phone
        phone_match = re.search(r'(\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', ocr_text)
        phone = phone_match.group(0) if phone_match else None
        
        return {
            "customer_name": lines[0] if lines else None,
            "contact_email": email,
            "contact_phone": phone,
            "line_items": line_items[:10],  # Limit to 10 items
            "delivery_date": None,
            "delivery_location": None,
            "special_instructions": None,
            "confidence": 0.4 if line_items else 0.2
        }
    
    def preprocess_image(self, image_data: bytes) -> bytes:
        """
        Preprocess image for better OCR.
        - Resize if too large
        - Convert to grayscale
        - Enhance contrast
        """
        image = Image.open(io.BytesIO(image_data))
        
        # Resize if too large (max 2000px on longest side)
        max_size = 2000
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Enhance contrast
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Save to bytes
        output = io.BytesIO()
        image.save(output, format='PNG')
        return output.getvalue()


# Global instance
image_extraction_service = ImageExtractionService()
