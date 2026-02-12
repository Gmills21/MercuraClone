from pydantic import BaseModel
from typing import List, Optional, Any

class Extraction(BaseModel):
    extraction_class: str
    extraction_text: str
    source_chunk_index: Optional[int] = None
    source_start_char: Optional[int] = None
    source_end_char: Optional[int] = None
    confidence: Optional[float] = None
    metadata: Optional[Any] = None

class ExampleData(BaseModel):
    text: str
    extractions: List[Extraction]

class ExtractionResult(BaseModel):
    document_text: str  # Original text
    extractions: List[Extraction]
    metadata: Optional[Any] = None
