"""
Database models and schemas for Mercura.
Defines the structure for Supabase tables.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EmailStatus(str, Enum):
    """Status of email processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class InboundEmail(BaseModel):
    """Model for inbound email tracking."""
    id: Optional[str] = None
    sender_email: EmailStr
    subject_line: Optional[str] = None
    received_at: datetime = Field(default_factory=datetime.utcnow)
    status: EmailStatus = EmailStatus.PENDING
    error_message: Optional[str] = None
    has_attachments: bool = False
    attachment_count: int = 0
    raw_email_size: Optional[int] = None
    user_id: Optional[str] = None
    
    class Config:
        use_enum_values = True


class LineItem(BaseModel):
    """Model for extracted line items."""
    id: Optional[str] = None
    email_id: str
    item_name: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    confidence_score: Optional[float] = None
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class ExtractionRequest(BaseModel):
    """Request model for Gemini extraction."""
    email_body: Optional[str] = None
    attachment_data: Optional[str] = None  # Base64 encoded
    attachment_type: Optional[str] = None  # pdf, png, jpg
    extraction_schema: Dict[str, Any]
    context: Optional[str] = None


class ExtractionResponse(BaseModel):
    """Response model from Gemini extraction."""
    success: bool
    line_items: List[Dict[str, Any]]
    confidence_score: float
    raw_response: Optional[str] = None
    error: Optional[str] = None
    processing_time_ms: Optional[int] = None


class ExportRequest(BaseModel):
    """Request model for data export."""
    email_ids: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    format: str = "csv"  # csv, excel, google_sheets
    include_metadata: bool = False
    google_sheet_id: Optional[str] = None  # For Google Sheets export


class WebhookPayload(BaseModel):
    """Generic webhook payload model."""
    sender: EmailStr
    recipient: str
    subject: Optional[str] = None
    body_plain: Optional[str] = None
    body_html: Optional[str] = None
    attachments: List[Dict[str, Any]] = []
    timestamp: Optional[datetime] = None
    message_id: Optional[str] = None
    
    # Provider-specific fields
    provider: str  # sendgrid or mailgun
    raw_payload: Optional[Dict[str, Any]] = None


class User(BaseModel):
    """User model for authentication."""
    id: Optional[str] = None
    email: EmailStr
    company_name: Optional[str] = None
    api_key: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    email_quota_per_day: int = 1000
    emails_processed_today: int = 0


class Catalog(BaseModel):
    """Master catalog for validating extracted data."""
    id: Optional[str] = None
    user_id: str
    sku: str
    item_name: str
    expected_price: Optional[float] = None
    cost_price: Optional[float] = None
    category: Optional[str] = None
    supplier: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class CompetitorMap(BaseModel):
    """Mapping from competitor SKU to our SKU."""
    id: Optional[str] = None
    user_id: str
    competitor_sku: str
    our_sku: str
    competitor_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class CatalogMatch(BaseModel):
    """A suggested match from the catalog."""
    catalog_item: Catalog
    score: float  # 0.0 to 1.0
    match_type: str  # 'sku_exact', 'sku_partial', 'name_overlap', 'fuzzy'


class SuggestionRequest(BaseModel):
    """Request for product suggestions."""
    items: List[Dict[str, str]]  # List of {sku, description, ...}


class SuggestionResponse(BaseModel):
    """Response with suggestions."""
    suggestions: Dict[int, List[CatalogMatch]]  # Key is index of item in request


class QuoteStatus(str, Enum):
    """Status of a quote."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Customer(BaseModel):
    """Customer model."""
    id: Optional[str] = None
    user_id: str
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class QuoteItem(BaseModel):
    """Item within a quote."""
    id: Optional[str] = None
    quote_id: str
    product_id: Optional[str] = None
    sku: Optional[str] = None
    description: str
    quantity: int = 1
    unit_price: float
    total_price: float
    validation_warnings: List[str] = []
    margin: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class Quote(BaseModel):
    """Quote/Estimate model."""
    id: Optional[str] = None
    user_id: str
    customer_id: Optional[str] = None
    inbound_email_id: Optional[str] = None
    quote_number: str
    status: QuoteStatus = QuoteStatus.DRAFT
    total_amount: float = 0.0
    valid_until: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    items: List[QuoteItem] = []
    metadata: Optional[Dict[str, Any]] = None


class QuoteTemplate(BaseModel):
    """Template for quotes."""
    id: Optional[str] = None
    user_id: str
    name: str
    description: Optional[str] = None
    default_items: List[Dict[str, Any]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


# SQL Schema for Supabase initialization
SUPABASE_SCHEMA = """
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    company_name TEXT,
    api_key TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    email_quota_per_day INTEGER DEFAULT 1000,
    emails_processed_today INTEGER DEFAULT 0
);

