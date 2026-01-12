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
    category: Optional[str] = None
    supplier: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


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

-- Catalogs table
CREATE TABLE IF NOT EXISTS catalogs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    sku TEXT NOT NULL,
    item_name TEXT NOT NULL,
    expected_price NUMERIC(10, 2),
    category TEXT,
    supplier TEXT,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB,
    UNIQUE(user_id, sku)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_inbound_emails_sender ON inbound_emails(sender_email);
CREATE INDEX IF NOT EXISTS idx_inbound_emails_status ON inbound_emails(status);
CREATE INDEX IF NOT EXISTS idx_inbound_emails_received_at ON inbound_emails(received_at);
CREATE INDEX IF NOT EXISTS idx_line_items_email_id ON line_items(email_id);
CREATE INDEX IF NOT EXISTS idx_line_items_sku ON line_items(sku);
CREATE INDEX IF NOT EXISTS idx_catalogs_user_sku ON catalogs(user_id, sku);

-- Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE inbound_emails ENABLE ROW LEVEL SECURITY;
ALTER TABLE line_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE catalogs ENABLE ROW LEVEL SECURITY;

-- RLS Policies (basic - customize based on auth strategy)
CREATE POLICY users_select_own ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY inbound_emails_select_own ON inbound_emails FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY line_items_select_own ON line_items FOR SELECT USING (
    email_id IN (SELECT id FROM inbound_emails WHERE user_id = auth.uid())
);
CREATE POLICY catalogs_all_own ON catalogs FOR ALL USING (auth.uid() = user_id);
"""
