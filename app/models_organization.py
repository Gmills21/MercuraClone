"""
Organization/Company models for multi-tenancy.
This is the foundation of data isolation in a B2B SaaS.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class OrganizationStatus(str, Enum):
    """Status of an organization."""
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELED = "canceled"


class Organization(BaseModel):
    """
    Organization/Company model.
    This is the top-level multi-tenant entity.
    All data (customers, products, quotes) belongs to an organization.
    """
    id: Optional[str] = None
    name: str
    slug: str  # Unique subdomain or identifier
    domain: Optional[str] = None  # Custom domain (e.g., "acme.com")
    
    # Owner information
    owner_user_id: str  # User who created the organization
    
    # Subscription & billing
    subscription_id: Optional[str] = None
    status: OrganizationStatus = OrganizationStatus.TRIAL
    seats_total: int = 1
    seats_used: int = 0
    
    # Settings
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)
    branding: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    trial_ends_at: Optional[datetime] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None


class OrganizationMember(BaseModel):
    """
    Link between User and Organization with role.
    Users can belong to multiple organizations (e.g., consultants).
    """
    id: Optional[str] = None
    organization_id: str
    user_id: str
    role: str  # 'owner', 'admin', 'manager', 'sales_rep', 'viewer'
    
    # Status
    is_active: bool = True
    invited_by: Optional[str] = None  # User ID who invited
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_active_at: Optional[datetime] = None
    
    # Permissions (optional fine-grained control)
    permissions: Optional[List[str]] = None
    
    metadata: Optional[Dict[str, Any]] = None


class OrganizationInvitation(BaseModel):
    """
    Pending invitation to join an organization.
    """
    id: Optional[str] = None
    organization_id: str
    email: EmailStr
    role: str = "sales_rep"
    
    # Invitation management
    token: str  # Secure token for accepting invitation
    invited_by: str  # User ID who sent invitation
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime  # Invitations expire after 7 days
    
    # Status
    status: str = "pending"  # 'pending', 'accepted', 'expired', 'canceled'
    accepted_at: Optional[datetime] = None
    accepted_by: Optional[str] = None  # User ID created from invitation
    
    metadata: Optional[Dict[str, Any]] = None


class OrganizationSettings(BaseModel):
    """Settings for an organization."""
    # Company info
    company_name: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None  # '1-10', '11-50', '51-200', '201-500', '501+'
    
    # Contact
    billing_email: Optional[EmailStr] = None
    support_email: Optional[EmailStr] = None
    phone: Optional[str] = None
    
    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    vat_number: Optional[str] = None  # For EU businesses
    
    # Features
    features_enabled: List[str] = Field(default_factory=list)
    integrations_enabled: List[str] = Field(default_factory=list)
    
    # Branding
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    
    # Security
    require_2fa: bool = False
    allowed_email_domains: Optional[List[str]] = None  # Restrict signups
    sso_enabled: bool = False
    sso_provider: Optional[str] = None


# Request/Response Models

class CreateOrganizationRequest(BaseModel):
    """Request to create a new organization."""
    name: str
    slug: str  # Must be unique
    owner_email: EmailStr
    owner_name: str
    owner_password: str


class UpdateOrganizationRequest(BaseModel):
    """Request to update organization details."""
    name: Optional[str] = None
    domain: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    branding: Optional[Dict[str, Any]] = None


class InviteMemberRequest(BaseModel):
    """Request to invite a new member."""
    email: EmailStr
    role: str = "sales_rep"
    send_email: bool = True  # Whether to send invitation email


class AcceptInvitationRequest(BaseModel):
    """Request to accept an invitation."""
    token: str
    user_name: str
    password: str


# Database Schema

ORGANIZATION_SCHEMA = """
-- Organizations table (multi-tenant root)
CREATE TABLE IF NOT EXISTS organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    domain TEXT,
    owner_user_id TEXT NOT NULL,
    subscription_id TEXT,
    status TEXT CHECK (status IN ('trial', 'active', 'suspended', 'canceled')) DEFAULT 'trial',
    seats_total INTEGER DEFAULT 1,
    seats_used INTEGER DEFAULT 0,
    settings TEXT,  -- JSON
    branding TEXT,  -- JSON
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    trial_ends_at TEXT,
    metadata TEXT  -- JSON
);

-- Organization Members (users belong to orgs)
CREATE TABLE IF NOT EXISTS organization_members (
    id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    invited_by TEXT,
    joined_at TEXT NOT NULL,
    last_active_at TEXT,
    permissions TEXT,  -- JSON array
    metadata TEXT,  -- JSON
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(organization_id, user_id)
);

-- Organization Invitations
CREATE TABLE IF NOT EXISTS organization_invitations (
    id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'sales_rep',
    token TEXT UNIQUE NOT NULL,
    invited_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    status TEXT CHECK (status IN ('pending', 'accepted', 'expired', 'canceled')) DEFAULT 'pending',
    accepted_at TEXT,
    accepted_by TEXT,
    metadata TEXT,  -- JSON
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (invited_by) REFERENCES users(id)
);

-- Sessions table (persistent token storage)
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token TEXT UNIQUE NOT NULL,
    organization_id TEXT,  -- Current organization context
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    last_used_at TEXT NOT NULL,
    user_agent TEXT,
    ip_address TEXT,
    is_active INTEGER DEFAULT 1,
    metadata TEXT,  -- JSON
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE SET NULL
);

-- Password Reset Tokens
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used_at TEXT,
    is_used INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_organizations_slug ON organizations(slug);
CREATE INDEX IF NOT EXISTS idx_organizations_owner ON organizations(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_org_members_org ON organization_members(organization_id);
CREATE INDEX IF NOT EXISTS idx_org_members_user ON organization_members(user_id);
CREATE INDEX IF NOT EXISTS idx_org_invites_email ON organization_invitations(email);
CREATE INDEX IF NOT EXISTS idx_org_invites_token ON organization_invitations(token);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_reset_tokens_token ON password_reset_tokens(token);
"""
