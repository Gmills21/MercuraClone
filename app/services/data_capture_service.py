"""
Intelligent Data Capture Service for OpenMercura
Free implementation using DeepSeek/OpenRouter API
"""

import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
from app.config import settings
from app.database import db
from app.models import ExtractionResponse, LineItem

logger = logging.getLogger(__name__)


class DataCaptureService:
    """Service for capturing and structuring data from unstructured text."""
    
    def __init__(self):
        self.api_key = settings.openrouter_api_key or settings.deepseek_api_key
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = settings.llm_model or "deepseek/deepseek-chat"
        
    def _build_extraction_prompt(self, text: str, schema: Dict[str, Any]) -> str:
        """Build the prompt for data extraction."""
        schema_str = json.dumps(schema, indent=2)
        
        return f"""You are a precise data extraction engine. Extract structured data from the provided text.

EXTRACTION RULES:
1. Output ONLY valid JSON matching the exact schema provided
2. Do not include markdown formatting, code blocks, or explanatory text
3. Use null for fields that cannot be determined
4. For currency, extract numeric values only (e.g., "$1,200" → 1200.00)
5. Use ISO format for dates (YYYY-MM-DD)
6. Verify all calculations are accurate

EXPECTED JSON SCHEMA:
{schema_str}

DOCUMENT TEXT TO ANALYZE:
{text}

Extract the data and return ONLY valid JSON:"""

    async def extract_from_text(
        self,
        text: str,
        schema: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        source: str = "manual"
    ) -> ExtractionResponse:
        """
        Extract structured data from unstructured text.
        
        Args:
            text: Raw text to analyze
            schema: Optional custom extraction schema
            user_id: User ID for saving to CRM
            source: Source of the data (email, csv, manual, etc.)
            
        Returns:
            ExtractionResponse with extracted line items
        """
        start_time = time.time()
        
        # Default schema for line items
        default_schema = {
            "line_items": [
                {
                    "item_name": "string - Product/service name",
                    "sku": "string - Product code/SKU",
                    "description": "string - Detailed description",
                    "quantity": "integer - Quantity requested",
                    "unit_price": "number - Price per unit",
                    "total_price": "number - Total line amount"
                }
            ],
            "metadata": {
                "document_type": "string (rfq/invoice/purchase_order/catalog)",
                "document_number": "string - Reference number",
                "date": "string - Document date (YYYY-MM-DD)",
                "vendor": "string - Vendor/customer name",
                "total_amount": "number - Grand total",
                "currency": "string - Currency code (USD/EUR/etc)"
            }
        }
        
        extraction_schema = schema or default_schema
        prompt = self._build_extraction_prompt(text, extraction_schema)
        
        try:
            # Call OpenRouter/DeepSeek API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://openmercura.local",
                "X-Title": "OpenMercura"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a precise data extraction engine. Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 4000
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                raw_text = data["choices"][0]["message"]["content"]
                
                # Clean up the response
                raw_text = self._clean_json_response(raw_text)
                
                # Parse JSON
                extracted_data = json.loads(raw_text)
                
                # Calculate metrics
                processing_time = int((time.time() - start_time) * 1000)
                line_items = extracted_data.get("line_items", [])
                confidence = self._calculate_confidence(line_items)
                
                # Save to CRM if user_id provided
                if user_id:
                    await self._save_to_crm(
                        user_id=user_id,
                        line_items=line_items,
                        metadata=extracted_data.get("metadata", {}),
                        source=source,
                        confidence=confidence
                    )
                
                return ExtractionResponse(
                    success=True,
                    line_items=line_items,
                    confidence_score=confidence,
                    raw_response=raw_text,
                    processing_time_ms=processing_time
                )
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return ExtractionResponse(
                success=False,
                line_items=[],
                confidence_score=0.0,
                error=f"Invalid JSON response: {str(e)}"
            )
        except httpx.HTTPError as e:
            logger.error(f"API error: {e}")
            return ExtractionResponse(
                success=False,
                line_items=[],
                confidence_score=0.0,
                error=f"API request failed: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Extraction error: {e}")
            return ExtractionResponse(
                success=False,
                line_items=[],
                confidence_score=0.0,
                error=str(e)
            )
    
    async def extract_from_csv(
        self,
        csv_content: str,
        user_id: Optional[str] = None,
        mapping: Optional[Dict[str, str]] = None
    ) -> ExtractionResponse:
        """
        Extract data from CSV content.
        
        Args:
            csv_content: Raw CSV string
            user_id: User ID for saving to CRM
            mapping: Optional column mapping {csv_column: target_field}
            
        Returns:
            ExtractionResponse with extracted line items
        """
        try:
            lines = csv_content.strip().split('\n')
            if len(lines) < 2:
                return ExtractionResponse(
                    success=False,
                    line_items=[],
                    confidence_score=0.0,
                    error="CSV must have at least a header row and one data row"
                )
            
            # Parse CSV
            headers = lines[0].split(',')
            line_items = []
            
            for line in lines[1:]:
                values = line.split(',')
                item = {}
                
                for i, header in enumerate(headers):
                    header_clean = header.strip().lower()
                    value = values[i].strip() if i < len(values) else ""
                    
                    # Apply mapping if provided
                    if mapping and header_clean in mapping:
                        target_field = mapping[header_clean]
                        item[target_field] = value
                    else:
                        # Auto-map common fields
                        if any(x in header_clean for x in ['item', 'product', 'name']):
                            item['item_name'] = value
                        elif 'sku' in header_clean or 'code' in header_clean:
                            item['sku'] = value
                        elif 'desc' in header_clean:
                            item['description'] = value
                        elif 'qty' in header_clean or 'quantity' in header_clean:
                            item['quantity'] = int(value) if value.isdigit() else 1
                        elif 'price' in header_clean and 'unit' in header_clean:
                            item['unit_price'] = float(value.replace(',', '').replace('$', '')) if value else 0.0
                        elif 'total' in header_clean:
                            item['total_price'] = float(value.replace(',', '').replace('$', '')) if value else 0.0
                
                if item.get('item_name') or item.get('sku'):
                    line_items.append(item)
            
            # Calculate confidence
            confidence = self._calculate_confidence(line_items)
            
            # Save to CRM
            if user_id:
                await self._save_to_crm(
                    user_id=user_id,
                    line_items=line_items,
                    metadata={"source_type": "csv", "record_count": len(line_items)},
                    source="csv_upload",
                    confidence=confidence
                )
            
            return ExtractionResponse(
                success=True,
                line_items=line_items,
                confidence_score=confidence,
                processing_time_ms=0
            )
            
        except Exception as e:
            logger.error(f"CSV extraction error: {e}")
            return ExtractionResponse(
                success=False,
                line_items=[],
                confidence_score=0.0,
                error=str(e)
            )
    
    async def _save_to_crm(
        self,
        user_id: str,
        line_items: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        source: str,
        confidence: float
    ):
        """Save extracted data to CRM database."""
        try:
            # Create a data capture record
            capture_record = {
                "user_id": user_id,
                "source": source,
                "document_type": metadata.get("document_type", "unknown"),
                "document_number": metadata.get("document_number"),
                "vendor": metadata.get("vendor"),
                "total_amount": metadata.get("total_amount"),
                "currency": metadata.get("currency", "USD"),
                "confidence_score": confidence,
                "extracted_at": datetime.utcnow().isoformat(),
                "line_item_count": len(line_items)
            }
            
            # Save to database (implement in database.py)
            await db.save_crm_capture(capture_record, line_items)
            logger.info(f"Saved {len(line_items)} line items to CRM for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to save to CRM: {e}")
            # Don't fail the extraction if CRM save fails
    
    def _clean_json_response(self, text: str) -> str:
        """Clean up JSON response from LLM."""
        text = text.strip()
        
        # Remove markdown code blocks
        if text.startswith("```"):
            lines = text.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = '\n'.join(lines)
            
        # Remove json label if present
        if text.lower().startswith("json"):
            text = text[4:].strip()
            
        return text
    
    def _calculate_confidence(self, line_items: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on data completeness."""
        if not line_items:
            return 0.0
        
        required_fields = ['item_name', 'quantity', 'unit_price']
        total_fields = 0
        filled_fields = 0
        
        for item in line_items:
            for field in required_fields:
                total_fields += 1
                if item.get(field) is not None and item.get(field) != "":
                    filled_fields += 1
        
        return round(filled_fields / total_fields, 2) if total_fields > 0 else 0.0


# Global service instance
data_capture_service = DataCaptureService()
