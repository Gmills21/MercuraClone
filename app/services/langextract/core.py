import json
import os
import re
from typing import List, Optional, Dict, Any

import httpx
from loguru import logger

from .data import Extraction, ExampleData, ExtractionResult

# Try to get API key from config, but handle failure gracefully
try:
    from app.config import settings
    GEMINI_API_KEY = settings.gemini_api_key
    KIMI_API_KEY = getattr(settings, "kimi_api_key", None) or os.getenv("KIMI_API_KEY", "")
    KIMI_MODEL = getattr(settings, "kimi_model", "moonshot-v1-32k") or os.getenv("KIMI_MODEL", "moonshot-v1-32k")
    KIMI_BASE_URL = getattr(settings, "kimi_base_url", "https://api.moonshot.ai/v1") or os.getenv("KIMI_BASE_URL", "https://api.moonshot.ai/v1")
except ImportError:
    GEMINI_API_KEY = None
    KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")
    KIMI_MODEL = os.getenv("KIMI_MODEL", "moonshot-v1-32k")
    KIMI_BASE_URL = os.getenv("KIMI_BASE_URL", "https://api.moonshot.ai/v1")


class LangExtract:
    def __init__(self, api_key: Optional[str] = None):
        self.gemini_api_key = api_key or GEMINI_API_KEY
        self.kimi_api_key = KIMI_API_KEY
        self.kimi_model = KIMI_MODEL
        self.kimi_base_url = KIMI_BASE_URL.rstrip("/")
        self._use_kimi = bool(self.kimi_api_key)
        if self._use_kimi:
            logger.info(f"LangExtract using Kimi (Moonshot AI) for document analysis: {self.kimi_model}")
        elif self.gemini_api_key:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_api_key)
            logger.info("LangExtract using Gemini for document analysis")
        else:
            logger.warning("LangExtract initialized without API key (neither Kimi nor Gemini)")
            
    async def extract(self, 
                text_or_documents: str, 
                prompt_description: str,
                examples: List[ExampleData] = None,
                model_id: str = "gemini-1.5-flash") -> ExtractionResult:
        """
        Extract structured data from text using Kimi (when configured) or Gemini with source grounding.
        Kimi/Moonshot AI is used for document analysis when KIMI_API_KEY is set.
        """
        if self._use_kimi:
            return await self._extract_with_kimi(text_or_documents, prompt_description, examples)
        if not self.gemini_api_key:
            raise ValueError("API Key is required for extraction (set KIMI_API_KEY or GEMINI_API_KEY)")

        import google.generativeai as genai
        model = genai.GenerativeModel(model_name=model_id)
        
        # Build prompt
        system_instructions = f"""You are a precise extraction engine. {prompt_description}
        
        CRITICAL INSTRUCTIONS:
        1. Extract the requested entities EXACTLY as they appear in the text.
        2. Return ONLY a JSON list of objects with 'extraction_class' and 'extraction_text'.
        3. Do NOT modify the text (e.g., do not correct spelling or formatting).
        4. If an entity appears multiple times, extract each occurrence if relevant.
        """
        
        full_text = text_or_documents
        
        # Construct examples context
        examples_text = ""
        if examples:
            examples_text = "\n\nEXAMPLES:\n"
            for ex in examples:
                ex_json = json.dumps([{"extraction_class": e.extraction_class, "extraction_text": e.extraction_text} for e in ex.extractions])
                examples_text += f"Input: {ex.text}\nOutput: {ex_json}\n\n"
        
        query = f"{system_instructions}{examples_text}\n\nINPUT TEXT:\n{full_text}\n\nOUTPUT JSON:"
        
        try:
            response = await model.generate_content_async(query)
            raw_response = response.text.strip()
            
            # Simple JSON cleanup
            if raw_response.startswith("```"):
                raw_response = raw_response.split("```")[1]
                if raw_response.startswith("json"):
                    raw_response = raw_response[4:]
            raw_response = raw_response.strip()
            
            extracted_data = json.loads(raw_response)
            
            # Grounding: Find positions in text
            final_extractions = []
            
            for item in extracted_data:
                text_val = item.get("extraction_text")
                cls_val = item.get("extraction_class")
                
                if not text_val:
                    continue
                
                # Find all occurrences of text_val in full_text
                matches = [m for m in re.finditer(re.escape(text_val), full_text)]
                
                if matches:
                    # HEURISTIC: First match for now
                    match = matches[0] 
                    
                    final_extractions.append(Extraction(
                        extraction_class=cls_val,
                        extraction_text=text_val,
                        source_start_char=match.start(),
                        source_end_char=match.end(),
                        confidence=0.9
                    ))
                else:
                    # Extracted text not found exactly
                    final_extractions.append(Extraction(
                        extraction_class=cls_val,
                        extraction_text=text_val,
                        confidence=0.5
                    ))

            return ExtractionResult(
                document_text=full_text,
                extractions=final_extractions
            )
            
        except Exception as e:
            logger.error(f"LangExtract extraction failed: {e}")
            return ExtractionResult(document_text=full_text, extractions=[])

    async def _extract_with_kimi(
        self,
        text_or_documents: str,
        prompt_description: str,
        examples: List[ExampleData] = None,
    ) -> ExtractionResult:
        """Extract using Kimi (Moonshot AI) - OpenAI-compatible API."""
        full_text = text_or_documents

        system_instructions = f"""You are a precise extraction engine. {prompt_description}

        CRITICAL INSTRUCTIONS:
        1. Extract the requested entities EXACTLY as they appear in the text.
        2. Return ONLY a JSON list of objects with 'extraction_class' and 'extraction_text'.
        3. Do NOT modify the text (e.g., do not correct spelling or formatting).
        4. If an entity appears multiple times, extract each occurrence if relevant.
        """

        examples_text = ""
        if examples:
            examples_text = "\n\nEXAMPLES:\n"
            for ex in examples:
                ex_json = json.dumps([{"extraction_class": e.extraction_class, "extraction_text": e.extraction_text} for e in ex.extractions])
                examples_text += f"Input: {ex.text}\nOutput: {ex_json}\n\n"

        user_content = f"{system_instructions}{examples_text}\n\nINPUT TEXT:\n{full_text}\n\nOUTPUT JSON:"

        messages = [
            {"role": "system", "content": "You are a precise extraction engine. Output only valid JSON arrays."},
            {"role": "user", "content": user_content},
        ]

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.kimi_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.kimi_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.kimi_model,
                        "messages": messages,
                        "temperature": 0.1,
                    },
                )
                response.raise_for_status()
                data = response.json()

            raw_response = data["choices"][0]["message"]["content"].strip()

            # Simple JSON cleanup
            if raw_response.startswith("```"):
                raw_response = raw_response.split("```")[1]
                if raw_response.startswith("json"):
                    raw_response = raw_response[4:]
            raw_response = raw_response.strip()

            extracted_data = json.loads(raw_response)
            final_extractions = []

            for item in extracted_data:
                text_val = item.get("extraction_text")
                cls_val = item.get("extraction_class")
                if not text_val:
                    continue
                matches = [m for m in re.finditer(re.escape(text_val), full_text)]
                if matches:
                    match = matches[0]
                    final_extractions.append(Extraction(
                        extraction_class=cls_val,
                        extraction_text=text_val,
                        source_start_char=match.start(),
                        source_end_char=match.end(),
                        confidence=0.9,
                    ))
                else:
                    final_extractions.append(Extraction(
                        extraction_class=cls_val,
                        extraction_text=text_val,
                        confidence=0.5,
                    ))

            return ExtractionResult(document_text=full_text, extractions=final_extractions)

        except Exception as e:
            logger.error(f"LangExtract Kimi extraction failed: {e}")
            return ExtractionResult(document_text=full_text, extractions=[])
