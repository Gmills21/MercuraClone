# Unimplemented Features

This document tracks features that require paid resources and could not be implemented with 100% free workarounds.

## Email Integration (SendGrid/Mailgun)

**Why:** Email webhook processing requires a domain with MX records and either SendGrid or Mailgun.

**Workaround:**
- Manual CSV upload for data import
- Chrome extension for Gmail/Outlook extraction
- API endpoints accept raw text directly

**Status:** Commented out in config - email_provider defaults to "none"

---

## Vector Search with Embeddings

**Why:** ChromaDB and sentence-transformers require significant disk space (~500MB+ for models) and may not work in all environments.

**Workaround:**
- SQLite full-text search (fallback)
- Keyword-based search on products/quotes

**Status:** RAG service gracefully degrades when dependencies unavailable

---

## Advanced AI Features

**Why:** OpenRouter free tier has rate limits (20 requests/minute). Heavy usage requires paid tier.

**Workaround:**
- Implemented with free tier
- Rate limiting handled gracefully
- Local processing for simple operations

**Status:** Functional with free tier, may hit limits under heavy load

---

## Note

All core functionality is implemented using free alternatives. This file serves as documentation for any limitations encountered.
