"""
Smart Search & Retrieval Service (RAG) for OpenMercura
Free implementation using ChromaDB and local HuggingFace embeddings
"""

import json
import logging
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import numpy as np

logger = logging.getLogger(__name__)

# Try to import ChromaDB
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not installed. RAG features will be limited.")

# Try to import sentence-transformers for local embeddings
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning("sentence-transformers not installed. Using fallback embeddings.")


@dataclass
class Document:
    """Document for RAG storage."""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


@dataclass
class SearchResult:
    """Search result from vector store."""
    document: Document
    score: float


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.dimension = 384  # MiniLM dimension
        
        if EMBEDDINGS_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
                logger.info(f"Loaded embedding model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                self.model = None
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        if self.model:
            try:
                embeddings = self.model.encode(texts, convert_to_list=True)
                return embeddings
            except Exception as e:
                logger.error(f"Embedding generation failed: {e}")
        
        # Fallback: simple hash-based embeddings (not semantic, but deterministic)
        return self._fallback_embeddings(texts)
    
    def _fallback_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate simple fallback embeddings using hashing."""
        embeddings = []
        for text in texts:
            # Create a deterministic hash-based embedding
            hash_val = hashlib.md5(text.lower().encode()).hexdigest()
            # Convert to a vector of 384 dimensions
            vector = []
            for i in range(0, len(hash_val), 2):
                val = int(hash_val[i:i+2], 16) / 255.0
                vector.append(val)
            # Pad or truncate to dimension
            while len(vector) < self.dimension:
                vector.extend(vector[:self.dimension - len(vector)])
            embeddings.append(vector[:self.dimension])
        return embeddings


class RAGService:
    """
    Retrieval-Augmented Generation Service.
    Provides smart search over documents using vector similarity.
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.embedding_service = EmbeddingService()
        self.client = None
        self.collection = None
        
        if CHROMADB_AVAILABLE:
            try:
                self.client = chromadb.Client(Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=persist_directory
                ))
                self._get_or_create_collection()
                logger.info("RAG service initialized with ChromaDB")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB: {e}")
                self.client = None
        else:
            # Fallback: in-memory storage
            self.memory_store: Dict[str, Document] = {}
            logger.info("RAG service using in-memory storage")
    
    def _get_or_create_collection(self, collection_name: str = "documents"):
        """Get or create a ChromaDB collection."""
        if self.client:
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
    
    async def add_document(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> str:
        """
        Add a document to the vector store.
        
        Args:
            content: Document text content
            metadata: Optional metadata dict
            doc_id: Optional document ID (generated if not provided)
            
        Returns:
            Document ID
        """
        if metadata is None:
            metadata = {}
        
        # Generate ID if not provided
        if doc_id is None:
            doc_id = hashlib.md5(content.encode()).hexdigest()
        
        # Generate embedding
        embeddings = self.embedding_service.embed([content])
        embedding = embeddings[0]
        
        # Add timestamp
        metadata["created_at"] = datetime.utcnow().isoformat()
        metadata["content_preview"] = content[:200]
        
        if self.collection:
            # Store in ChromaDB
            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata]
            )
            # Persist
            self.client.persist()
        else:
            # Store in memory
            self.memory_store[doc_id] = Document(
                id=doc_id,
                content=content,
                metadata=metadata,
                embedding=embedding
            )
        
        return doc_id
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Add multiple documents.
        
        Args:
            documents: List of {content, metadata, id} dicts
            
        Returns:
            List of document IDs
        """
        ids = []
        for doc in documents:
            doc_id = await self.add_document(
                content=doc["content"],
                metadata=doc.get("metadata"),
                doc_id=doc.get("id")
            )
            ids.append(doc_id)
        return ids
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.5
    ) -> List[SearchResult]:
        """
        Search for similar documents.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            threshold: Minimum similarity score (0-1)
            
        Returns:
            List of SearchResult
        """
        # Generate query embedding
        query_embedding = self.embedding_service.embed([query])[0]
        
        results = []
        
        if self.collection:
            # Search ChromaDB
            chroma_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Convert to SearchResult
            for i in range(len(chroma_results["ids"][0])):
                score = 1 - chroma_results["distances"][0][i]  # Convert distance to similarity
                if score >= threshold:
                    doc = Document(
                        id=chroma_results["ids"][0][i],
                        content=chroma_results["documents"][0][i],
                        metadata=chroma_results["metadatas"][0][i]
                    )
                    results.append(SearchResult(document=doc, score=score))
        else:
            # Search in memory
            for doc in self.memory_store.values():
                score = self._cosine_similarity(query_embedding, doc.embedding)
                if score >= threshold:
                    results.append(SearchResult(document=doc, score=score))
            
            # Sort by score
            results.sort(key=lambda x: x.score, reverse=True)
            results = results[:top_k]
        
        return results
    
    async def chat_with_data(
        self,
        query: str,
        context_window: int = 3
    ) -> Dict[str, Any]:
        """
        Chat with your data using RAG.
        
        Args:
            query: User question
            context_window: Number of documents to include as context
            
        Returns:
            Response with answer and sources
        """
        # Search for relevant documents
        results = await self.search(query, top_k=context_window, threshold=0.3)
        
        if not results:
            return {
                "answer": "I don't have enough information to answer that question.",
                "sources": [],
                "confidence": 0.0
            }
        
        # Build context from retrieved documents
        context_parts = []
        for i, result in enumerate(results):
            context_parts.append(f"Document {i+1}: {result.document.content}")
        
        context = "\n\n".join(context_parts)
        
        # Generate response using the context
        # In a full implementation, this would call an LLM
        # For now, return a structured response with the context
        answer = self._generate_simple_answer(query, results)
        
        return {
            "answer": answer,
            "sources": [
                {
                    "id": r.document.id,
                    "content_preview": r.document.content[:200],
                    "score": round(r.score, 3),
                    "metadata": r.document.metadata
                }
                for r in results
            ],
            "confidence": round(sum(r.score for r in results) / len(results), 3)
        }
    
    def _generate_simple_answer(self, query: str, results: List[SearchResult]) -> str:
        """Generate a simple answer from search results."""
        if not results:
            return "No relevant information found."
        
        # Simple keyword matching answer
        query_lower = query.lower()
        
        # Check for common question types
        if any(word in query_lower for word in ['what', 'describe', 'explain']):
            return f"Based on your documents: {results[0].document.content[:500]}..."
        
        if any(word in query_lower for word in ['how many', 'count', 'number']):
            return f"I found {len(results)} relevant documents. The most relevant states: {results[0].document.content[:300]}..."
        
        # Default response
        return f"Here's what I found: {results[0].document.content[:400]}..."
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the store."""
        try:
            if self.collection:
                self.collection.delete(ids=[doc_id])
                self.client.persist()
            elif doc_id in self.memory_store:
                del self.memory_store[doc_id]
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False
    
    async def list_documents(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Document]:
        """List all documents in the store."""
        if self.collection:
            results = self.collection.get(
                limit=limit,
                offset=offset,
                include=["documents", "metadatas"]
            )
            
            documents = []
            for i in range(len(results["ids"])):
                documents.append(Document(
                    id=results["ids"][i],
                    content=results["documents"][i],
                    metadata=results["metadatas"][i]
                ))
            return documents
        else:
            docs = list(self.memory_store.values())
            return docs[offset:offset + limit]
    
    def _cosine_similarity(self, a: List[float], b: Optional[List[float]]) -> float:
        """Calculate cosine similarity between two vectors."""
        if b is None:
            return 0.0
        
        a_vec = np.array(a)
        b_vec = np.array(b)
        
        norm_a = np.linalg.norm(a_vec)
        norm_b = np.linalg.norm(b_vec)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(np.dot(a_vec, b_vec) / (norm_a * norm_b))
    
    async def index_quotes(self, quotes: List[Dict[str, Any]]):
        """Index quote data for search."""
        for quote in quotes:
            content = f"Quote {quote.get('quote_number', 'N/A')}: "
            content += f"Customer: {quote.get('customer_name', 'Unknown')}. "
            content += f"Total: ${quote.get('total_amount', 0)}. "
            content += f"Status: {quote.get('status', 'unknown')}."
            
            await self.add_document(
                content=content,
                metadata={
                    "type": "quote",
                    "quote_id": quote.get('id'),
                    "quote_number": quote.get('quote_number'),
                    "customer_id": quote.get('customer_id')
                }
            )
    
    async def index_products(self, products: List[Dict[str, Any]]):
        """Index product catalog for search."""
        for product in products:
            content = f"Product: {product.get('name', 'N/A')}. "
            content += f"SKU: {product.get('sku', 'N/A')}. "
            if product.get('description'):
                content += f"Description: {product['description']}. "
            content += f"Price: ${product.get('price', 0)}."
            
            await self.add_document(
                content=content,
                metadata={
                    "type": "product",
                    "product_id": product.get('id'),
                    "sku": product.get('sku'),
                    "category": product.get('category')
                }
            )


# Global service instance
rag_service = RAGService()
