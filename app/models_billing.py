"""
Billing and Subscription models for B2B SaaS.
Supports per-seat pricing with Paddle as Merchant of Record.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SubscriptionStatus(str, Enum):
    """Status of a subscription."""
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    PAUSED = "paused"


class BillingInterval(str, Enum):
    """Billing interval for subscriptions."""
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionPlan(BaseModel):
    """Subscription plan definition."""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    price_per_seat: float  # Price per sales rep/seat
    billing_interval: BillingInterval = BillingInterval.MONTHLY
    paddle_plan_id: Optional[str] = None  # Paddle product/plan ID
    features: List[str] = []
    max_seats: Optional[int] = None  # None = unlimited
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class Subscription(BaseModel):
    """User subscription record."""
    id: Optional[str] = None
    user_id: str
    plan_id: str
    paddle_subscription_id: Optional[str] = None
    paddle_customer_id: Optional[str] = None
    status: SubscriptionStatus = SubscriptionStatus.TRIAL
    seats: int = 1  # Number of sales reps/seats
    price_per_seat: float
    total_amount: float  # seats * price_per_seat
    billing_interval: BillingInterval = BillingInterval.MONTHLY
    current_period_start: datetime = Field(default_factory=datetime.utcnow)
    current_period_end: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class Invoice(BaseModel):
    """Invoice record for billing."""
    id: Optional[str] = None
    subscription_id: str
    user_id: str
    paddle_invoice_id: Optional[str] = None
    invoice_number: str
    amount: float
    currency: str = "USD"
    status: str  # 'draft', 'open', 'paid', 'void', 'uncollectible'
    invoice_date: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    invoice_pdf_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class PaymentMethod(BaseModel):
    """Payment method on file."""
    id: Optional[str] = None
    user_id: str
    paddle_payment_method_id: Optional[str] = None
    type: str  # 'card', 'paypal', etc.
    last4: Optional[str] = None
    brand: Optional[str] = None  # 'visa', 'mastercard', etc.
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None
    is_default: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class BillingAddress(BaseModel):
    """Billing address for invoices."""
    id: Optional[str] = None
    user_id: str
    company_name: Optional[str] = None
    line1: str
    line2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str  # ISO 3166-1 alpha-2 code
    vat_number: Optional[str] = None  # For EU businesses
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SeatAssignment(BaseModel):
    """Assignment of a subscription seat to a sales rep."""
    id: Optional[str] = None
    subscription_id: str
    user_id: str
    sales_rep_email: str
    sales_rep_name: Optional[str] = None
    is_active: bool = True
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    deactivated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class UsageRecord(BaseModel):
    """Track usage metrics for billing."""
    id: Optional[str] = None
    subscription_id: str
    user_id: str
    metric_name: str  # 'quotes_generated', 'emails_processed', etc.
    quantity: int
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


# Request/Response Models

class CreateSubscriptionRequest(BaseModel):
    """Request to create a new subscription."""
    plan_id: str
    seats: int = 1
    billing_interval: BillingInterval = BillingInterval.MONTHLY
    payment_method_id: Optional[str] = None


class UpdateSubscriptionRequest(BaseModel):
    """Request to update subscription."""
    seats: Optional[int] = None
    plan_id: Optional[str] = None
    cancel_at_period_end: Optional[bool] = None


class CheckoutSessionRequest(BaseModel):
    """Request to create a Paddle checkout session."""
    plan_id: str
    seats: int = 1
    billing_interval: BillingInterval = BillingInterval.MONTHLY
    success_url: str
    cancel_url: str


class CheckoutSessionResponse(BaseModel):
    """Response with Paddle checkout URL."""
    checkout_url: str
    session_id: str


class BillingPortalRequest(BaseModel):
    """Request to create a billing portal session."""
    return_url: str


class BillingPortalResponse(BaseModel):
    """Response with billing portal URL."""
    portal_url: str


# Database Schema for Supabase

BILLING_SCHEMA = """
-- Subscription Plans table
CREATE TABLE IF NOT EXISTS subscription_plans (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price_per_seat NUMERIC(10, 2) NOT NULL,
    billing_interval TEXT CHECK (billing_interval IN ('monthly', 'yearly')) DEFAULT 'monthly',
    paddle_plan_id TEXT,
    features JSONB,
    max_seats INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- Subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plan_id UUID REFERENCES subscription_plans(id),
    paddle_subscription_id TEXT UNIQUE,
    paddle_customer_id TEXT,
    status TEXT CHECK (status IN ('trial', 'active', 'past_due', 'canceled', 'paused')) DEFAULT 'trial',
    seats INTEGER DEFAULT 1,
    price_per_seat NUMERIC(10, 2) NOT NULL,
    total_amount NUMERIC(10, 2) NOT NULL,
    billing_interval TEXT CHECK (billing_interval IN ('monthly', 'yearly')) DEFAULT 'monthly',
    current_period_start TIMESTAMPTZ DEFAULT NOW(),
    current_period_end TIMESTAMPTZ,
    trial_end TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- Invoices table
CREATE TABLE IF NOT EXISTS invoices (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    subscription_id UUID REFERENCES subscriptions(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    paddle_invoice_id TEXT UNIQUE,
    invoice_number TEXT NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    currency TEXT DEFAULT 'USD',
    status TEXT DEFAULT 'draft',
    invoice_date TIMESTAMPTZ DEFAULT NOW(),
    due_date TIMESTAMPTZ,
    paid_at TIMESTAMPTZ,
    invoice_pdf_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- Payment Methods table
CREATE TABLE IF NOT EXISTS payment_methods (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    paddle_payment_method_id TEXT,
    type TEXT NOT NULL,
    last4 TEXT,
    brand TEXT,
    exp_month INTEGER,
    exp_year INTEGER,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- Billing Addresses table
CREATE TABLE IF NOT EXISTS billing_addresses (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    company_name TEXT,
    line1 TEXT NOT NULL,
    line2 TEXT,
    city TEXT NOT NULL,
    state TEXT,
    postal_code TEXT NOT NULL,
    country TEXT NOT NULL,
    vat_number TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seat Assignments table
CREATE TABLE IF NOT EXISTS seat_assignments (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    subscription_id UUID REFERENCES subscriptions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    sales_rep_email TEXT NOT NULL,
    sales_rep_name TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    deactivated_at TIMESTAMPTZ,
    metadata JSONB
);

-- Usage Records table
CREATE TABLE IF NOT EXISTS usage_records (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    subscription_id UUID REFERENCES subscriptions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    metric_name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_paddle ON subscriptions(paddle_subscription_id);
CREATE INDEX IF NOT EXISTS idx_invoices_user ON invoices(user_id);
CREATE INDEX IF NOT EXISTS idx_invoices_subscription ON invoices(subscription_id);
CREATE INDEX IF NOT EXISTS idx_seat_assignments_subscription ON seat_assignments(subscription_id);
CREATE INDEX IF NOT EXISTS idx_usage_records_subscription ON usage_records(subscription_id);

-- RLS Policies
ALTER TABLE subscription_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_methods ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_addresses ENABLE ROW LEVEL SECURITY;
ALTER TABLE seat_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY subscription_plans_select_all ON subscription_plans FOR SELECT USING (TRUE);
CREATE POLICY subscriptions_all_own ON subscriptions FOR ALL USING (auth.uid() = user_id);
CREATE POLICY invoices_all_own ON invoices FOR ALL USING (auth.uid() = user_id);
CREATE POLICY payment_methods_all_own ON payment_methods FOR ALL USING (auth.uid() = user_id);
CREATE POLICY billing_addresses_all_own ON billing_addresses FOR ALL USING (auth.uid() = user_id);
CREATE POLICY seat_assignments_all_own ON seat_assignments FOR ALL USING (auth.uid() = user_id);
CREATE POLICY usage_records_all_own ON usage_records FOR ALL USING (auth.uid() = user_id);
"""
