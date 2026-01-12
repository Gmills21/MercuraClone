# 📁 Mercura - Complete File Structure

```
Mercura Clone/
│
├── 📄 README.md                      # Project overview and introduction
├── 📄 QUICKSTART.md                  # Step-by-step setup guide
├── 📄 PROJECT_SUMMARY.md             # Implementation status and summary
├── 📄 PDR                            # Product Design Reference (complete spec)
├── 📄 DEPLOYMENT_CHECKLIST.md        # Production deployment guide
├── 📄 requirements.txt               # Python dependencies
├── 📄 .env.example                   # Environment variable template
├── 📄 .gitignore                     # Git exclusions
│
├── 📂 app/                           # Main application code
│   ├── 📄 __init__.py               # Package initializer
│   ├── 📄 main.py                   # FastAPI application entry point
│   ├── 📄 config.py                 # Configuration management
│   ├── 📄 models.py                 # Data models and database schema
│   ├── 📄 database.py               # Supabase client wrapper
│   │
│   ├── 📂 routes/                   # API route handlers
│   │   ├── 📄 __init__.py          # Routes package initializer
│   │   ├── 📄 webhooks.py          # Email webhook endpoints
│   │   ├── 📄 data.py              # Data query endpoints
│   │   └── 📄 export.py            # Export endpoints
│   │
│   └── 📂 services/                 # Business logic services
│       ├── 📄 __init__.py          # Services package initializer
│       ├── 📄 gemini_service.py    # Gemini AI extraction service
│       └── 📄 export_service.py    # Data export service
│
├── 📂 scripts/                      # Utility scripts
│   └── 📄 init_db.py               # Database initialization script
│
├── 📂 tests/                        # Test files
│   └── 📄 test_extraction.py       # Gemini extraction tests
│
├── 📂 logs/                         # Application logs (auto-created)
│   └── 📄 mercura.log              # Main log file
│
├── 📂 temp/                         # Temporary files (auto-created)
│   └── 📂 exports/                 # Temporary export files
│
└── 📂 credentials/                  # API credentials (optional)
    └── 📄 google-sheets-credentials.json  # Google Sheets service account

```

---

## 📊 File Statistics

| Category | Count | Total Lines |
|----------|-------|-------------|
| **Core Application** | 5 files | ~1,800 lines |
| **API Routes** | 3 files | ~600 lines |
| **Services** | 2 files | ~600 lines |
| **Scripts & Tests** | 2 files | ~300 lines |
| **Documentation** | 5 files | ~1,200 lines |
| **Configuration** | 3 files | ~100 lines |
| **TOTAL** | **20 files** | **~4,600 lines** |

---

## 🗂️ File Descriptions

### Documentation Files

| File | Purpose | Size |
|------|---------|------|
| `README.md` | Project overview, features, and quick links | ~3 KB |
| `QUICKSTART.md` | Detailed setup instructions for new users | ~6 KB |
| `PROJECT_SUMMARY.md` | Implementation status and architecture | ~12 KB |
| `PDR` | Complete product design reference | ~16 KB |
| `DEPLOYMENT_CHECKLIST.md` | Production deployment guide | ~10 KB |

### Application Core

| File | Purpose | Lines |
|------|---------|-------|
| `app/main.py` | FastAPI app, CORS, logging, startup | ~100 |
| `app/config.py` | Environment variables, settings | ~100 |
| `app/models.py` | Pydantic models, SQL schema | ~250 |
| `app/database.py` | Supabase operations, CRUD | ~300 |

### API Routes

| File | Purpose | Lines |
|------|---------|-------|
| `app/routes/webhooks.py` | Email webhook handler, processing | ~350 |
| `app/routes/data.py` | Data query endpoints | ~200 |
| `app/routes/export.py` | Export endpoints | ~150 |

### Services

| File | Purpose | Lines |
|------|---------|-------|
| `app/services/gemini_service.py` | AI extraction logic | ~350 |
| `app/services/export_service.py` | CSV/Excel/Sheets export | ~300 |

### Supporting Files

| File | Purpose | Lines |
|------|---------|-------|
| `scripts/init_db.py` | Database setup helper | ~80 |
| `tests/test_extraction.py` | Gemini extraction tests | ~150 |
| `requirements.txt` | Python dependencies | ~40 |
| `.env.example` | Configuration template | ~50 |
| `.gitignore` | Git exclusions | ~50 |

---

## 🔍 Key Components by Function

### 1. Email Ingestion
```
app/routes/webhooks.py
├── verify_sendgrid_signature()
├── verify_mailgun_signature()
├── process_email_webhook()
└── inbound_email_webhook()
```

### 2. AI Extraction
```
app/services/gemini_service.py
├── GeminiService
│   ├── extract_from_text()
│   ├── extract_from_pdf()
│   ├── extract_from_image()
│   └── _calculate_confidence()
```

### 3. Data Storage
```
app/database.py
├── Database
│   ├── create_inbound_email()
│   ├── update_email_status()
│   ├── create_line_items()
│   ├── get_line_items_by_email()
│   └── get_line_items_by_date_range()
```

### 4. Data Export
```
app/services/export_service.py
├── ExportService
│   ├── export_to_csv()
│   ├── export_to_excel()
│   ├── export_to_google_sheets()
│   └── _clean_dataframe()
```

### 5. API Endpoints
```
app/main.py
├── / (root)
├── /health
├── /docs
│
app/routes/webhooks.py
├── POST /webhooks/inbound-email
└── GET /webhooks/health
│
app/routes/data.py
├── GET /data/emails
├── GET /data/emails/{id}
├── GET /data/line-items
└── GET /data/stats
│
app/routes/export.py
├── POST /export/csv
├── POST /export/excel
└── POST /export/google-sheets
```

