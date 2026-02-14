"""
Knowledge Base Routes (Optional Feature)
API endpoints for product knowledge base - completely separate from core CRM.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Optional

from app.services.knowledge_base_service import get_knowledge_base_service, KnowledgeBaseService
from app.security_utils import sanitize_filename

router = APIRouter(prefix="/knowledge", tags=["knowledge-base"])


def check_kb_enabled():
    """Dependency to check if knowledge base is enabled."""
    kb = get_knowledge_base_service()
    if not kb.is_available():
        raise HTTPException(
            status_code=503,
            detail="Knowledge base feature is not enabled. Set KNOWLEDGE_BASE_ENABLED=true and install dependencies (chromadb, sentence-transformers)."
        )
    return kb


@router.get("/status")
async def get_kb_status():
    """
    Get knowledge base status and statistics.
    Works even when KB is disabled (shows why).
    """
    kb = get_knowledge_base_service()
    return kb.get_stats()


@router.post("/query")
async def query_knowledge_base(
    question: str = Form(..., description="Natural language question about products"),
    doc_types: Optional[str] = Form(None, description="Comma-separated doc types to search (catalog,spec_sheet,pricing)"),
    use_ai: bool = Form(True, description="Use AI to synthesize answer"),
    kb: KnowledgeBaseService = Depends(check_kb_enabled)
):
    """
    Query the knowledge base with a natural language question.
    
    Examples:
    - "What's the lead time on XT-400 valves?"
    - "Do we have stainless steel fittings in stock?"
    - "What's the price break for 100 units of SKU ABC-123?"
    """
    doc_type_list = doc_types.split(",") if doc_types else None
    
    result = await kb.query(
        question=question,
        doc_types=doc_type_list,
        use_ai=use_ai
    )
    
    return {
        "answer": result.answer,
        "sources": result.sources,
        "confidence": result.confidence,
        "query_time_ms": result.query_time_ms
    }


@router.post("/ingest")
async def ingest_document(
    file: UploadFile = File(..., description="Document to ingest (PDF, TXT, MD)"),
    doc_type: str = Form(..., description="Document type: catalog, spec_sheet, pricing, manual"),
    supplier: Optional[str] = Form(None, description="Supplier/manufacturer name"),
    notes: Optional[str] = Form(None, description="Additional notes"),
    kb: KnowledgeBaseService = Depends(check_kb_enabled)
):
    """
    Ingest a document into the knowledge base.
    
    Supported formats: PDF, TXT, Markdown (images/PDFs need OCR preprocessing)
    """
    import tempfile
    import os
    
    # Validate doc_type
    valid_types = ["catalog", "spec_sheet", "pricing", "manual", "datasheet", "unknown"]
    if doc_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid doc_type. Must be one of: {', '.join(valid_types)}"
        )
    
    # Sanitize filename and save uploaded file temporarily
    safe_filename = sanitize_filename(file.filename)
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    suffix = f".{safe_filename.split('.')[-1]}" if '.' in safe_filename else ""
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Prepare metadata
        metadata = {
            "original_filename": safe_filename,
            "uploaded_at": str(__import__('datetime').datetime.now()),
        }
        if supplier:
            metadata["supplier"] = supplier
        if notes:
            metadata["notes"] = notes
        
        # TODO: For PDFs and images, would integrate NuMarkdown here
        # For now, only text files work directly
        
        # Ingest
        result = await kb.ingest_document(
            file_path=tmp_path,
            doc_type=doc_type,
            metadata=metadata
        )
        
        # Cleanup
        os.unlink(tmp_path)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except Exception as e:
        # Cleanup on error
        if 'tmp_path' in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents(
    kb: KnowledgeBaseService = Depends(check_kb_enabled)
):
    """List all ingested documents with metadata."""
    try:
        results = kb.collection.get()
        
        # Group by source file
        docs = {}
        for i, metadata in enumerate(results['metadatas']):
            source = metadata.get("source", "unknown")
            if source not in docs:
                docs[source] = {
                    "source": source,
                    "doc_type": metadata.get("doc_type", "unknown"),
                    "chunks": 0,
                    "metadata": {k: v for k, v in metadata.items() 
                               if k not in ["source", "doc_type", "chunk_index", "total_chunks"]}
                }
            docs[source]["chunks"] += 1
        
        return {
            "total_documents": len(docs),
            "total_chunks": len(results['ids']),
            "documents": list(docs.values())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    kb: KnowledgeBaseService = Depends(check_kb_enabled)
):
    """Delete a document and all its chunks from the knowledge base."""
    success = await kb.delete_document(document_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"success": True, "message": f"Document {document_id} deleted"}


@router.post("/ask")
async def quick_ask(
    question: str = Form(...),
    kb: KnowledgeBaseService = Depends(check_kb_enabled)
):
    """
    Quick ask endpoint - simplified query for common questions.
    Same as /query but with sensible defaults.
    """
    result = await kb.query(question=question, top_k=3, use_ai=True)
    
    return {
        "answer": result.answer,
        "confidence": result.confidence,
        "has_sources": len(result.sources) > 0
    }
