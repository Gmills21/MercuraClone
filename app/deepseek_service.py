"""
DeepSeek service - NOW USING MultiProviderAIService
This module is kept for backward compatibility.
All AI calls are routed through the unified MultiProviderAIService.
"""

import os
import json
from typing import Optional, Dict, Any, List
from loguru import logger

# Import the new multi-provider service
from app.ai_provider_service import get_ai_service, MultiProviderAIService


class DeepSeekService:
    """
    Service for AI interactions - NOW USING MultiProviderAIService.
    
    This class is maintained for backward compatibility.
    It delegates all operations to the unified MultiProviderAIService
    which handles intelligent key rotation between Gemini and OpenRouter.
    """
    
    def __init__(self, openrouter_key: Optional[str] = None, deepseek_key: Optional[str] = None):
        """
        Initialize the service.
        
        Note: The key parameters are now ignored as we use MultiProviderAIService
        which loads all keys from environment automatically.
        """
        self.ai_service = get_ai_service()
        
        # For backward compatibility logging
        key_count = len(self.ai_service.keys)
        gemini_count = len([k for k in self.ai_service.keys if k.provider.value == "gemini"])
        openrouter_count = len([k for k in self.ai_service.keys if k.provider.value == "openrouter"])
        
        logger.info(f"DeepSeekService initialized (using MultiProviderAIService)")
        logger.info(f"  Available keys: {key_count} total ({gemini_count} Gemini, {openrouter_count} OpenRouter)")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a chat completion request via MultiProviderAIService.
        
        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            model: Model to use (provider auto-selected)
        
        Returns:
            API response dict
        """
        return await self.ai_service.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
            fallback_providers=True
        )
    
    async def extract_structured_data(
        self,
        text: str,
        schema: Dict[str, Any],
        instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract structured data from unstructured text.
        
        Args:
            text: Raw text to parse
            schema: JSON schema describing expected output
            instructions: Additional instructions for the model
        
        Returns:
            Parsed structured data
        """
        return await self.ai_service.extract_structured_data(
            text=text,
            schema=schema,
            instructions=instructions
        )
    
    async def parse_line_items(self, text: str) -> Dict[str, Any]:
        """
        Parse line items from quote/email text.
        
        Args:
            text: Raw text containing line items
        
        Returns:
            Extracted line items with confidence score
        """
        schema = {
            "line_items": [
                {
                    "item_name": "string",
                    "sku": "string or null",
                    "description": "string or null",
                    "quantity": "number",
                    "unit_price": "number",
                    "total_price": "number"
                }
            ],
            "document_type": "string (quote, invoice, email, etc.)",
            "document_number": "string or null",
            "date": "string or null (ISO format)",
            "vendor": "string or null",
            "total_amount": "number",
            "currency": "string (default: USD)"
        }
        
        instructions = """
        Extract all line items from the text. Look for:
        - Product names and descriptions
        - SKUs or part numbers
        - Quantities and units
        - Prices (unit and total)
        - Document metadata (date, vendor, quote number)
        
        Calculate totals if not explicitly stated.
        """
        
        result = await self.extract_structured_data(text, schema, instructions)
        
        if result["success"]:
            # Add confidence scoring
            data = result["data"]
            line_items = data.get("line_items", [])
            confidence = 0.9 if len(line_items) > 0 else 0.5
            
            return {
                "success": True,
                "line_items": line_items,
                "document_type": data.get("document_type"),
                "document_number": data.get("document_number"),
                "date": data.get("date"),
                "vendor": data.get("vendor"),
                "total_amount": data.get("total_amount"),
                "currency": data.get("currency", "USD"),
                "confidence_score": confidence,
            }
        
        return {"success": False, "error": result.get("error", "Unknown error")}
    
    async def analyze_competitor(self, url: str, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze competitor data from scraped content.
        
        Args:
            url: Competitor URL
            scraped_data: Raw scraped content (title, description, etc.)
        
        Returns:
            Structured competitor analysis
        """
        schema = {
            "name": "string - company name",
            "description": "string - concise company description",
            "key_features": ["list of key product features"],
            "pricing_indicators": "string - any pricing info or pricing model hints",
            "target_market": "string - who they sell to",
            "competitive_strengths": ["list of competitive advantages"],
            "confidence": "number 0-1"
        }
        
        instructions = """
        Analyze this competitor website data and extract key business intelligence.
        Be concise but thorough. If data is missing, indicate with null or empty arrays.
        """
        
        content = f"""URL: {url}
Title: {scraped_data.get('title', 'N/A')}
Meta Description: {scraped_data.get('description', 'N/A')}
Meta Keywords: {scraped_data.get('keywords', 'N/A')}
Text Content Preview: {scraped_data.get('text', 'N/A')[:2000]}
"""
        
        result = await self.extract_structured_data(text=content, schema=schema, instructions=instructions)
        
        if result["success"]:
            data = result["data"]
            return {
                "url": url,
                "name": data.get("name", "Unknown"),
                "description": data.get("description"),
                "features": data.get("key_features", []),
                "pricing": data.get("pricing_indicators"),
                "target_market": data.get("target_market"),
                "strengths": data.get("competitive_strengths", []),
                "confidence": data.get("confidence", 0.5),
                "last_updated": "2026-01-31T00:00:00Z",
            }
        
        return {"error": result.get("error", "Analysis failed"), "url": url}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics from MultiProviderAIService."""
        return self.ai_service.get_stats()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all providers."""
        return await self.ai_service.health_check()


# Singleton instance
_deepseek_service: Optional[DeepSeekService] = None


def get_deepseek_service() -> DeepSeekService:
    """Get or create DeepSeek service singleton."""
    global _deepseek_service
    if _deepseek_service is None:
        _deepseek_service = DeepSeekService()
    return _deepseek_service