"""
RAG (Chat with your data) API routes.
Uses local ChromaDB + DeepSeek free tier.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.rag_service import get_rag_service, chat_with_data
from app.database_sqlite import save_document, list_documents
from app.deepseek_service import get_deepseek_service
from fastapi import Depends
from app.middleware.organization import get_current_user_and_org
from datetime import datetime
import uuid

router = APIRouter(prefix="/rag", tags=["rag"])


class ChatRequest(BaseModel):
    query: str
    context: Optional[List[Dict[str, str]]] = None


class ChatResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]]
    available: bool


class DocumentUploadRequest(BaseModel):
    content: str
    source: str
    doc_type: str = "generic"
    metadata: Optional[Dict[str, Any]] = None


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Chat with your data using RAG.
    Retrieves relevant documents and generates response with DeepSeek.
    """
    result = await chat_with_data(request.query, request.context)
    return ChatResponse(**result)


@router.post("/documents")
async def add_document(
    request: DocumentUploadRequest,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Add a document to the RAG knowledge base."""
    rag = get_rag_service()
    
    # Add to ChromaDB
    doc_id = rag.add_document(
        content=request.content,
        source=request.source,
        doc_type=request.doc_type,
        metadata=request.metadata
    )
    
    if not doc_id:
        raise HTTPException(status_code=500, detail="Failed to add document to RAG")
    
    # Also save to SQLite for persistence
    doc_data = {
        "id": doc_id,
        "organization_id": user_org[1],
        "content": request.content[:500],  # Preview
        "source": request.source,
        "type": request.doc_type,
        "metadata": request.metadata or {},
        "created_at": datetime.utcnow().isoformat()
    }
    save_document(doc_data)
    
    return {"id": doc_id, "message": "Document added successfully"}


@router.get("/documents")
async def list_documents_endpoint(
    doc_type: Optional[str] = None,
    user_org: tuple = Depends(get_current_user_and_org)
):
    """List documents in the knowledge base."""
    user_id, org_id = user_org
    docs = list_documents(organization_id=org_id, doc_type=doc_type)
    return {"documents": docs, "count": len(docs)}


@router.get("/stats")
async def get_rag_stats():
    """Get RAG system statistics."""
    rag = get_rag_service()
    stats = rag.get_stats()
    return stats


@router.post("/search")
async def search_documents(query: str, n_results: int = 5, doc_type: Optional[str] = None):
    """Search documents by semantic similarity."""
    rag = get_rag_service()
    
    if not rag.is_available():
        raise HTTPException(status_code=503, detail="RAG service not available")
    
    results = rag.search(query, n_results=n_results, doc_type=doc_type)
    return {"results": results, "query": query}


@router.post("/ingest/quotes")
async def ingest_all_quotes(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Ingest all existing quotes into RAG for searching."""
    from app.database_sqlite import list_quotes, get_quote_with_items
    
    rag = get_rag_service()
    user_id, org_id = user_org
    quotes = list_quotes(organization_id=org_id, limit=1000)
    
    ingested = 0
    for q in quotes:
        quote = get_quote_with_items(q["id"], organization_id=org_id)
        if quote:
            # Create searchable content
            items_text = "\n".join([
                f"- {item.get('product_name', 'Unknown')}: {item.get('quantity')} x ${item.get('unit_price')}"
                for item in quote.get("items", [])
            ])
            
            content = f"""Quote #{quote.get('token', 'N/A')}
Total: ${quote.get('total', 0)}
Status: {quote.get('status')}
Items:
{items_text}
"""
            
            rag.add_document(
                content=content,
                source=f"quote:{quote['id']}",
                doc_type="quote",
                metadata={"quote_id": quote["id"], "token": quote.get("token")}
            )
            ingested += 1
    
    return {"ingested": ingested, "message": f"Ingested {ingested} quotes into RAG"}


@router.post("/ingest/products")
async def ingest_all_products(
    user_org: tuple = Depends(get_current_user_and_org)
):
    """Ingest all products into RAG for searching."""
    from app.database_sqlite import list_products
    
    rag = get_rag_service()
    user_id, org_id = user_org
    products = list_products(organization_id=org_id, limit=1000)
    
    ingested = 0
    for p in products:
        content = f"""{p['name']} (SKU: {p['sku']})
Price: ${p['price']}
Category: {p.get('category', 'N/A')}
Description: {p.get('description', 'N/A')}
"""
        
        rag.add_document(
            content=content,
            source=f"product:{p['id']}",
            doc_type="product",
            metadata={"product_id": p["id"], "sku": p["sku"]}
        )
        ingested += 1
    
    return {"ingested": ingested, "message": f"Ingested {ingested} products into RAG"}
