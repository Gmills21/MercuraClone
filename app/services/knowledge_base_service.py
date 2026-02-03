"""
Product Knowledge Base Service (Optional Feature)
RAG-powered document search for product catalogs, spec sheets, pricing docs.

This module is completely isolated from core CRM functionality.
Enable via KNOWLEDGE_BASE_ENABLED=true in environment.
"""

import os
import hashlib
from typing import List, Dict, Any, Optional, Generator, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from loguru import logger

# Optional dependencies - gracefully degrade if missing
# Disable posthog telemetry before importing chromadb (Python 3.8 compatibility)
import os
os.environ['POSTHOG_DISABLED'] = 'true'
os.environ['CHROMA_TELEMETRY'] = 'false'

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

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class DocumentChunk:
    """A chunk of ingested document with metadata."""
    content: str
    source: str  # filename
    doc_type: str  # catalog, spec_sheet, pricing, etc.
    page: Optional[int] = None
    product_sku: Optional[str] = None
    chunk_index: int = 0


@dataclass
class KnowledgeQueryResult:
    """Result from knowledge base query."""
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    query_time_ms: int


class KnowledgeBaseService:
    """
    Optional product knowledge base using RAG.
    
    Completely separate from core CRM. Ingests product catalogs,
    spec sheets, pricing docs. Answers natural language queries
    about products, specs, pricing, availability.
    """
    
    def __init__(self):
        self.enabled = os.getenv("KNOWLEDGE_BASE_ENABLED", "false").lower() == "true"
        self.db_path = os.getenv("KNOWLEDGE_BASE_PATH", "./data/knowledge_base")
        self.collection_name = "product_documents"
        
        # Optional AI for enhanced answering - supports DeepSeek OR OpenRouter
        self.deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        self.ai_provider = None  # 'deepseek' or 'openrouter'
        self.ai_client = None
        self.ai_model = None
        
        if OPENAI_AVAILABLE:
            # Prefer DeepSeek if both are set (or only DeepSeek)
            if self.deepseek_key:
                self.ai_client = AsyncOpenAI(
                    base_url="https://api.deepseek.com/v1",
                    api_key=self.deepseek_key,
                )
                self.ai_provider = "deepseek"
                self.ai_model = "deepseek-chat"
                logger.info("Knowledge base using DeepSeek AI")
            elif self.openrouter_key:
                self.ai_client = AsyncOpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.openrouter_key,
                )
                self.ai_provider = "openrouter"
                self.ai_model = "deepseek/deepseek-chat:free"
                logger.info("Knowledge base using OpenRouter AI")
        
        # ChromaDB setup
        self.client = None
        self.collection = None
        self.embedder = None
        
        if self.enabled:
            self._initialize()
    
    def _initialize(self):
        """Initialize ChromaDB and embedder."""
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not installed. Knowledge base disabled.")
            self.enabled = False
            return
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("sentence-transformers not installed. Knowledge base disabled.")
            self.enabled = False
            return
        
        try:
            # Initialize ChromaDB (new API for 0.4.x)
            Path(self.db_path).mkdir(parents=True, exist_ok=True)
            
            # Use PersistentClient for local storage
            # Disable telemetry to avoid posthog compatibility issues
            settings = Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
            
            # Set env var to disable posthog before importing
            import os
            os.environ['POSTHOG_DISABLED'] = 'true'
            
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=settings
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            # Load embedder (lightweight model)
            logger.info("Loading sentence transformer model...")
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            
            logger.info(f"Knowledge base initialized at {self.db_path}")
            logger.info(f"Documents in collection: {self.collection.count()}")
            
        except Exception as e:
            import traceback
            logger.error(f"Failed to initialize knowledge base: {e}")
            logger.error(traceback.format_exc())
            self.enabled = False
    
    def is_available(self) -> bool:
        """Check if knowledge base is enabled and working."""
        return self.enabled and self.collection is not None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        if not self.is_available():
            return {
                "enabled": False,
                "available": False,
                "document_count": 0,
                "message": "Knowledge base not enabled or dependencies missing"
            }
        
        return {
            "enabled": True,
            "available": True,
            "document_count": self.collection.count(),
            "db_path": self.db_path,
            "ai_enhanced": self.ai_client is not None,
            "ai_provider": self.ai_provider,
            "ai_model": self.ai_model
        }
    
    def _extract_text_from_pdf(self, file_path: str) -> Generator[Tuple[int, str], None, None]:
        """
        Extract text from PDF page by page (memory efficient).
        
        Yields:
            Tuple of (page_number, text)
        """
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            
            logger.info(f"Processing PDF with {total_pages} pages")
            
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    text = page.extract_text()
                    if text and text.strip():
                        yield page_num, text.strip()
                except Exception as e:
                    logger.warning(f"Failed to extract page {page_num}: {e}")
                    continue
                    
        except ImportError:
            logger.error("pypdf not installed. Cannot process PDFs.")
            raise
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks."""
        if not text:
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to end at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                if last_period > chunk_size * 0.5:
                    chunk = chunk[:last_period + 1]
                    end = start + last_period + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return chunks
    
    async def ingest_document(
        self,
        file_path: str,
        doc_type: str = "unknown",
        metadata: Optional[Dict] = None,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> Dict[str, Any]:
        """
        Ingest a document into the knowledge base with page-by-page processing.
        
        Args:
            file_path: Path to document (PDF, TXT, MD)
            doc_type: Type of document (catalog, spec_sheet, pricing)
            metadata: Additional metadata (supplier, date, etc.)
            chunk_size: Size of text chunks
            overlap: Overlap between chunks
        
        Returns:
            Ingestion results
        """
        if not self.is_available():
            return {"error": "Knowledge base not available"}
        
        file = Path(file_path)
        if not file.exists():
            return {"error": f"File not found: {file_path}"}
        
        doc_id_base = hashlib.md5(file_path.encode()).hexdigest()[:12]
        total_chunks = 0
        pages_processed = 0
        start_time = datetime.now()
        
        try:
            logger.info(f"Ingesting {file_path} as {doc_type}")
            
            # Handle different file types
            if file.suffix.lower() == '.pdf':
                # Get total page count first for logging
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(file_path)
                    total_pages = len(reader.pages)
                    logger.info(f"Processing PDF with {total_pages} pages")
                except Exception as e:
                    logger.warning(f"Could not get page count: {e}")
                    total_pages = None
                
                # Process PDF page-by-page (memory efficient)
                for page_num, page_text in self._extract_text_from_pdf(file_path):
                    if not page_text:
                        continue
                    
                    # Chunk this page
                    chunks = self._chunk_text(page_text, chunk_size, overlap)
                    
                    # Store chunks in batches for better performance
                    batch_size = 10
                    for batch_start in range(0, len(chunks), batch_size):
                        batch_end = min(batch_start + batch_size, len(chunks))
                        batch_chunks = chunks[batch_start:batch_end]
                        
                        ids = []
                        embeddings = []
                        documents = []
                        metadatas = []
                        
                        for chunk_idx, chunk in enumerate(batch_chunks, batch_start):
                            global_chunk_idx = total_chunks + chunk_idx
                            chunk_id = f"{doc_id_base}_p{page_num}_c{chunk_idx}"
                            
                            embedding = self.embedder.encode(chunk).tolist()
                            
                            ids.append(chunk_id)
                            embeddings.append(embedding)
                            documents.append(chunk)
                            metadatas.append({
                                "source": file.name,  # Use filename only, not full path
                                "doc_type": doc_type,
                                "page": page_num,
                                "chunk_index": global_chunk_idx,
                                **(metadata or {})
                            })
                        
                        self.collection.add(
                            ids=ids,
                            embeddings=embeddings,
                            documents=documents,
                            metadatas=metadatas
                        )
                    
                    total_chunks += len(chunks)
                    pages_processed += 1
                    
                    # Log progress every 10 pages
                    if pages_processed % 10 == 0:
                        logger.info(f"Processed {pages_processed} pages, {total_chunks} chunks")
                
            elif file.suffix.lower() in ['.txt', '.md', '.markdown']:
                # Process text files normally
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                chunks = self._chunk_text(content, chunk_size, overlap)
                logger.info(f"Processing text file with {len(chunks)} chunks")
                
                # Store in batches
                batch_size = 50
                for batch_start in range(0, len(chunks), batch_size):
                    batch_end = min(batch_start + batch_size, len(chunks))
                    batch_chunks = chunks[batch_start:batch_end]
                    
                    ids = []
                    embeddings = []
                    documents = []
                    metadatas = []
                    
                    for i, chunk in enumerate(batch_chunks, batch_start):
                        chunk_id = f"{doc_id_base}_{i}"
                        embedding = self.embedder.encode(chunk).tolist()
                        
                        ids.append(chunk_id)
                        embeddings.append(embedding)
                        documents.append(chunk)
                        metadatas.append({
                            "source": file.name,
                            "doc_type": doc_type,
                            "chunk_index": i,
                            **(metadata or {})
                        })
                    
                    self.collection.add(
                        ids=ids,
                        embeddings=embeddings,
                        documents=documents,
                        metadatas=metadatas
                    )
                    
                    if batch_end % 100 == 0 or batch_end == len(chunks):
                        logger.info(f"Processed {batch_end}/{len(chunks)} chunks")
                
                total_chunks = len(chunks)
                pages_processed = 1
            else:
                return {"error": f"Unsupported file type: {file.suffix}"}
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Ingested {pages_processed} pages into {total_chunks} chunks in {elapsed:.1f}s")
            
            return {
                "success": True,
                "document_id": doc_id_base,
                "pages_processed": pages_processed,
                "chunks_created": total_chunks,
                "source": file.name,
                "doc_type": doc_type,
                "processing_time_seconds": elapsed
            }
            
        except Exception as e:
            import traceback
            logger.error(f"Document ingestion failed: {e}")
            logger.error(traceback.format_exc())
            return {
                "error": str(e),
                "partial_success": total_chunks > 0,
                "chunks_created": total_chunks,
                "pages_processed": pages_processed
            }
    
    async def query(
        self,
        question: str,
        top_k: int = 5,
        doc_types: Optional[List[str]] = None,
        use_ai: bool = True
    ) -> KnowledgeQueryResult:
        """
        Query the knowledge base with a natural language question.
        
        Args:
            question: Natural language query
            top_k: Number of chunks to retrieve
            doc_types: Filter by document types
            use_ai: Whether to use AI for answer synthesis
        
        Returns:
            Query result with answer and sources
        """
        import time
        start_time = time.time()
        
        if not self.is_available():
            return KnowledgeQueryResult(
                answer="Knowledge base is not enabled or available.",
                sources=[],
                confidence=0.0,
                query_time_ms=0
            )
        
        try:
            # Embed the query
            query_embedding = self.embedder.encode(question).tolist()
            
            # Search collection
            where_filter = {"doc_type": {"$in": doc_types}} if doc_types else None
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter
            )
            
            # Build context from retrieved chunks
            contexts = []
            sources = []
            
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i]
                
                contexts.append(doc)
                sources.append({
                    "content": doc[:300] + "..." if len(doc) > 300 else doc,
                    "source": metadata.get("source", "unknown"),
                    "doc_type": metadata.get("doc_type", "unknown"),
                    "page": metadata.get("page"),
                    "relevance_score": 1 - distance
                })
            
            # Generate answer
            if use_ai and self.ai_client:
                answer = await self._generate_ai_answer(question, contexts)
            else:
                answer = self._generate_basic_answer(question, contexts)
            
            # Calculate confidence
            avg_relevance = sum(s["relevance_score"] for s in sources) / len(sources) if sources else 0
            confidence = min(1.0, avg_relevance * (1.2 if use_ai and self.ai_client else 0.8))
            
            query_time_ms = int((time.time() - start_time) * 1000)
            
            return KnowledgeQueryResult(
                answer=answer,
                sources=sources,
                confidence=confidence,
                query_time_ms=query_time_ms
            )
            
        except Exception as e:
            logger.error(f"Knowledge base query failed: {e}")
            return KnowledgeQueryResult(
                answer=f"Error querying knowledge base: {str(e)}",
                sources=[],
                confidence=0.0,
                query_time_ms=int((time.time() - start_time) * 1000)
            )
    
    async def _generate_ai_answer(self, question: str, contexts: List[str]) -> str:
        """Generate answer using AI with retrieved contexts."""
        context_text = "\n\n---\n\n".join(contexts)
        
        prompt = f"""Answer the following question based ONLY on the provided context.
