import json
from typing import List, Optional, Dict, Any
import google.generativeai as genai
import re
from loguru import logger
from .data import Extraction, ExampleData, ExtractionResult

# Try to get API key from config, but handle failure gracefully
try:
    from app.config import settings
    API_KEY = settings.gemini_api_key
except ImportError:
    API_KEY = None

class LangExtract:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or API_KEY
        if not self.api_key:
            logger.warning("LangExtract initialized without API key")
        else:
            genai.configure(api_key=self.api_key)
            
    async def extract(self, 
                text_or_documents: str, 
                prompt_description: str,
                examples: List[ExampleData] = None,
                model_id: str = "gemini-1.5-flash") -> ExtractionResult:
        """
        Extract structured data from text using Gemini with source grounding.
        Mimics langextract.extract functionality.
        """
        if not self.api_key:
            raise ValueError("API Key is required for extraction")

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
