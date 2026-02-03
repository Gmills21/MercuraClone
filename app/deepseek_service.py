"""
DeepSeek service for OpenRouter free tier.
Replaces paid Gemini API with free DeepSeek via OpenRouter.
"""

import os
import json
import httpx
from typing import Optional, Dict, Any, List
from loguru import logger

# OpenRouter free tier endpoints
OPENROUTER_API_URL = "https://openrouter.ai/api/v1"
# Free tier models (verified available on OpenRouter)
DEFAULT_MODEL = "nvidia/nemotron-3-nano-30b-a3b:free"

# Fallback models (all free tier)
FALLBACK_MODELS = [
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "upstage/solar-pro-3:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "arcee-ai/trinity-large-preview:free",
]


class DeepSeekService:
    """Service for interacting with DeepSeek via OpenRouter or Direct API."""
    
    def __init__(self, openrouter_key: Optional[str] = None, deepseek_key: Optional[str] = None):
        from app.config import settings
        
        self.openrouter_key = openrouter_key or settings.openrouter_api_key
        self.openrouter_url = OPENROUTER_API_URL
        self.openrouter_model = settings.openrouter_model or DEFAULT_MODEL
        
        self.deepseek_key = deepseek_key or settings.deepseek_api_key
        self.deepseek_url = settings.deepseek_base_url
        self.deepseek_model = settings.deepseek_model
        
        if not self.openrouter_key and not self.deepseek_key:
            logger.warning("No AI API keys configured (OpenRouter or DeepSeek). AI features will not work.")
    
    def _get_headers(self, api_key: str, is_openrouter: bool = True) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if is_openrouter:
            headers.update({
                "HTTP-Referer": "https://openmercura.local",
                "X-Title": "OpenMercura",
            })
        return headers
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a chat completion request, trying OpenRouter first, then direct DeepSeek.
        """
        # Try OpenRouter first if configured
        if self.openrouter_key:
            logger.info("Attempting chat completion via OpenRouter")
            res = await self._call_api(
                url=f"{self.openrouter_url}/chat/completions",
                api_key=self.openrouter_key,
                model=model or self.openrouter_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                is_openrouter=True
            )
            if "error" not in res:
                return res
            logger.warning(f"OpenRouter failed: {res.get('error')}. Falling back to Direct DeepSeek if available.")

        # Fallback to direct DeepSeek
        if self.deepseek_key:
            logger.info("Attempting chat completion via Direct DeepSeek")
            res = await self._call_api(
                url=f"{self.deepseek_url}/chat/completions",
                api_key=self.deepseek_key,
                model=self.deepseek_model, # Use direct model if falling back
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                is_openrouter=False
            )
            if "error" not in res:
                return res
            logger.error(f"Direct DeepSeek failed: {res.get('error')}")
            return res

        return {"error": "No AI API keys configured or all providers failed."}

    async def _call_api(
        self,
        url: str,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
        is_openrouter: bool
    ) -> Dict[str, Any]:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    headers=self._get_headers(api_key, is_openrouter),
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except Exception as e:
            return {"error": str(e)}
    
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
        system_prompt = f"""You are a data extraction assistant. Extract structured information from the provided text.

Output Format: Return ONLY valid JSON matching this schema:
{json.dumps(schema, indent=2)}

{instructions or ''}

Important: Return ONLY the JSON object, no markdown formatting, no explanations."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract data from this text:\n\n{text}"},
        ]
        
        result = await self.chat_completion(messages, temperature=0.1)
        
        if "error" in result:
            return {"success": False, "error": result["error"]}
        
        try:
            content = result["choices"][0]["message"]["content"]
            # Clean up potential markdown formatting
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            parsed = json.loads(content)
            return {"success": True, "data": parsed}
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse extraction result: {e}")
            return {"success": False, "error": f"Parsing failed: {e}"}
    
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


# Singleton instance
_deepseek_service: Optional[DeepSeekService] = None


def get_deepseek_service() -> DeepSeekService:
    """Get or create DeepSeek service singleton."""
    global _deepseek_service
    if _deepseek_service is None:
        _deepseek_service = DeepSeekService()
    return _deepseek_service
