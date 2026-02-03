# Product Knowledge Base (Optional Feature)

**Status:** Optional module - OpenMercura works perfectly without it

## Overview

AI-powered document search for product catalogs, spec sheets, and pricing documents. Sales reps can ask natural language questions like "What's the lead time on XT-400 valves?" and get instant answers from ingested documentation.

## Why It's Optional

1. **Not everyone has digitized catalogs** - Some distributors still work with paper/phone
2. **Adds dependencies** - Requires ChromaDB and sentence-transformers
3. **Resource usage** - Vector DB and embeddings use disk/RAM
4. **Core CRM is complete** - Quoting, customers, products work without it

## Enable the Feature

### 1. Install Dependencies

```bash
pip install chromadb sentence-transformers
```

### 2. Set Environment Variable

```bash
# .env file
KNOWLEDGE_BASE_ENABLED=true
KNOWLEDGE_BASE_PATH=./data/knowledge_base  # Optional, default shown
```

### 3. Restart the Server

Knowledge base initializes on startup if enabled.

## How It Works

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Upload Doc     │────▶│  Extract Text    │────▶│  Chunk & Embed  │
│  (PDF/TXT/MD)   │     │  (NuMarkdown*)   │     │  (ChromaDB)     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                            │
┌─────────────────┐     ┌──────────────────┐               │
│  Show Answer    │◄────│  AI Synthesis    │◄──────────────┘
│  + Sources      │     │  (OpenRouter)    │
└─────────────────┘     └──────────────────┘
        ▲
        │
┌─────────────────┐
│  Natural Lang   │
│  Query          │
└─────────────────┘
```

*NuMarkdown integration is planned for PDF/image OCR - currently text files work directly

## API Endpoints

### Check Status
```
GET /knowledge/status
```
Returns: enabled, available, document_count, ai_enhanced

### Query
```
POST /knowledge/query
Content-Type: multipart/form-data

question: "What's the lead time on XT-400?"
doc_types: "spec_sheet,pricing"  # Optional filter
use_ai: true                     # Synthesize answer (default: true)
```

### Ingest Document
```
POST /knowledge/ingest
Content-Type: multipart/form-data

file: <document.pdf>
doc_type: "catalog"  # catalog, spec_sheet, pricing, manual, datasheet
supplier: "Acme Corp"  # Optional
notes: "Q1 2024 pricing"  # Optional
```

### List Documents
```
GET /knowledge/documents
```

### Delete Document
```
DELETE /knowledge/documents/{document_id}
```

## Document Types

| Type | Description | Example Questions |
|------|-------------|-------------------|
| catalog | Product catalogs | "Do you carry 3-inch ball valves?" |
| spec_sheet | Technical specs | "What's the pressure rating on XT-400?" |
| pricing | Price lists | "What's the price break at 100 units?" |
| manual | Product manuals | "How do I install the XT-400?" |
| datasheet | Technical datasheets | "What materials is the seal made of?" |

## Frontend Component

```tsx
import { KnowledgeBaseSearch } from '../components/KnowledgeBaseSearch';

// Use anywhere - gracefully handles disabled state
<KnowledgeBaseSearch />
```

When KB is disabled, shows friendly message explaining how to enable.

## Architecture

### Complete Isolation

```
app/
├── services/
│   ├── extraction_engine.py      # Core CRM - extraction
│   ├── onboarding_service.py     # Core CRM - onboarding
│   └── knowledge_base_service.py # ← OPTIONAL - isolated
├── routes/
│   ├── extraction_unified.py     # Core CRM
│   └── knowledge_base.py         # ← OPTIONAL - isolated
```

- No imports from knowledge base into core services
- Core CRM never checks if KB is enabled
- KB fails gracefully if dependencies missing

### Dependencies

| Dependency | Required For | Fallback |
|------------|--------------|----------|
| chromadb | Vector storage | Feature disabled |
| sentence-transformers | Embeddings | Feature disabled |
| openrouter (optional) | AI synthesis | Basic concatenation |

## Use Cases

### Scenario 1: Quick Spec Lookup
**Before:** Rep searches through 50-page PDF, calls supplier
**After:** "What's the max temp for XT-400?" → Instant answer

### Scenario 2: Pricing Questions
**Before:** Rep opens Excel, searches for SKU, checks price tier
**After:** "Price for 50 units of ABC-123?" → Instant answer with volume break

### Scenario 3: New Hire Training
**Before:** 3 months to learn product line
**After:** Ask AI anything, get instant answers from docs

## Future Enhancements

1. **NuMarkdown Integration** - OCR for PDFs and images
2. **Auto-ingestion** - Watch folder for new documents
3. **Supplier APIs** - Direct sync from supplier portals
4. **Multi-tenant** - Separate KBs per customer segment

## Migration Path

### Enable Later
User starts with KB disabled, enables after 6 months:
1. Install dependencies
2. Set KNOWLEDGE_BASE_ENABLED=true
3. Upload existing catalogs
4. Start using immediately

### Disable
User tries KB, decides not needed:
1. Set KNOWLEDGE_BASE_ENABLED=false
2. Delete ./data/knowledge_base folder
3. Core CRM continues normally

## Performance

| Metric | Value |
|--------|-------|
| Query latency | 100-500ms |
| Embedding model | all-MiniLM-L6-v2 (80MB) |
| Chunk size | 500 tokens |
| Overlap | 50 tokens |
| Max chunks/query | 5 |

## Security Notes

- Documents stored locally in ChromaDB
- No cloud vector DB (privacy)
- File uploads validated
- Path traversal prevented

---

**Remember:** This is a bonus feature. The CRM is complete without it.
