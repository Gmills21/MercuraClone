"""
Gemini 1.5 Flash integration for data extraction.
"""

from app.config import settings
from app.models import ExtractionRequest, ExtractionResponse
import json
import base64
import time
import logging
from typing import Dict, Any, Optional
from app.errors import (
    AIServiceException,
    ai_service_unavailable,
    ai_extraction_failed
)

logger = logging.getLogger(__name__)

# Try to configure Gemini, but handle version mismatch gracefully
try:
    import google.generativeai as genai
    # Test if GenerativeModel exists (not in older versions)
    if not hasattr(genai, 'GenerativeModel'):
        raise ImportError("google-generativeai version too old. Need >=0.3.2")
    genai.configure(api_key=settings.gemini_api_key)
    GEMINI_AVAILABLE = True
except Exception as e:
    logger.warning(f"Gemini service unavailable: {e}")
    genai = None
    GEMINI_AVAILABLE = False


class GeminiService:
    """Service for extracting structured data using Gemini 1.5 Flash."""
    
    def __init__(self):
        """Initialize Gemini model."""
        if not GEMINI_AVAILABLE:
            raise AIServiceException(
                ai_service_unavailable(
                    provider="Gemini",
                    detail="google-generativeai library not installed or version too old. Need >=0.3.2"
                )
            )
        
        print(f"Gemini model from settings: {settings.gemini_model}")
        self.model = genai.GenerativeModel(model_name=settings.gemini_model)
        
        # Default extraction schema for invoices/purchase orders
        self.default_schema = {
            "line_items": [
                {
                    "item_name": "string",
                    "sku": "string",
                    "description": "string",
                    "quantity": "integer",
                    "unit_price": "float",
                    "total_price": "float"
                }
            ],
            "metadata": {
                "document_type": "string (invoice/purchase_order/catalog)",
                "document_number": "string",
                "date": "string (ISO format)",
                "deadline": "string (deadline or due date if found, ISO format)",
                "vendor": "string",
                "total_amount": "float",
                "currency": "string"
            }
        }
    
    def _build_extraction_prompt(
        self, 
        schema: Dict[str, Any],
        context: Optional[str] = None
    ) -> str:
        """Build the system prompt for extraction."""
        prompt = f"""You are a precise data extraction engine. Your task is to analyze documents and extract structured data.

CRITICAL INSTRUCTIONS:
1. Output ONLY valid JSON matching the exact schema provided below
2. Do not include any explanatory text, markdown formatting, or code blocks
3. If a field cannot be determined, use null
4. For currency values, extract only the numeric value (e.g., "$1,200.00" → 1200.00)
5. For dates, use ISO format (YYYY-MM-DD)
6. Be extremely accurate with numbers - double-check all calculations
7. If the document contains both body text and attachments, prioritize attachment data for line items

EXPECTED JSON SCHEMA:
{json.dumps(schema, indent=2)}

{f"ADDITIONAL CONTEXT: {context}" if context else ""}

Now analyze the provided document and return the extracted data as valid JSON:"""
        
        return prompt
    
    async def extract_from_text(
        self,
        text: str,
        schema: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None
    ) -> ExtractionResponse:
        """Extract data from plain text."""
        try:
            start_time = time.time()
            
            # Use default schema if none provided
            extraction_schema = schema or self.default_schema
            
            # Build prompt
            prompt = self._build_extraction_prompt(extraction_schema, context)
            full_prompt = f"{prompt}\n\nDOCUMENT TEXT:\n{text}"
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            
            # Parse JSON response
            raw_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.strip()
            
            extracted_data = json.loads(raw_text)
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            
            # Extract line items
            line_items = extracted_data.get('line_items', [])
            
            # Calculate confidence score (simplified - based on completeness)
            confidence = self._calculate_confidence(line_items)
            
            return ExtractionResponse(
                success=True,
                line_items=line_items,
                confidence_score=confidence,
                raw_response=raw_text,
                processing_time_ms=processing_time
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            raise AIServiceException(
                ai_extraction_failed(
                    provider="Gemini",
                    detail=f"Invalid JSON response: {str(e)}",
                    context=context
                ),
                original_exception=e
            )
        except Exception as e:
            logger.error(f"Extraction error: {e}")
            raise AIServiceException(
                ai_extraction_failed(
                    provider="Gemini",
                    detail=str(e),
                    context=context
                ),
                original_exception=e
            )
    
    async def extract_from_pdf(
        self,
        pdf_base64: str,
        schema: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None
    ) -> ExtractionResponse:
        """Extract data from PDF file."""
        try:
            start_time = time.time()
            
            # Use default schema if none provided
            extraction_schema = schema or self.default_schema
            
            # Build prompt
            prompt = self._build_extraction_prompt(extraction_schema, context)
            
            # Decode base64 PDF
            pdf_bytes = base64.b64decode(pdf_base64)
            
            # Upload file to Gemini
            file_part = {
                'mime_type': 'application/pdf',
                'data': pdf_bytes
            }
            
            # Generate response with PDF
            response = self.model.generate_content([prompt, file_part])
            
            # Parse JSON response
            raw_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.strip()
            
            extracted_data = json.loads(raw_text)
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            
            # Extract line items
            line_items = extracted_data.get('line_items', [])
            
            # Calculate confidence score
            confidence = self._calculate_confidence(line_items)
            
            return ExtractionResponse(
                success=True,
                line_items=line_items,
                confidence_score=confidence,
                raw_response=raw_text,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            raise AIServiceException(
                ai_extraction_failed(
                    provider="Gemini",
                    detail=f"PDF extraction failed: {str(e)}",
                    context=context
                ),
                original_exception=e
            )
    
    async def extract_from_image(
        self,
        image_base64: str,
        image_type: str,
        schema: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None
    ) -> ExtractionResponse:
        """Extract data from image file."""
        try:
            start_time = time.time()
            
            # Use default schema if none provided
            extraction_schema = schema or self.default_schema
            
            # Build prompt
            prompt = self._build_extraction_prompt(extraction_schema, context)
            
            # Decode base64 image
            image_bytes = base64.b64decode(image_base64)
            
            # Map image type to MIME type
            mime_types = {
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg'
            }
            
            mime_type = mime_types.get(image_type.lower(), 'image/png')
            
            # Upload file to Gemini
            file_part = {
                'mime_type': mime_type,
                'data': image_bytes
            }
            
            # Generate response with image
            response = self.model.generate_content([prompt, file_part])
            
            # Parse JSON response
            raw_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.strip()
            
            extracted_data = json.loads(raw_text)
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            
            # Extract line items
            line_items = extracted_data.get('line_items', [])
            
            # Calculate confidence score
            confidence = self._calculate_confidence(line_items)
            
            return ExtractionResponse(
                success=True,
                line_items=line_items,
                confidence_score=confidence,
                raw_response=raw_text,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Image extraction error: {e}")
            raise AIServiceException(
                ai_extraction_failed(
                    provider="Gemini",
                    detail=f"Image extraction failed: {str(e)}",
                    context=context
                ),
                original_exception=e
            )
    
    def _calculate_confidence(self, line_items: list) -> float:
        """Calculate confidence score based on data completeness."""
        if not line_items:
            return 0.0
        
        total_fields = 0
        filled_fields = 0
        
        required_fields = ['item_name', 'quantity', 'unit_price', 'total_price']
        
        for item in line_items:
            for field in required_fields:
                total_fields += 1
                if item.get(field) is not None:
                    filled_fields += 1
        
        if total_fields == 0:
            return 0.0
        
        return round(filled_fields / total_fields, 2)


# Global service instance (lazy init to handle import errors gracefully)
gemini_service = None
try:
    if GEMINI_AVAILABLE:
        gemini_service = GeminiService()
except Exception as e:
    logger.warning(f"Failed to initialize GeminiService: {e}")
