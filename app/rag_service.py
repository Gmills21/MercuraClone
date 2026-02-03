"""
RAG (Retrieval-Augmented Generation) service using ChromaDB.
Free, local vector database - no paid cloud services.
"""

import os
import uuid
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

# Handle optional ChromaDB dependency
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from loguru import logger

# ChromaDB storage path
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "chroma")
os.makedirs(CHROMA_DIR, exist_ok=True)


class RAGService:
    """RAG service using local ChromaDB."""
    
    def __init__(self, collection_name: str = "mercura_docs"):
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.embedding_model = None
        self._initialized = False
        
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not installed. RAG features will be disabled.")
            return
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("sentence-transformers not installed. RAG features will be disabled.")
            return
        
        try:
            # Initialize ChromaDB client (new API for chromadb >= 0.4.0)
            self.client = chromadb.PersistentClient(path=CHROMA_DIR)
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            # Load embedding model (lightweight, runs locally)
            # Using all-MiniLM-L6-v2 - small, fast, free
            logger.info("Loading embedding model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            self._initialized = True
            logger.info("RAG service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            self._initialized = False
    
    def is_available(self) -> bool:
        """Check if RAG service is available."""
        return self._initialized and CHROMADB_AVAILABLE and SENTENCE_TRANSFORMERS_AVAILABLE
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector
        """
        if not self.embedding_model:
            raise RuntimeError("Embedding model not loaded")
        
        return self.embedding_model.encode(text).tolist()
    
    def add_document(
        self,
        content: str,
        source: str,
        doc_type: str = "generic",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a document to the RAG database.
        
        Args:
            content: Document content
            source: Source identifier (URL, filename, etc.)
            doc_type: Document type (quote, product, email, etc.)
            metadata: Additional metadata
        
        Returns:
            Document ID
        """
        if not self.is_available():
            logger.warning("RAG service not available, skipping document add")
            return ""
        
        doc_id = str(uuid.uuid4())
        embedding = self.embed_text(content)
        
        doc_metadata = {
            "source": source,
            "type": doc_type,
            "created_at": datetime.utcnow().isoformat(),
            **(metadata or {})
        }
        
        try:
            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[doc_metadata]
            )
            logger.info(f"Added document {doc_id} from {source}")
            return doc_id
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return ""
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        doc_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            n_results: Number of results to return
            doc_type: Filter by document type
        
        Returns:
            List of search results with scores
        """
        if not self.is_available():
            logger.warning("RAG service not available, returning empty results")
            return []
        
        try:
            query_embedding = self.embed_text(query)
            
            where_filter = None
            if doc_type:
                where_filter = {"type": doc_type}
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter
            )
            
            # Format results
            formatted = []
            if results["ids"] and len(results["ids"]) > 0:
                for i in range(len(results["ids"][0])):
                    formatted.append({
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "score": results["distances"][0][i] if results["distances"] else 0.0
                    })
            
            return formatted
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID."""
        if not self.is_available():
            return False
        
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        if not self.is_available():
            return {"available": False}
        
        try:
            count = self.collection.count()
            return {
                "available": True,
                "document_count": count,
                "collection_name": self.collection_name
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"available": False, "error": str(e)}


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create RAG service singleton."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


async def chat_with_data(
    query: str,
    context_messages: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Chat with your data using RAG.
    
    Args:
        query: User question
        context_messages: Previous messages for context
    
    Returns:
        Response with sources
    """
    rag = get_rag_service()
    
    if not rag.is_available():
        return {
            "response": "RAG service is not available. Please ensure ChromaDB and sentence-transformers are installed.",
            "sources": [],
            "available": False
        }
    
    # Search for relevant documents
    results = rag.search(query, n_results=5)
    
    if not results:
        return {
            "response": "I couldn't find any relevant documents to answer your question.",
            "sources": [],
            "available": True
        }
    
    # Build context from search results
    context_parts = []
    for i, result in enumerate(results[:3], 1):  # Use top 3
        context_parts.append(f"[Document {i}]\n{result['content'][:500]}")
    
    context = "\n\n".join(context_parts)
    
    # Build prompt
    prompt = f"""Based on the following documents, answer the user's question.

Documents:
{context}

User Question: {query}

Answer:"""

    # Use DeepSeek for response generation
    from app.deepseek_service import get_deepseek_service
    deepseek = get_deepseek_service()
    
    messages = [{"role": "user", "content": prompt}]
    if context_messages:
        messages = context_messages + messages
    
    result = await deepseek.chat_completion(messages, temperature=0.7)
    
    if "error" in result:
        return {
            "response": f"Error generating response: {result['error']}",
            "sources": results,
            "available": True
        }
    
    try:
        response_text = result["choices"][0]["message"]["content"]
        return {
            "response": response_text,
            "sources": results,
            "available": True
        }
    except (KeyError, IndexError) as e:
        return {
            "response": "Error parsing response from AI model.",
            "sources": results,
            "available": True
        }