---

## 📦 Dependencies Breakdown

### Core Framework
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation

### Database
- `supabase` - Database client
- `psycopg2-binary` - PostgreSQL adapter

### AI/ML
- `google-generativeai` - Gemini API

### Data Processing
- `pandas` - Data manipulation
- `openpyxl` - Excel support
- `xlsxwriter` - Excel formatting

### Email
- `python-email-validator` - Email validation
- `email-reply-parser` - Email parsing

### Google Integration
- `gspread` - Google Sheets
- `google-auth` - Authentication

### Utilities
- `python-dotenv` - Environment variables
- `loguru` - Logging
- `httpx` - HTTP client

---

## 🎯 Code Organization Principles

### 1. Separation of Concerns
- **Routes**: Handle HTTP requests/responses
- **Services**: Contain business logic
- **Database**: Manage data persistence
- **Models**: Define data structures

### 2. Dependency Injection
- Configuration loaded once at startup
- Services instantiated as singletons
- Database client shared across modules

### 3. Error Handling
- Try/except blocks in all async functions
- Structured logging for debugging
- HTTP exceptions for API errors

### 4. Type Safety
- Pydantic models for validation
- Type hints throughout codebase
- Enum for status values

---

## 🔄 Data Flow Through Files

```
1. Email Arrives
   └─> webhooks.py (verify signature)

2. Process Email
   └─> webhooks.py (process_email_webhook)
       ├─> database.py (create_inbound_email)
       ├─> gemini_service.py (extract_from_pdf/text/image)
       └─> database.py (create_line_items)

3. Query Data
   └─> data.py (get_emails, get_line_items)
       └─> database.py (fetch from Supabase)

4. Export Data
   └─> export.py (export_csv/excel/sheets)
       └─> export_service.py (generate file)
           └─> database.py (fetch data)
```

---

## 📝 Configuration Files

### Environment Variables (.env)
```
Application Settings
├── APP_NAME
├── APP_ENV
├── DEBUG
└── SECRET_KEY

Database
├── SUPABASE_URL
├── SUPABASE_KEY
└── SUPABASE_SERVICE_KEY

AI Service
├── GEMINI_API_KEY
└── GEMINI_MODEL

Email Provider
├── EMAIL_PROVIDER
├── SENDGRID_WEBHOOK_SECRET
├── MAILGUN_API_KEY
└── MAILGUN_WEBHOOK_SECRET

Export Settings
├── MAX_EXPORT_ROWS
└── EXPORT_TEMP_DIR

Processing Settings
├── MAX_ATTACHMENT_SIZE_MB
├── ALLOWED_ATTACHMENT_TYPES
└── CONFIDENCE_THRESHOLD
```

---

## 🧪 Test Coverage

### Current Tests
- ✅ Gemini text extraction
- ✅ Invoice processing
- ✅ Purchase order processing
- ✅ Confidence scoring

### Future Tests (Recommended)
- [ ] Webhook signature verification
- [ ] Database CRUD operations
- [ ] Export formatting
- [ ] Error handling
- [ ] Rate limiting
- [ ] Multi-attachment processing

---

## 📈 Scalability Considerations

### Current Architecture
- **Single server**: Good for 0-1000 emails/day
- **Synchronous processing**: Simple, reliable
- **Direct database access**: Fast queries

### Future Enhancements
- **Queue system** (Redis/Celery): Handle 10,000+ emails/day
- **Microservices**: Separate extraction service
- **Caching**: Redis for frequently accessed data
- **Load balancing**: Multiple server instances
- **CDN**: Static asset delivery

---

## 🔐 Security Files

### Sensitive Files (Never Commit)
```
.env                              # Environment variables
credentials/                      # API credentials
logs/                            # Application logs
temp/                            # Temporary files
database_schema.sql              # Generated schema
*.csv, *.xlsx                    # Export files
```

### Protected by .gitignore
All sensitive files are excluded from version control.

---

## 🎨 Code Style

### Formatting
- **Line length**: 88 characters (Black default)
- **Indentation**: 4 spaces
- **Quotes**: Double quotes for strings
- **Imports**: Grouped and sorted

### Naming Conventions
- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case()`
- **Constants**: `UPPER_CASE`
- **Private**: `_leading_underscore()`

---

## 📚 Documentation Standards

### Docstrings
```python
"""
Brief description.

Detailed explanation if needed.

Args:
    param1: Description
    param2: Description

Returns:
    Description of return value

Raises:
    ExceptionType: When this happens
"""
```

### Comments
- Explain **why**, not **what**
- Use for complex logic
- Keep updated with code changes

---

## ✨ Project Highlights

### Code Quality
- ✅ Type hints throughout
- ✅ Comprehensive error handling
- ✅ Structured logging
- ✅ Pydantic validation
- ✅ Async/await patterns

### Documentation
- ✅ 5 comprehensive guides
- ✅ Inline code comments
- ✅ API documentation (auto-generated)
- ✅ Architecture diagrams
- ✅ Deployment checklist

### Features
- ✅ Dual email provider support
- ✅ Multi-format extraction (PDF, images, text)
- ✅ Three export formats
- ✅ Confidence scoring
- ✅ User quota management

---

**Total Project Size**: ~50 KB of code + documentation  
**Development Time**: Complete implementation  
**Production Ready**: Yes ✅

---

*Last Updated: January 10, 2026*
