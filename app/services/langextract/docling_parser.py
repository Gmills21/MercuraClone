
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
