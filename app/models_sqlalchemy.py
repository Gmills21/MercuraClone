"""
SQLAlchemy Models
Mirror of the existing SQLite schema for PostgreSQL/SQLite compatibility.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database_sqlalchemy import Base


def generate_uuid():
    """Generate a UUID string."""
    return str(uuid.uuid4())


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="sales_rep")  # admin, manager, sales_rep, viewer
    company_id = Column(String, ForeignKey("organizations.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="members")
    quotes = relationship("Quote", back_populates="user")


class Organization(Base):
    """Organization/Company model."""
    __tablename__ = "organizations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    domain = Column(String, nullable=True)
    owner_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(String, nullable=True)
    status = Column(String, default="trial")  # trial, active, suspended, canceled
    seats_total = Column(Integer, default=1)
    seats_used = Column(Integer, default=0)
    settings = Column(JSON, default=dict)
    branding = Column(JSON, nullable=True)
    trial_ends_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    members = relationship("User", back_populates="organization")
    customers = relationship("Customer", back_populates="organization")
    products = relationship("Product", back_populates="organization")
    quotes = relationship("Quote", back_populates="organization")
    invitations = relationship("OrganizationInvitation", back_populates="organization")


class OrganizationMember(Base):
    """Organization membership model."""
    __tablename__ = "organization_members"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    invited_by = Column(String, nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, nullable=True)
    permissions = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)


class OrganizationInvitation(Base):
    """Organization invitation model."""
    __tablename__ = "organization_invitations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    email = Column(String, nullable=False, index=True)
    role = Column(String, default="sales_rep")
    token = Column(String, unique=True, nullable=False)
    invited_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    status = Column(String, default="pending")  # pending, accepted, expired, canceled
    accepted_at = Column(DateTime, nullable=True)
    accepted_by = Column(String, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="invitations")


class Customer(Base):
    """Customer model."""
    __tablename__ = "customers"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True, index=True)
    company = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="customers")
    quotes = relationship("Quote", back_populates="customer")


class Product(Base):
    """Product model."""
    __tablename__ = "products"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    sku = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    cost = Column(Float, nullable=True)
    category = Column(String, nullable=True)
    competitor_sku = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="products")
    
    # Unique constraint on organization + sku
    __table_args__ = (
        # Can't use uniqueconstraint easily with string-based FK in SQLite
        # Handled at application level
    )


class Project(Base):
    """Project model."""
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    address = Column(Text, nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    quotes = relationship("Quote", back_populates="project")


class Quote(Base):
    """Quote model."""
    __tablename__ = "quotes"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    assigned_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="draft")
    subtotal = Column(Float, default=0)
    tax_rate = Column(Float, default=0)
    tax_amount = Column(Float, default=0)
    total = Column(Float, default=0)
    notes = Column(Text, nullable=True)
    token = Column(String, unique=True, nullable=False, default=generate_uuid)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="quotes")
    customer = relationship("Customer", back_populates="quotes")
    project = relationship("Project", back_populates="quotes")
    user = relationship("User", back_populates="quotes", foreign_keys=[user_id])
    items = relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan")


class QuoteItem(Base):
    """Quote line item model."""
    __tablename__ = "quote_items"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    quote_id = Column(String, ForeignKey("quotes.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=True)
    product_name = Column(String, nullable=True)
    sku = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    competitor_sku = Column(String, nullable=True)
    
    # Relationships
    quote = relationship("Quote", back_populates="items")


class InboundEmail(Base):
    """Inbound email model."""
    __tablename__ = "inbound_emails"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    sender_email = Column(String, nullable=False)
    recipient_email = Column(String, nullable=False)
    subject_line = Column(String, nullable=True)
    body_plain = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")  # pending, processing, processed, failed
    error_message = Column(Text, nullable=True)
    has_attachments = Column(Boolean, default=False)
    attachment_count = Column(Integer, default=0)
    message_id = Column(String, unique=True, nullable=True)
    metadata = Column(JSON, nullable=True)


class PasswordResetToken(Base):
    """Password reset token model."""
    __tablename__ = "password_reset_tokens"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    is_used = Column(Boolean, default=False)


class Competitor(Base):
    """Competitor model."""
    __tablename__ = "competitors"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    url = Column(String, nullable=False)
    name = Column(String, nullable=False)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    keywords = Column(String, nullable=True)
    pricing = Column(Text, nullable=True)
    features = Column(Text, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    error = Column(String, nullable=True)


class Extraction(Base):
    """Data extraction model."""
    __tablename__ = "extractions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    source_type = Column(String, nullable=False)
    source_content = Column(Text, nullable=True)
    parsed_data = Column(JSON, nullable=False)
    confidence_score = Column(Float, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)


class Session(Base):
    """User session model."""
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, nullable=False)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime, default=datetime.utcnow)
    user_agent = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON, nullable=True)


class IntegrationSecret(Base):
    """Integration secrets model (encrypted)."""
    __tablename__ = "integration_secrets"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    integration_type = Column(String, nullable=False)  # quickbooks, hubspot, etc.
    encrypted_data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
