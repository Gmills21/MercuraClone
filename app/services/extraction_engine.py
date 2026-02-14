"""
Unified Extraction Engine
Handles both text and image extraction with consistent AI behavior
Uses MultiProviderAIService for intelligent API key rotation
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import base64
import io

from PIL import Image
from loguru import logger

# Load .env file for os.getenv
try:
    from dotenv import load_dotenv
    import pathlib
    env_path = pathlib.Path(__file__).parent.parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    logger.info(f"Loaded .env from {env_path}")
except ImportError:
    logger.warning("python-dotenv not installed")
except Exception as e:
    logger.warning(f"Failed to load .env: {e}")

# Optional OCR - only needed for image extraction
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    pytesseract = None

# PDF and Office Document support
try:
    import pdfplumber
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import pandas as pd
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

# Import our new multi-provider AI service
from app.ai_provider_service import get_ai_service, extract_structured_data
from app.services.langextract.docling_parser import DoclingParser
from app.posthog_utils import capture_event
from app.errors import ai_extraction_failed, ai_service_unavailable
from app.utils.resilience import with_timeout, TimeoutError
import time
import os


class ExtractionEngine:
    """
    Unified extraction for RFQ data from any source (text, image, email).
    
    Provides consistent:
    - AI prompting
    - Data cleaning
    - Quote mapping
    - Confidence scoring
    
    Uses MultiProviderAIService for intelligent API key rotation between
    Gemini and OpenRouter providers.
    """
    
    def __init__(self):
        self.ai_service = get_ai_service()
        self.ai_provider = "multi-provider"
        self.ai_model = "auto-rotated"
        self.docling_parser = DoclingParser()
        logger.info("Extraction engine initialized with MultiProviderAIService and Docling")
    
    async def extract_from_text(self, text: str, source_type: str = "email") -> Dict[str, Any]:
        """
        Extract RFQ data from text (email, pasted text, etc.)
        
        Args:
            text: Raw text to parse
            source_type: 'email', 'chat', 'document'
        
        Returns:
            Structured RFQ data with confidence score
        """
        logger.info(f"Extracting from text (source: {source_type})")
        
        if not text or not text.strip():
            return self._empty_result("No text provided")
        
        # Use AI to parse structured data
        structured_data = await self._parse_with_ai(text, source_type)
        
        # Clean and normalize
        cleaned_data = self._clean_extraction(structured_data)
        
        # Calculate confidence
        confidence = self._calculate_confidence(cleaned_data, has_ocr=False)
        
        return {
            "success": True,
            "source": source_type,
            "raw_text": text[:1000],  # Truncate for storage
            "structured_data": cleaned_data,
            "confidence": confidence,
            "extraction_method": "ai_text"
        }
    
    async def extract_from_image(self, image_data: bytes, filename: str = "image.jpg") -> Dict[str, Any]:
        """
        Extract RFQ data from image (photo, scan, screenshot)
        
        Args:
            image_data: Raw image bytes
            filename: Original filename
        
        Returns:
            Structured RFQ data with confidence score
        """
        logger.info(f"Extracting from image: {filename}")
        
        # Check if OCR is available
        if not PYTESSERACT_AVAILABLE:
            return {
                "success": False,
                "error": "OCR not available. Install pytesseract and Tesseract OCR to extract from images.",
                "structured_data": self._empty_result("OCR not available")["structured_data"],
                "confidence": 0.0
            }
        
        try:
            # Step 1: OCR
            ocr_text = await self._run_ocr(image_data)
            
            if not ocr_text or not ocr_text.strip():
                return self._empty_result("No text found in image")
            
            # Step 2: Parse OCR text with same AI as text extraction
            structured_data = await self._parse_with_ai(ocr_text, "image")
            
            # Step 3: Clean and normalize
            cleaned_data = self._clean_extraction(structured_data)
            
            # Step 4: Calculate confidence (lower due to OCR step)
            confidence = self._calculate_confidence(cleaned_data, has_ocr=True)
            
            return {
                "success": True,
                "source": "image",
                "filename": filename,
                "ocr_text": ocr_text[:2000],
                "structured_data": cleaned_data,
                "confidence": confidence * 0.9,  # Slight penalty for OCR
                "extraction_method": "ocr_then_ai"
            }
            
        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
            return self._empty_result(f"Extraction failed: {str(e)}")

    async def extract_from_pdf(self, pdf_data: bytes, filename: str = "document.pdf") -> Dict[str, Any]:
        """Extract RFQ data from PDF document."""
        logger.info(f"Extracting from PDF: {filename}")
        
        # Try Docling first (Best for complex layouts)
        try:
            if self.docling_parser.converter:
                logger.info("Attempting Docling extraction...")
                # Docling takes a file path or Path object, or InputDocument. 
                # For byte stream, we wrap in BytesIO and it usually auto-detects.
                # However, providing a filename helps.
                from docling.datamodel.base_models import InputFormat
                from docling.document_converter import DocumentConverter
                
                # Check if we can pass BytesIO directly to my wrapper
                markdown_text = self.docling_parser.parse(io.BytesIO(pdf_data), filename_hint=filename)
                
                if markdown_text and len(markdown_text) > 50:
                    logger.info("Docling extraction successful")
                    
                    # AI Parse with structured context
                    structured_data = await self._parse_with_ai(markdown_text, "pdf_docling")
                    cleaned_data = self._clean_extraction(structured_data)
                    confidence = self._calculate_confidence(cleaned_data, has_ocr=False)
                    
                    return {
                        "success": True,
                        "source": "pdf",
                        "filename": filename,
                        "full_text": markdown_text[:5000], # Store more text as MD is compact
                        "structured_data": cleaned_data,
                        "confidence": confidence + 0.15, # Bonus for Docling structure
                        "extraction_method": "docling_ai"
                    }
        except Exception as e:
            logger.warning(f"Docling extraction failed, falling back to legacy parsers: {e}")

        if not PDF_AVAILABLE:
            return self._empty_result("PDF extraction libraries not available")
            
        try:
            full_text = ""
            
            # Try pdfplumber first (often better for tables/structured text)
            try:
                with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            full_text += page_text + "\n\n"
            except Exception as e:
                logger.warning(f"pdfplumber failed: {e}. Falling back to PyPDF2.")
                
            # Fallback to PyPDF2 if pdfplumber extracted nothing
            if not full_text.strip():
                reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
                for page in reader.pages:
                    full_text += page.extract_text() + "\n\n"
            
            if not full_text.strip():
                return self._empty_result("No text could be extracted from PDF")
            
            # AI Parse
            structured_data = await self._parse_with_ai(full_text, "pdf")
            cleaned_data = self._clean_extraction(structured_data)
            confidence = self._calculate_confidence(cleaned_data, has_ocr=False)
            
            return {
                "success": True,
                "source": "pdf",
                "filename": filename,
                "full_text": full_text[:2000],
                "structured_data": cleaned_data,
                "confidence": confidence,
                "extraction_method": "pdf_ai"
            }
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return self._empty_result(f"PDF Extraction failed: {str(e)}")

    async def extract_from_document(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """
        Universal document extraction using Docling.
        Supports DOCX, PPTX, HTML, AsciiDoc, etc.
        """
        logger.info(f"Extracting from document: {filename}")
        
        try:
            if self.docling_parser.converter:
                logger.info(f"Using Docling for document: {filename}")
                
                # Pass file_data and filename hint to the parser
                markdown_text = self.docling_parser.parse(io.BytesIO(file_data), filename_hint=filename)
                
                if markdown_text and len(markdown_text) > 10:
                    logger.info("Docling document extraction successful")
                    
                    # AI Parse
                    structured_data = await self._parse_with_ai(markdown_text, f"docling_{filename.split('.')[-1]}")
                    cleaned_data = self._clean_extraction(structured_data)
                    confidence = self._calculate_confidence(cleaned_data, has_ocr=False)
                    
                    return {
                        "success": True,
                        "source": "document",
                        "filename": filename,
                        "full_text": markdown_text[:5000],
                        "structured_data": cleaned_data,
                        "confidence": confidence,
                        "extraction_method": "docling_ai"
                    }
            
            return self._empty_result(f"Docling not available for document: {filename}")
            
        except Exception as e:
            logger.error(f"Document extraction failed: {e}")
            return self._empty_result(f"Document extraction failed: {str(e)}")

    async def extract_from_xlsx(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """Extract RFQ data from Excel/CSV."""
        logger.info(f"Extracting from Spreadsheet: {filename}")
        
        if not EXCEL_AVAILABLE:
            return self._empty_result("Excel extraction libraries not available")
            
        try:
            # Read first sheet into text representative format
            if filename.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file_data))
            else:
                df = pd.read_excel(io.BytesIO(file_data))
            
            # Convert to markdown-like string for AI to process
            csv_text = df.to_csv(index=False)
            
            # AI Parse
            structured_data = await self._parse_with_ai(csv_text, "spreadsheet")
            cleaned_data = self._clean_extraction(structured_data)
            confidence = self._calculate_confidence(cleaned_data, has_ocr=False)
            
            return {
                "success": True,
                "source": "spreadsheet",
                "filename": filename,
                "full_text": csv_text[:2000],
                "structured_data": cleaned_data,
                "confidence": confidence,
                "extraction_method": "spreadsheet_ai"
            }
        except Exception as e:
            logger.error(f"Spreadsheet extraction failed: {e}")
            return self._empty_result(f"Spreadsheet extraction failed: {str(e)}")
    
    async def extract(self, 
                     text: Optional[str] = None,
                     file_data: Optional[bytes] = None,
                     filename: Optional[str] = None,
                     source_type: str = "unknown",
                     user_id: str = "anonymous") -> Dict[str, Any]:
        """
        Universal extraction method - handles text, image, PDF, Excel
        
        Features:
        - Timeout protection (60 seconds max)
        - User-friendly error messages
        - Graceful degradation when AI is unavailable
        - Detailed error tracking
        """
        start_time = time.time()
        
        # Track request received
        capture_event(
            distinct_id=user_id,
            event_name="receive_request",
            properties={
                "source_type": source_type,
                "filename": filename,
                "is_file": bool(file_data),
                "extension": filename.lower().split('.')[-1] if filename else None
            }
        )
        
        result = None
        
        try:
            # Apply timeout protection
            result = await with_timeout(
                self._extract_with_fallback(text, file_data, filename, source_type),
                timeout_seconds=60.0,
                timeout_message="Extraction took too long. Try a smaller file or different format."
            )
        except TimeoutError as e:
            logger.warning(f"Extraction timeout: {e}")
            result = {
                "success": False,
                "error": str(e),
                "error_code": "EXTRACTION_TIMEOUT",
                "retryable": True,
                "suggested_action": "Try uploading a smaller file, converting to PDF, or typing the information directly.",
                "structured_data": self._empty_structure(),
                "confidence": 0.0
            }
        except Exception as e:
            logger.exception(f"Unexpected extraction error: {e}")
            result = {
                "success": False,
                "error": "An unexpected error occurred while processing your file.",
                "error_code": "EXTRACTION_ERROR",
                "retryable": True,
                "suggested_action": "Please try again. If the problem persists, contact support.",
                "structured_data": self._empty_structure(),
                "confidence": 0.0
            }
            
        duration = time.time() - start_time
        
        # Track processing time and success
        capture_event(
            distinct_id=user_id,
            event_name="extraction_processed",
            properties={
                "processing_time_sec": round(duration, 3),
                "success": result.get("success", False),
                "method": result.get("extraction_method"),
                "confidence": result.get("confidence", 0.0),
                "line_item_count": len(result.get("structured_data", {}).get("line_items", []))
            }
        )
        
        return result
    
    async def _extract_with_fallback(
        self,
        text: Optional[str],
        file_data: Optional[bytes],
        filename: Optional[str],
        source_type: str
    ) -> Dict[str, Any]:
        """Internal extraction with format fallback logic."""
        if file_data and filename:
            ext = filename.lower().split('.')[-1]
            if ext in ['pdf']:
                return await self.extract_from_pdf(file_data, filename)
            elif ext in ['xlsx', 'xls', 'csv']:
                return await self.extract_from_xlsx(file_data, filename)
            elif ext in ['docx', 'pptx', 'html', 'htm', 'md', 'txt']:
                return await self.extract_from_document(file_data, filename)
            elif ext in ['jpg', 'jpeg', 'png', 'webp']:
                return await self.extract_from_image(file_data, filename)
            else:
                # If Docling is available, let it try unknown formats first
                if self.docling_parser.converter:
                    return await self.extract_from_document(file_data, filename)
                else:
                    # Fallback to OCR if it's an unrecognized file that might be an image
                    return await self.extract_from_image(file_data, filename)
        elif text:
            return await self.extract_from_text(text, source_type)
        else:
            return self._empty_result("No text or file provided", "NO_INPUT")
    
    async def _run_ocr(self, image_data: bytes) -> str:
        """Run OCR on image data."""
        if not PYTESSERACT_AVAILABLE:
            logger.error("OCR requested but pytesseract not installed")
            return ""
        
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if too large
        max_size = 2000
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Run OCR
        return pytesseract.image_to_string(image)
    
    async def _parse_with_ai(self, text: str, source_type: str) -> Dict[str, Any]:
        """Parse structured data from text using LangExtract with source grounding."""
        from app.services.langextract import extract, visualize
        
        prompt_description = """
        Extract the following entities from the Request for Quote (RFQ):
        - customer_name: The company or person requesting the quote.
        - contact_email: Email address of the requester.
        - contact_phone: Phone number of the requester.
        - delivery_date: Requested delivery date.
        - delivery_location: Delivery address.
        - special_instructions: Any special notes.
        - line_item_quantity: The quantity for a line item (e.g., 50).
        - line_item_unit: The unit of measure (pcs, ea, etc).
        - line_item_sku: The part number or SKU.
        - line_item_description: The description of the product.
        
        Rules:
        - Only extract if this is a quote request.
        - For line items, extract each component separately but keep them associated with the line text.
        """
        
        try:
            # 1. Run LangExtract
            result = await extract(
                text_or_documents=text,  # No limit, let Gemini handle large context
                prompt_description=prompt_description
            )
            
            # 2. Generate visualization HTML
            visualization_html = visualize(result)
            
            # 3. Post-process extractions into structured data
            data = {
                "customer_name": None,
                "contact_email": None,
                "contact_phone": None,
                "line_items": [],
                "delivery_date": None,
                "delivery_location": None,
                "special_instructions": None,
                "visualization_html": visualization_html
            }
            
            # Helper to get extraction text
            def get_text(cls_name):
                return next((e.extraction_text for e in result.extractions if e.extraction_class == cls_name), None)
            
            data["customer_name"] = get_text("customer_name")
            data["contact_email"] = get_text("contact_email")
            data["contact_phone"] = get_text("contact_phone")
            data["delivery_date"] = get_text("delivery_date")
            data["delivery_location"] = get_text("delivery_location")
            data["special_instructions"] = get_text("special_instructions")
            
            # Group line items by line number (using source_start_char)
            # We assume items on the same line belong together
            line_items_map = {}
            
            for ext in result.extractions:
                if not ext.extraction_class.startswith("line_item_"):
                    continue
                
                # Determine line number
                # Simple approximation: count newlines before start char
                if ext.source_start_char is not None:
                    line_num = text.count('\n', 0, ext.source_start_char)
                else:
                    line_num = -1 # fallback group
                
                if line_num not in line_items_map:
                    line_items_map[line_num] = {
                        "fields": {},
                        "source_locations": []
                    }
                
                # Map class to field name
                # line_item_quantity -> quantity
                field = ext.extraction_class.replace("line_item_", "")
                if field == "description": field = "item_name" # Map description to item_name per schema
                
                # Store value
                if field in ["quantity"]:
                    # Try to parse number
                    import re
                    nums = re.findall(r'\d+', ext.extraction_text)
                    if nums:
                        line_items_map[line_num]["fields"][field] = int(nums[0])
                    else:
                        line_items_map[line_num]["fields"][field] = 1
                else:
                    line_items_map[line_num]["fields"][field] = ext.extraction_text
                
                # Store source location for zero-error precision
                if ext.source_start_char is not None and ext.source_end_char is not None:
                    line_items_map[line_num]["source_locations"].append({
                        "field": field,
                        "start_char": ext.source_start_char,
                        "end_char": ext.source_end_char,
                        "confidence": ext.confidence or 0.8
                    })

            # Convert map to list
            for line_num, item_data in sorted(line_items_map.items()):
                fields = item_data["fields"]
                if "item_name" in fields or "sku" in fields: # Filter valid items
                    # Calculate bounding box from source locations (approximate)
                    source_locs = item_data["source_locations"]
                    bbox = None
                    if source_locs:
                        # Use the first source location to estimate position
                        first_loc = source_locs[0]
                        # Approximate position as percentage of text length
                        total_len = len(text)
                        if total_len > 0:
                            start_pct = (first_loc["start_char"] / total_len) * 100
                            bbox = {
                                "x": 5,  # Left margin
                                "y": min(start_pct, 95),  # Vertical position
                                "width": 90,  # Full width minus margins
                                "height": 3   # Approximate line height
                            }
                    
                    data["line_items"].append({
                        "item_name": fields.get("item_name", "Unknown Item"),
                        "quantity": fields.get("quantity", 1),
                        "sku": fields.get("sku"),
                        "unit": fields.get("unit", "pcs"),
                        "notes": f"Line {line_num+1}" if line_num >= 0 else None,
                        "source_location": {
                            "line": line_num + 1 if line_num >= 0 else None,
                            "page": 1,  # Single page for text
                            "bbox": bbox,
                            "char_range": source_locs[0] if source_locs else None
                        },
                        "extraction_confidence": min([loc["confidence"] for loc in source_locs]) if source_locs else 0.7
                    })
            
            return data
                
        except Exception as e:
            logger.error(f"LangExtract parsing failed: {e}")
            return self._basic_parse(text)
    
    def _basic_parse(self, text: str) -> Dict[str, Any]:
        """Basic regex-based parsing when AI unavailable."""
        import re
        
        # Find quantities and items
        line_items = []
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        for line in lines:
            # Match quantity ONLY at the start of the line
            # Pattern: number followed by x/pcs/units/ea at the START
            # Strict regex: (\d+) captured, optional unit captured, then separator, then content
            qty_match = re.match(r'^[\s\-\*•]*(\d+)\s*(x|pcs?|units?|ea|each)?([.:\s\-])\s*(.*)', line, re.IGNORECASE)
            
            if qty_match:
                qty_val = int(qty_match.group(1))
                unit = qty_match.group(2)
                separator = qty_match.group(3)
                item_name = qty_match.group(4).strip()
                
                # HEURISTIC 1: Numbered List Detection
                # If "1. ItemName" (no unit, dot separator), assume it's a list item, NOT a quantity of 1
                if not unit and '.' in separator:
                    continue

                # HEURISTIC 2: Technical Spec Detection
                # If quantity is large (>10) and item name starts with technical keywords (PSI, Class, Type)
                # e.g. "150 PSI" -> Qty 150 (WRONG)
                if qty_val > 10 and re.match(r'^(PSI|Class|Type|Grade|ANSI|DIN|WOG|CWP)', item_name, re.IGNORECASE):
                    continue

                # Only strip the quantity prefix, preserve the rest
                # Skip if item_name is just numbers (phone number false positive)
                if item_name and len(item_name) > 3 and not re.match(r'^[\d\s\-\(\)\.]+$', item_name):
                    line_items.append({
                        "item_name": item_name,
                        "quantity": qty_val,
                        "sku": None,
                        "unit": "pcs"
                    })
        
        # Find email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        email = email_match.group(0) if email_match else None
        
        # Find phone number (US format: (555) 123-4567 or 555-123-4567 or 555.123.4567)
        phone_match = re.search(r'\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}', text)
        phone = phone_match.group(0) if phone_match else None
        
        # Extract customer name - look for patterns like "from [Company]" or "[Name] from [Company]"
        customer_name = None
        
        # Pattern 1: "from [Company]"
        from_match = re.search(r'from\s+([A-Z][A-Za-z\s&]+?)(?:\.|,|\n|$)', text)
        if from_match:
            customer_name = from_match.group(1).strip()
        
        # Pattern 2: "[Name] from [Company]"
        if not customer_name:
            name_from_match = re.search(r'(?:I am|this is|from)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s+from|\s+at|\n|$)', text, re.IGNORECASE)
            if name_from_match:
                customer_name = name_from_match.group(1).strip()
        
        # Pattern 3: Look for "Corp", "Inc", "LLC", "Ltd"
        if not customer_name:
            company_match = re.search(r'([A-Z][A-Za-z\s]+(?:Corp|Inc|LLC|Ltd|Company|Co\.))', text)
            if company_match:
                customer_name = company_match.group(1).strip()
        
        # Fallback: first non-empty line if it looks like a company/person
        if not customer_name and lines:
            first = lines[0]
            # Only use first line if it doesn't look like a greeting
            if not re.match(r'^(Hi|Hello|Hey|Dear|Subject|Re:|Fwd:|To:|From:)', first, re.IGNORECASE):
                customer_name = first[:100]
        
        return {
            "customer_name": customer_name or "Unknown",
            "contact_email": email,
            "contact_phone": phone,
            "line_items": line_items[:10],
            "delivery_date": None,
            "delivery_location": None,
            "special_instructions": None,
            "confidence": 0.4 if line_items else 0.2
        }
    
    def _clean_extraction(self, data: Dict) -> Dict[str, Any]:
        """Clean and normalize extracted data."""
        cleaned = {
            "customer_name": self._clean_customer_name(data.get("customer_name")),
            "contact_email": self._clean_email(data.get("contact_email")),
            "contact_phone": self._clean_phone(data.get("contact_phone")),
            "line_items": [],
            "delivery_date": self._clean_date(data.get("delivery_date")),
            "delivery_location": self._clean_string(data.get("delivery_location")),
            "special_instructions": self._clean_string(data.get("special_instructions")),
            "visualization_html": data.get("visualization_html")  # Pass through HTML
        }
        
        # Clean line items
        for item in data.get("line_items", []):
            cleaned_item = {
                "item_name": self._clean_string(item.get("item_name", "Unknown Item")),
                "quantity": max(1, int(item.get("quantity", 1))),
                "sku": self._clean_string(item.get("sku")),
                "unit": item.get("unit", "pcs"),
                "notes": self._clean_string(item.get("notes"))
            }
            cleaned["line_items"].append(cleaned_item)
        
        return cleaned
    
    def _calculate_confidence(self, data: Dict, has_ocr: bool = False) -> float:
        """Calculate extraction confidence score."""
        score = 0.5  # Base score
        
        # Boost for customer name
        if data.get("customer_name") and data["customer_name"] != "Unknown":
            score += 0.15
        
        # Boost for line items
        if data.get("line_items"):
            score += min(0.2, len(data["line_items"]) * 0.05)
        
        # Boost for contact info
        if data.get("contact_email"):
            score += 0.1
        
        # Penalty for OCR
        if has_ocr:
            score *= 0.9
        
        return min(1.0, max(0.0, score))
    
    def _clean_string(self, s: Any) -> Optional[str]:
        """Clean string value."""
        if not s:
            return None
        s = str(s).strip()
        return s if s else None
    
    def _clean_customer_name(self, name: Any) -> Optional[str]:
        """Clean customer name by removing common prefixes."""
        name = self._clean_string(name)
        if not name:
            return None
        
        # Remove common prefixes
        prefixes = [
            r'^(?:Hi|Hello|Hey|Greetings)[,\s]+',
            r'^(?:Quote request|RFQ|Inquiry|Order)[\s\-]+(?:from|for)[:\s\-]+',
            r'^(?:This is|I am|We are)[:\s]+',
            r'^["\'\s]+',
        ]
        
        import re
        for prefix in prefixes:
            name = re.sub(prefix, '', name, flags=re.IGNORECASE)
        
        # Remove trailing punctuation
        name = re.sub(r'[:;,.\-]+$', '', name).strip()
        
        # Remove "from" at the end
        name = re.sub(r'\s+from$', '', name, flags=re.IGNORECASE).strip()
        
        return name if name else None
    
    def _clean_email(self, email: Any) -> Optional[str]:
        """Validate and clean email."""
        import re
        email = self._clean_string(email)
        if email and re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            return email
        return None
    
    def _clean_phone(self, phone: Any) -> Optional[str]:
        """Clean phone number."""
        phone = self._clean_string(phone)
        if phone:
            # Remove non-numeric except + - ( )
            import re
            phone = re.sub(r'[^\d\+\-\(\)\s]', '', phone)
            return phone if len(phone) >= 10 else None
        return None
    
    def _clean_date(self, date: Any) -> Optional[str]:
        """Clean and normalize date."""
        date = self._clean_string(date)
        # Could add date parsing here
        return date
    
    def _empty_structure(self) -> Dict[str, Any]:
        """Return empty structure for failed extractions."""
        return {
            "customer_name": None,
            "contact_email": None,
            "contact_phone": None,
            "line_items": [],
            "delivery_date": None,
            "delivery_location": None,
            "special_instructions": None
        }
    
    def _empty_result(self, error_message: str, error_code: str = "EXTRACTION_FAILED") -> Dict[str, Any]:
        """Return empty result with error and user-friendly messaging."""
        return {
            "success": False,
            "error": error_message,
            "error_code": error_code,
            "retryable": True,
            "suggested_action": "Try uploading a clearer image, converting to PDF, or typing the information directly.",
            "structured_data": self._empty_structure(),
            "confidence": 0.0
        }


# Global instance
extraction_engine = ExtractionEngine()