If the answer is not in the context, say "I don't have that information in the knowledge base."

CONTEXT:
{context_text}

QUESTION: {question}

Provide a concise, accurate answer. Include specific details (SKUs, prices, specs) when available."""

        try:
            response = await self.ai_client.chat.completions.create(
                model=self.ai_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions about products based on provided documentation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"AI answer generation failed ({self.ai_provider}/{self.ai_model}): {e}")
            return self._generate_basic_answer(question, contexts)
    
    def _generate_basic_answer(self, question: str, contexts: List[str]) -> str:
        """Generate basic answer without AI (fallback)."""
        if not contexts:
            return "No relevant information found in the knowledge base."
        
        answer_parts = ["Based on the knowledge base:"]
        
        for i, ctx in enumerate(contexts[:3], 1):
            preview = ctx[:200].replace('\n', ' ')
            answer_parts.append(f"\n{i}. {preview}...")
        
        answer_parts.append("\n\n(Enable AI enhancement for synthesized answers)")
        
        return "\n".join(answer_parts)
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete all chunks for a document."""
        if not self.is_available():
            return False
        
        try:
            # Find all chunks with this document prefix
            results = self.collection.get(
                where={"source": {"$contains": document_id}}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} chunks for {document_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False


# Global instance
_kb_service: Optional[KnowledgeBaseService] = None


def get_knowledge_base_service() -> KnowledgeBaseService:
    """Get or create knowledge base service instance."""
    global _kb_service
    if _kb_service is None:
        _kb_service = KnowledgeBaseService()
    return _kb_service
