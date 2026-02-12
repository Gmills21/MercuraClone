
import io
import os
import tempfile
from pathlib import Path
from typing import Union, Optional
from loguru import logger

try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    logger.warning("Docling is not installed. Document parsing features will be unavailable.")

class DoclingParser:
    """
    Wrapper for IBM's Docling library to parse complex documents into structured Markdown.
    Supports PDF, DOCX, PPTX, XLSX, HTML, and images.
    """
    def __init__(self):
        if DOCLING_AVAILABLE:
            self.converter = DocumentConverter()
        else:
            self.converter = None

    def parse(self, source: Union[str, Path, io.BytesIO], filename_hint: Optional[str] = None) -> str:
        """
        Parses a document (PDF, DOCX, etc.) into Markdown text using Docling.
        
        Args:
            source: File path (str/Path) or file-like object (BytesIO).
            filename_hint: Original filename (useful for temp file extension) if source is bytes.
            
        Returns:
            str: The structured Markdown content of the document.
        """
        if not DOCLING_AVAILABLE:
            raise ImportError(
                "Docling is required for document parsing but not installed. "
                "Please run `pip install docling`."
            )
        
        temp_file_path = None
        
        try:
            # Handle BytesIO by writing to temp file with correct extension
            if isinstance(source, io.BytesIO) or isinstance(source, bytes):
                content = source.read() if isinstance(source, io.BytesIO) else source
                
                # Determine extension
                suffix = ".pdf" # Default
                if filename_hint:
                    base, ext = os.path.splitext(filename_hint)
                    if ext: 
                        suffix = ext
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                    temp_file.write(content)
                    temp_file_path = temp_file.name
                    logger.debug(f"Created temp file for Docling: {temp_file_path}")
                    
                source_to_convert = temp_file_path
            else:
                source_to_convert = source

            logger.info(f"Parsing document with Docling: {source_to_convert}")
            
            conversion_result = self.converter.convert(source_to_convert)
            markdown_content = conversion_result.document.export_to_markdown()
            return markdown_content
            
        except Exception as e:
            logger.error(f"Docling parsing failed: {e}")
            raise
        finally:
            # Cleanup temp file if created
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.debug(f"Cleaned up temp file: {temp_file_path}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temp file {temp_file_path}: {cleanup_error}")

    def format_to_gaeb_xml(self, items: list, metadata: dict = None) -> str:
        """
        Formats a list of line items into a simplified GAEB XML (DA83) structure.
        Useful for European ERP integrations.
        
        Args:
            items: List of dicts containing 'description', 'quantity', 'unit_price', 'sku'.
            metadata: Optional project metadata.
            
        Returns:
            str: GAEB XML string.
        """
        import xml.etree.ElementTree as ET
        from datetime import datetime
        
        # Create root GAEB element
        gaeb = ET.Element("GAEB")
        gaeb.set("xmlns", "http://www.gaeb.de/GAEB_DA_XML/200407")
        
        # Project Info
        prjsr = ET.SubElement(gaeb, "PrjInfo")
        ET.SubElement(prjsr, "LblPrj").text = metadata.get("project_name", "Exported Quote") if metadata else "Exported Quote"
        ET.SubElement(prjsr, "Date").text = datetime.now().strftime("%Y-%m-%d")
        
        # Award (Offer)
        award = ET.SubElement(gaeb, "Award")
        boq = ET.SubElement(award, "BoQ") # Bill of Quantities
        
        lv_body = ET.SubElement(boq, "BoQBody")
        
        # Items (Positions)
        # Assuming a flat list for now, wrapped in a single lot
        lot_group = ET.SubElement(lv_body, "BoQCtgy") # Lot
        ET.SubElement(lot_group, "LblTx").text = "Main Lot"
        
        for i, item in enumerate(items, 1):
            item_list = ET.SubElement(lot_group, "Itemlist")
            
            # Position Item
            item_xml = ET.SubElement(item_list, "Item")
            item_xml.set("RNoPart", str(i)) # Row number
            
            # Quantity
            qty = item.get("quantity", 0)
            qty_elem = ET.SubElement(item_xml, "Qty")
            qty_elem.text = str(qty)
            
            # Unit
            unit_elem = ET.SubElement(item_xml, "QU")
            unit_elem.text = "Pce" # Default to Piece
            
            # Description (Short & Long)
            desc = item.get("description", item.get("item_name", "Item"))
            # Short Text (first 40 chars)
            st = ET.SubElement(item_xml, "TextShort")
            st.text = desc[:40] if desc else "No Desc"
            
            # Long Text
            lt = ET.SubElement(item_xml, "TextLong")
            lt_p = ET.SubElement(lt, "P") # Paragraph
            lt_p.text = desc
            
            # Unit Price
            price = item.get("unit_price", 0)
            up = ET.SubElement(item_xml, "UP")
            up.text = str(price)
            
            # Total Price
            tp = ET.SubElement(item_xml, "IT")
            tp.text = str(float(qty) * float(price))
            
        # Convert to string
        try:
            # ET.tostring returns bytes, decode to str
            xml_str = ET.tostring(gaeb, encoding="utf-8", method="xml").decode("utf-8")
            return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'
        except Exception as e:
            logger.error(f"Failed to generate GAEB XML: {e}")
            return ""
