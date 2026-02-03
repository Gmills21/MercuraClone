# OpenMercura - Repository Mix

## Project Overview
Generated: 2026-01-31

## Table of Contents
1. [Project Structure](#project-structure)
2. [Configuration Files](#configuration-files)
3. [Backend (Python)](#backend-python)
4. [Frontend (TypeScript/React)](#frontend-typescriptreact)
5. [Documentation](#documentation)

---

## Project Structure

```
MercuraClone/
├── app/                          # Backend Python application
│   ├── __init__.py
│   ├── main.py                   # FastAPI entry point
│   ├── config.py                 # Configuration settings
│   ├── database_sqlite.py        # SQLite database layer
│   ├── models.py                 # Pydantic models
│   ├── routes/                   # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── customers.py
│   │   ├── products.py
│   │   ├── quotes.py
│   │   ├── alerts.py
│   │   ├── quickbooks.py
│   │   ├── intelligence.py
│   │   ├── impact.py
│   │   └── ...
│   ├── services/                 # Business logic services
│   │   ├── __init__.py
│   │   ├── email_service.py
│   │   └── ...
│   ├── alert_service.py
│   ├── quickbooks_service.py
│   ├── customer_intelligence_service.py
│   ├── business_impact_service.py
│   ├── onboarding_service.py
│   └── ...
├── frontend/                     # React frontend
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── Layout.tsx
│   │   │   ├── NotificationCenter.tsx
│   │   │   ├── GettingStarted.tsx
│   │   │   └── ui/               # UI primitives
│   │   ├── pages/                # Page components
│   │   │   ├── TodayView.tsx
│   │   │   ├── SmartQuote.tsx
│   │   │   ├── BusinessImpact.tsx
│   │   │   ├── IntelligenceDashboard.tsx
│   │   │   ├── CameraCapture.tsx
│   │   │   └── ...
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── docs/                         # Documentation
├── tests/                        # Test files
├── data/                         # SQLite database
├── requirements.txt
├── docker-compose.yml
└── README.md
```

---

## Configuration Files

### requirements.txt
```
# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database (Local SQLite - FREE)

# Web Scraping (FREE)
beautifulsoup4==4.12.3

# Vector DB for RAG (FREE, Local)
chromadb==0.4.22
sentence-transformers==2.3.1

# Data Processing
pandas>=2.2.0
openpyxl==3.1.2
xlsxwriter==3.1.9

# Image Processing & OCR
Pillow==10.2.0
pytesseract==0.3.10

# Email Processing
email-validator==2.1.0
email-reply-parser==0.5.12

# Google Sheets Integration
gspread==6.0.0
google-auth==2.27.0
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0

# HTTP & Webhooks
httpx>=0.27.0
requests==2.31.0

# Utilities
python-dotenv==1.0.0
pydantic>=2.10.0
pydantic-settings==2.1.0

# Date/Time
python-dateutil==2.8.2
pytz==2024.1

# Security
cryptography==42.0.0
python-jose[cryptography]==3.3.0

# Logging & Monitoring
loguru==0.7.2

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0

# Development
black==24.1.1
flake8==7.0.0
mypy==1.8.0
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/mercura.db
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:80"
    depends_on:
      - backend
    restart: unless-stopped
```

---

## Backend (Python)

### app/main.py
Main FastAPI application entry point with all routers registered.

```python
"""
OpenMercura - Quote Management API
Built with FastAPI, SQLite, and AI-powered extraction
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.routes import auth, customers, products, quotes
from app.routes import extractions, competitors, rag, analytics
from app.routes import templates, portal, erp_export
from app.routes import quickbooks, alerts, intelligence, image_extract, impact, onboarding

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    print("=" * 50)
    print("Project OpenMercura Ready.")
    print("=" * 50)
    yield

app = FastAPI(
    title=settings.app_name,
    description="AI-powered quote management for distributors",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(products.router)
app.include_router(quotes.router)
app.include_router(extractions.router)
app.include_router(competitors.router)
app.include_router(rag.router)
app.include_router(analytics.router)
app.include_router(templates.router)
app.include_router(portal.router)
app.include_router(erp_export.router)
app.include_router(quickbooks.router)
app.include_router(alerts.router)
app.include_router(intelligence.router)
app.include_router(image_extract.router)
app.include_router(impact.router)
app.include_router(onboarding.router)

@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "features": {
            "crm": True,
            "quotes": True,
            "competitor_analysis": True,
            "rag": "available",
            "multi_user": True,
            "analytics": True,
            "industry_templates": True,
            "customer_portal": True,
            "erp_export": True,
            "quickbooks": True
        }
    }
```

### Key Service Files

**app/alert_service.py** - Smart alert generation (New RFQ, Follow-up, Expiring)
**app/quickbooks_service.py** - OAuth2 QuickBooks integration
**app/customer_intelligence_service.py** - Health scores and insights
**app/business_impact_service.py** - ROI and time savings tracking
**app/image_extraction_service.py** - OCR and AI image processing
**app/onboarding_service.py** - User onboarding and progressive disclosure

---

## Frontend (TypeScript/React)

### frontend/src/App.tsx
Main React application with routing.

```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { TodayView } from './pages/TodayView';
import { SmartQuote } from './pages/SmartQuote';
import { Quotes } from './pages/Quotes';
import { Customers } from './pages/Customers';
import { IntelligenceDashboard } from './pages/IntelligenceDashboard';
import { CustomerIntelligence } from './pages/CustomerIntelligence';
import { BusinessImpact } from './pages/BusinessImpact';
import { CameraCapture } from './pages/CameraCapture';
import { QuickBooksIntegration } from './pages/QuickBooksIntegration';
import { AlertsPage } from './pages/AlertsPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout><TodayView /></Layout>} />
        <Route path="/quotes" element={<Layout><Quotes /></Layout>} />
        <Route path="/quotes/new" element={<Layout><SmartQuote /></Layout>} />
        <Route path="/customers" element={<Layout><Customers /></Layout>} />
        <Route path="/intelligence" element={<Layout><IntelligenceDashboard /></Layout>} />
        <Route path="/intelligence/customers/:customerId" element={<Layout><CustomerIntelligence /></Layout>} />
        <Route path="/impact" element={<Layout><BusinessImpact /></Layout>} />
        <Route path="/camera" element={<Layout><CameraCapture /></Layout>} />
        <Route path="/quickbooks" element={<Layout><QuickBooksIntegration /></Layout>} />
        <Route path="/alerts" element={<Layout><AlertsPage /></Layout>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

### Key Page Components

**frontend/src/pages/TodayView.tsx** - Main dashboard with GettingStarted checklist
**frontend/src/pages/SmartQuote.tsx** - AI-powered quote creation
**frontend/src/pages/BusinessImpact.tsx** - ROI and time savings dashboard
**frontend/src/pages/IntelligenceDashboard.tsx** - Customer intelligence overview
**frontend/src/pages/CameraCapture.tsx** - Photo-to-quote OCR feature
**frontend/src/components/NotificationCenter.tsx** - Alert bell dropdown
**frontend/src/components/GettingStarted.tsx** - Onboarding checklist

---

## Documentation

### docs/SMART_QUOTE_FEATURE.md
AI-powered RFQ extraction and quote creation.

### docs/QUICKBOOKS_INTEGRATION.md
Native QuickBooks OAuth2 sync.

### docs/CUSTOMER_INTELLIGENCE.md
Simple, actionable customer analytics.

### docs/BUSINESS_IMPACT.md
ROI and time savings tracking.

### docs/SIMPLIFICATION.md
Onboarding and progressive disclosure.

---

## Key Features Summary

1. **Smart Quote** - AI extracts items from RFQ emails
2. **QuickBooks Integration** - Two-way sync with OAuth2
3. **Today View** - Daily command center with priorities
4. **Smart Alerts** - 3 essential alert types (no noise)
5. **Customer Intelligence** - Health scores and insights
6. **Camera Capture** - Photo to quote via OCR
7. **Business Impact** - ROI and time savings tracking
8. **Onboarding** - Progressive disclosure for new users

---

## API Endpoints Summary

| Endpoint | Description |
|----------|-------------|
| `POST /quotes/` | Create quote |
| `POST /extractions/parse` | Parse RFQ text with AI |
| `GET /alerts/` | Get user alerts |
| `GET /intelligence/customers` | Customer intelligence |
| `GET /impact/dashboard` | Business impact metrics |
| `POST /image-extract/upload` | Extract from image |
| `POST /quickbooks/connect` | Connect QuickBooks |
| `GET /onboarding/checklist` | Onboarding progress |

---

## Build Commands

```bash
# Backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run build:web

# Docker
docker-compose up -d
```

---

## Environment Variables

```
QUICKBOOKS_CLIENT_ID=your_client_id
QUICKBOOKS_CLIENT_SECRET=your_client_secret
QUICKBOOKS_SANDBOX=true
OPENROUTER_API_KEY=your_key
DATABASE_URL=sqlite:///./data/mercura.db
```

---

*This repomix contains the consolidated structure and key files of the OpenMercura project.*
*For full source code, see the individual files in the repository.*
