# MercuraClone - AI-Driven "Speed-as-a-Weapon" Platform

**Version:** 1.0
**Last Updated:** January 29, 2026
**Status:** Active Development

---

## Executive Summary

MercuraClone is an AI-powered quote automation platform that transforms the competitive landscape for industrial distributors by enabling "First-to-Quote" advantage through semantic matching and automated workflows. Our platform unifies a high-velocity Browser Extension for data capture with a precision Web Dashboard for review and management, all powered by Gemini AI semantic matching rather than costly ERP integrations.

**Core Value Proposition:** Replicate Mercura's high-performance quoting without enterprise ERP costs by perfecting AI-driven parsing of "dirty" email data and technical PDFs, prioritizing velocity and scale over rigid regulatory precision.

**Strategic Focus:** US market emphasis on speed-to-quote, leveraging semantic search and self-learning AI to match products without live ERP connections.

---

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Browser        │     │   FastAPI       │     │   Gemini AI     │
│  Extension      │────▶│   Backend       │────▶│   Service       │
│  (Capture)      │     │   (Processing)  │     │  (Semantic      │
│                 │     │                 │     │   Matching)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         │ Forward RFQ Email     │ Extract & Structure  │ Match Products
         │ (PDF/Excel/Email)     │ Data via AI          │ via Vector Search
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Web Dashboard │     │   Supabase      │     │   Export        │
│   (Review &     │◀────│   Database      │────▶│   Formats       │
│    Management)  │     │   (Storage)     │     │  (Excel/PDF)    │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Data Flow:**
1. **Capture Phase:** Browser Extension detects and forwards RFQ emails with attachments to API
2. **Processing Phase:** FastAPI receives webhooks, extracts data using Gemini AI
3. **Matching Phase:** Semantic search matches extracted items against catalog using vector embeddings
4. **Review Phase:** Web Dashboard presents draft quotes for human validation and approval
5. **Output Phase:** Generate formatted quotes (Excel/PDF) or export for ERP systems

---

## Technology Stack

### Core Components
- **Frontend:** React/TypeScript (Web Dashboard + Browser Extension)
- **Backend:** FastAPI/Python (API and processing)
- **AI Engine:** Google Gemini 1.5 Flash (extraction and embeddings)
- **Database:** Supabase PostgreSQL with Vector extension
- **Email Processing:** SendGrid Inbound Parse / Mailgun Routes
- **Data Export:** Pandas for CSV/Excel generation

### Key Features
- **AI Specs Parsing:** Gemini-powered extraction from messy PDFs, Excel files, and email bodies
- **Email Automation:** Inbound webhook processing for seamless RFQ ingestion
- **Semantic Matching:** Vector-based product matching without direct ERP hooks
- **Competitor Mapping:** Manual upload of competitor SKU cross-references for improved accuracy
- **Draft Quote Generation:** Automated creation of reviewable quotes from extracted data
- **Web Dashboard:** Human-in-the-loop review interface for quote validation
- **Export Formats:** Excel and PDF generation for customer delivery

---

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Supabase account
- Google Cloud account (for Gemini API)
- SendGrid or Mailgun account

### Installation

```bash
# Backend setup
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python scripts/init_db.py

# Frontend setup
cd frontend
npm install
npm run dev

# Run backend
uvicorn app.main:app --reload
```

### Environment Variables
See `.env.example` for required configuration including:
- SUPABASE_URL & SUPABASE_KEY
- GEMINI_API_KEY
- EMAIL_PROVIDER settings
- Database credentials

---

## Project Structure

```
MercuraClone/
├── app/                          # FastAPI Backend
│   ├── main.py                   # Application entry point
│   ├── config.py                 # Configuration management
│   ├── models.py                 # Database models & schemas
│   ├── database.py               # Supabase client
│   ├── routes/                   # API endpoints
│   │   ├── webhooks.py          # Email webhook handlers
│   │   ├── data.py              # Data queries
│   │   ├── export.py            # Export functionality
│   │   └── quotes.py            # Quote management
│   └── services/                # Business logic
│       ├── gemini_service.py    # AI extraction
│       └── export_service.py    # Data export
├── frontend/                     # React Web Application
│   ├── src/
│   │   ├── chrome/              # Browser Extension
│   │   │   ├── content.js       # Content script
│   │   │   ├── popup.html       # Extension popup
│   │   │   └── manifest.json    # Extension config
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/               # Application pages
│   │   └── services/            # Frontend API services
│   └── vite.config.ts           # Build configuration
├── scripts/                      # Utility scripts
│   ├── init_db.py               # Database setup
│   └── seed_data.py             # Sample data
├── docs/                        # Documentation
├── archive/                     # Legacy research materials
├── tests/                       # Test suite
├── .env.example                 # Environment template
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## Development Roadmap

### Phase 1: Foundation (Current)
- ✅ Browser Extension integration for RFQ detection
- ✅ Webhook processing for inbound emails
- ✅ Gemini AI extraction pipeline
- ✅ Basic quote creation and review UI
- ✅ Competitor mapping upload functionality

### Phase 2: Intelligence (Next)
- 🔄 Vector database setup for semantic search
- 🔄 Multi-layered matching engine (X-Ref → Exact → Fuzzy → Semantic)
- 🔄 Confidence scoring and validation rules
- 🔄 Enhanced review UI with bulk approval

### Phase 3: Scale & Automation
- 📋 Automated UOM conversion
- 📋 Bulk processing capabilities
- 📋 Advanced export formats for ERP systems
- 📋 Email automation for quote delivery
- 📋 Performance analytics dashboard

---

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

### Key Endpoints
- `POST /webhooks/inbound-email` - Receive and process emails
- `GET /data/emails` - List processed emails
- `GET /data/emails/{id}` - Get email details with line items
- `POST /export/csv` - Export data as CSV
- `POST /export/excel` - Export data as Excel

---

## Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| Email processing time | < 10s | ✅ Achieved |
| Extraction accuracy | > 80% | ✅ Achieved |
| Time-to-First-Quote | < 10 minutes | 🔄 In Progress |
| Automation rate | > 70% | 📋 Planned |

---

## Contributing

### For All Contributors
1. Review `PROJECT_REFERENCE.md` for technical guidelines
2. Check `MasterProjectRoadmap.md` for architectural decisions
3. Follow the established tech stack and patterns
4. Test changes against the existing test suite

### For AI Agents
- **MANDATORY:** Review `PROJECT_REFERENCE.md` before any code generation
- Adhere to the "Lite" rule: No vector search or RAG unless explicitly requested
- Prioritize Gemini 1.5 Flash for AI operations
- Handle "messy" inputs gracefully with proper error handling

---

## License

MIT License - see LICENSE file for details.

---

**Built with ❤️ using FastAPI, React, Gemini AI, and Supabase**
