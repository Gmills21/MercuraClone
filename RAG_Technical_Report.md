# Tailored Technical Report: RAG & Vector Knowledge Base Configuration

**Prepared for:** OpenMercura Technical Team
**Objective:** Enable "Zero-Error" quoting through robust local technical knowledge ingestion.

---

## 1. System Architecture: The "Brain" Components

To achieve Grade A extraction and technical research capabilities, OpenMercura utilizes two core libraries that operate entirely locally, ensuring data privacy and compliance with trade standards.

### A. ChromaDB (The Local Vector Memory)
*   **Role:** Acts as the long-term memory for your application.
*   **Storage:** Data is stored in `./data/chroma`. It is a persistent SQLite-backed vector store.
*   **Privacy:** Unlike cloud-based vector stores (like Pinecone), ChromaDB runs locally. Customer data NEVER leaves your infrastructure for indexing.
*   **Technical Spec:** Uses HNSW (Hierarchical Navigable Small World) graphs for fast similarity searching.

### B. Sentence-Transformers (The Semantic Interpreter)
*   **Role:** Translates technical text into mathematical vectors.
*   **Model:** `all-MiniLM-L6-v2`.
*   **Capabilities:** Understands deep technical context. For example, it recognizes that *"250 PSI"* and *"high-pressure rated"* are semantically related, even if the words don't match exactly.
*   **Performance:** Optimized for CPU usage, allowing for fast searches without expensive GPU hardware.

---

## 2. Technical Configuration & Integration

### Startup Detection Logic
The `app.main:startup_event` has been configured to perform a "System Health Check" for RAG services. 

```python
# app/main.py snippet
from app.rag_service import get_rag_service
rag_service = get_rag_service()
if rag_service.is_available():
    logger.info("RAG service initialized (ChromaDB + sentence-transformers)")
else:
    logger.warning("RAG service not available - Knowledge Base tab will be disabled")
```

### Dashboard Impact
Once these libraries are installed:
1.  **Status Change:** The "Knowledge Base" tab in the dashboard transitions from "Disabled" to "Active".
2.  **Test 1 Capability:** The system can now ingest technical documents (PDFs, Catalogs) and cite them during the quoting process.
3.  **Trust Signals:** Page number citations and technical spec side-bars will now populate with real data retrieved from the local store.

---

## 3. Maintenance and Scalability
*   **Dependency Management:** `chromadb` and `sentence-transformers` are pinned in `requirements.txt` to ensure consistent deployments.
*   **Data Isolation:** Each organization has its own logical separation within the vector store (if configured) or separate collections can be used to prevent cross-tenant data leakage.

---

**Next Steps:**
1.  Upload a technical catalog (e.g., Nitra Catalog) via the Knowledge Base.
2.  Perform a "Smart Quote" extraction to verify that the RAG service provides relevant technical matching and alternatives.