-- Inbound emails table
CREATE TABLE IF NOT EXISTS inbound_emails (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    sender_email TEXT NOT NULL,
    subject_line TEXT,
    received_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT CHECK (status IN ('pending', 'processing', 'processed', 'failed')) DEFAULT 'pending',
    error_message TEXT,
    has_attachments BOOLEAN DEFAULT FALSE,
    attachment_count INTEGER DEFAULT 0,
    raw_email_size INTEGER,
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Line items table
CREATE TABLE IF NOT EXISTS line_items (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    email_id UUID REFERENCES inbound_emails(id) ON DELETE CASCADE,
    item_name TEXT,
    sku TEXT,
    description TEXT,
    quantity INTEGER,
    unit_price NUMERIC(10, 2),
    total_price NUMERIC(10, 2),
    confidence_score FLOAT,
    extracted_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- Catalogs table (Products)
CREATE TABLE IF NOT EXISTS catalogs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    sku TEXT NOT NULL,
    item_name TEXT NOT NULL,
    expected_price NUMERIC(10, 2),
    cost_price NUMERIC(10, 2),
    category TEXT,
    supplier TEXT,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB,
    embedding vector(768), -- Gemini embeddings are 768 dimensions
    UNIQUE(user_id, sku)
);

-- Index for vector search
CREATE INDEX IF NOT EXISTS idx_catalogs_embedding ON catalogs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    company TEXT,
    address TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- Quotes table
CREATE TABLE IF NOT EXISTS quotes (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    inbound_email_id UUID REFERENCES inbound_emails(id) ON DELETE SET NULL,
    quote_number TEXT NOT NULL,
    status TEXT DEFAULT 'draft',
    total_amount NUMERIC(10, 2) DEFAULT 0.00,
    valid_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- Quote Items table
CREATE TABLE IF NOT EXISTS quote_items (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    quote_id UUID REFERENCES quotes(id) ON DELETE CASCADE,
    product_id UUID REFERENCES catalogs(id) ON DELETE SET NULL,
    sku TEXT,
    description TEXT,
    quantity INTEGER DEFAULT 1,
    unit_price NUMERIC(10, 2),
    total_price NUMERIC(10, 2),
    validation_warnings JSONB,
    margin NUMERIC(10, 4),
    metadata JSONB
);

-- Competitor Maps table
CREATE TABLE IF NOT EXISTS competitor_maps (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    competitor_sku TEXT NOT NULL,
    our_sku TEXT NOT NULL,
    competitor_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB,
    UNIQUE(user_id, competitor_sku)
);

-- Quote Templates table
CREATE TABLE IF NOT EXISTS quote_templates (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    default_items JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_inbound_emails_sender ON inbound_emails(sender_email);
CREATE INDEX IF NOT EXISTS idx_inbound_emails_message_id ON inbound_emails(message_id);
CREATE INDEX IF NOT EXISTS idx_inbound_emails_status ON inbound_emails(status);
CREATE INDEX IF NOT EXISTS idx_inbound_emails_received_at ON inbound_emails(received_at);
CREATE INDEX IF NOT EXISTS idx_line_items_email_id ON line_items(email_id);
CREATE INDEX IF NOT EXISTS idx_line_items_sku ON line_items(sku);
CREATE INDEX IF NOT EXISTS idx_catalogs_user_sku ON catalogs(user_id, sku);
CREATE INDEX IF NOT EXISTS idx_quotes_user ON quotes(user_id);
CREATE INDEX IF NOT EXISTS idx_quotes_customer ON quotes(customer_id);

-- Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE inbound_emails ENABLE ROW LEVEL SECURITY;
ALTER TABLE line_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE catalogs ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE quotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE quote_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE quote_templates ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY users_select_own ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY inbound_emails_select_own ON inbound_emails FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY line_items_select_own ON line_items FOR SELECT USING (
    email_id IN (SELECT id FROM inbound_emails WHERE user_id = auth.uid())
);
CREATE POLICY catalogs_all_own ON catalogs FOR ALL USING (auth.uid() = user_id);
CREATE POLICY competitor_maps_all_own ON competitor_maps FOR ALL USING (auth.uid() = user_id);
CREATE POLICY customers_all_own ON customers FOR ALL USING (auth.uid() = user_id);
CREATE POLICY quotes_all_own ON quotes FOR ALL USING (auth.uid() = user_id);
CREATE POLICY quote_items_all_own ON quote_items FOR ALL USING (
    quote_id IN (SELECT id FROM quotes WHERE user_id = auth.uid())
);
CREATE POLICY quote_templates_all_own ON quote_templates FOR ALL USING (auth.uid() = user_id);

-- RPC Function for Vector Search
CREATE OR REPLACE FUNCTION match_catalogs (
  query_embedding vector(768),
  match_threshold float,
  match_count int,
  filter_user_id uuid
)
RETURNS TABLE (
  id uuid,
  user_id uuid,
  sku text,
  item_name text,
  expected_price numeric,
  cost_price numeric,
  category text,
  supplier text,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    c.id,
    c.user_id,
    c.sku,
    c.item_name,
    c.expected_price,
    c.cost_price,
    c.category,
    c.supplier,
    c.metadata,
    1 - (c.embedding <=> query_embedding) as similarity
  FROM catalogs c
  WHERE c.user_id = filter_user_id
  AND 1 - (c.embedding <=> query_embedding) > match_threshold
  ORDER BY c.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
"""
