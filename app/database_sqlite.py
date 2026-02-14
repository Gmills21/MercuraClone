"""
Local SQLite database for OpenMercura.
Replaces paid Supabase with free local SQLite.
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from loguru import logger

from app.config import settings

# Database path - derived from settings.database_url
# Handle sqlite:/// prefix
db_url = settings.database_url
if db_url.startswith("sqlite:///"):
    DB_PATH = db_url.replace("sqlite:///", "")
    # Handle both relative and absolute paths
    if not os.path.isabs(DB_PATH) and not DB_PATH.startswith("./"):
        # If it's just "mercura.db", make it relative to root
        DB_PATH = os.path.abspath(os.path.join(os.getcwd(), DB_PATH))
    elif DB_PATH.startswith("./"):
        DB_PATH = os.path.abspath(os.path.join(os.getcwd(), DB_PATH[2:]))
else:
    # Fallback to default if URL is not sqlite
    DB_PATH = os.path.abspath(os.path.join(os.getcwd(), "mercura.db"))

DB_DIR = os.path.dirname(DB_PATH)

# Ensure data directory exists
if DB_DIR:
    os.makedirs(DB_DIR, exist_ok=True)


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Enable foreign key enforcement on every connection
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Enable WAL mode for better concurrency (if not already enabled)
    conn.execute("PRAGMA journal_mode = WAL")
    
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize database with all required tables."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Users table (for multi-user support)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'sales_rep',
                company_id TEXT NOT NULL DEFAULT 'default',
                created_at TEXT NOT NULL,
                last_login TEXT,
                is_active INTEGER NOT NULL DEFAULT 1
            )
        """)
        
        # Create default admin user if no users exist AND ADMIN_PASSWORD is set
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            import os
            admin_password = os.getenv("ADMIN_PASSWORD")
            if admin_password:
                # Use the auth module's password hashing if available
                try:
                    from app.auth import _hash_password
                    password_hash = _hash_password(admin_password)
                except ImportError:
                    # Fallback hashing
                    import hashlib
                    import secrets
                    salt = secrets.token_hex(32)
                    pwdhash = hashlib.pbkdf2_hmac('sha256', admin_password.encode('utf-8'), salt.encode('utf-8'), 600000)
                    password_hash = f"pbkdf2:${salt}${pwdhash.hex()}"
                
                now = datetime.utcnow().isoformat()
                admin_email = os.getenv("ADMIN_EMAIL", "admin@openmercura.local")
                cursor.execute("""
                    INSERT INTO users (id, email, name, password_hash, role, company_id, created_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, ('admin-001', admin_email, 'System Admin', password_hash, 'admin', 'default', now, 1))
                logger.info(f"Created default admin user: {admin_email}")
            else:
                logger.warning("No users exist and ADMIN_PASSWORD not set. Create first user via /auth/register")
        
        # Migration: add deleted_at for soft-delete (account deletion)
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        if "deleted_at" not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN deleted_at TEXT")
            logger.info("Added users.deleted_at for account soft-delete")
        
        # Customers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                company TEXT,
                phone TEXT,
                address TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
        """)
        
        # Products table
        # Products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                sku TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                cost REAL,
                category TEXT,
                competitor_sku TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
                UNIQUE(organization_id, sku)
            )
        """)
        
        # Quotes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotes (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                customer_id TEXT NOT NULL,
                project_id TEXT,
                assigned_user_id TEXT,
                status TEXT NOT NULL DEFAULT 'draft',
                subtotal REAL NOT NULL DEFAULT 0,
                tax_rate REAL NOT NULL DEFAULT 0,
                tax_amount REAL NOT NULL DEFAULT 0,
                total REAL NOT NULL DEFAULT 0,
                notes TEXT,
                token TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                expires_at TEXT,
                metadata TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers (id),
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE SET NULL,
                FOREIGN KEY (assigned_user_id) REFERENCES users (id) ON DELETE SET NULL,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
        """)
        
        # Migration: Ensure quotes table has metadata column
        cursor.execute("PRAGMA table_info(quotes)")
        columns = [info[1] for info in cursor.fetchall()]
        if "metadata" not in columns:
            try:
                cursor.execute("ALTER TABLE quotes ADD COLUMN metadata TEXT")
                logger.info("Migrated quotes table: added metadata column")
            except Exception as e:
                logger.error(f"Failed to migrate quotes table: {e}")
        
        # Quote items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quote_items (
                id TEXT PRIMARY KEY,
                quote_id TEXT NOT NULL,
                product_id TEXT,
                product_name TEXT,
                sku TEXT,
                description TEXT,
                quantity REAL NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                competitor_sku TEXT,
                FOREIGN KEY (quote_id) REFERENCES quotes (id) ON DELETE CASCADE
            )
        """)
        
        # Competitors table
        # Competitors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competitors (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                url TEXT NOT NULL,
                name TEXT NOT NULL,
                title TEXT,
                description TEXT,
                keywords TEXT,
                pricing TEXT,
                features TEXT,
                last_updated TEXT NOT NULL,
                error TEXT,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
                UNIQUE(organization_id, url)
            )
        """)
        
        # Documents table (for RAG)
        # Documents table (for RAG)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL,
                type TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
        """)
        
        # Extractions table (CRM data capture)
        # Extractions table (CRM data capture)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extractions (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                source_type TEXT NOT NULL,
                source_content TEXT,
                parsed_data TEXT NOT NULL,
                confidence_score REAL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                processed_at TEXT,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
        """)
        
        # Organizations table (multi-tenant root)
        cursor.execute("""
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
                settings TEXT,
                branding TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                trial_ends_at TEXT,
                metadata TEXT
            )
        """)
        
        # Organization Members (users belong to orgs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS organization_members (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                invited_by TEXT,
                joined_at TEXT NOT NULL,
                last_active_at TEXT,
                permissions TEXT,
                metadata TEXT,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(organization_id, user_id)
            )
        """)
        
        # Organization Invitations
        cursor.execute("""
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
                metadata TEXT,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
                FOREIGN KEY (invited_by) REFERENCES users(id)
            )
        """)
        
        # Sessions table (persistent token storage)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                organization_id TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                last_used_at TEXT NOT NULL,
                user_agent TEXT,
                ip_address TEXT,
                is_active INTEGER DEFAULT 1,
                metadata TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE SET NULL
            )
        """)
        
        # Password Reset Tokens
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used_at TEXT,
                is_used INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                name TEXT NOT NULL,
                address TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
        """)
        
        # Integration Secrets (Encrypted)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS integration_secrets (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                integration_type TEXT NOT NULL, -- 'quickbooks', 'hubspot', etc.
                encrypted_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(organization_id, integration_type),
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
        """)

        # Inbound Emails table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inbound_emails (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                sender_email TEXT NOT NULL,
                recipient_email TEXT NOT NULL,
                subject_line TEXT,
                body_plain TEXT,
                body_html TEXT,
                received_at TEXT NOT NULL,
                status TEXT CHECK (status IN ('pending', 'processing', 'processed', 'failed')) DEFAULT 'pending',
                error_message TEXT,
                has_attachments INTEGER DEFAULT 0,
                attachment_count INTEGER DEFAULT 0,
                message_id TEXT UNIQUE,
                metadata TEXT,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_org ON customers (organization_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_email ON customers (email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_org ON products (organization_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_sku ON products (sku)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotes_org ON quotes (organization_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotes_customer ON quotes (customer_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotes_project ON quotes (project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotes_assigned_user ON quotes (assigned_user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quote_items_quote ON quote_items (quote_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quote_items_product ON quote_items (product_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_competitors_org ON competitors (organization_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_competitors_url ON competitors (url)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_org ON documents (organization_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_type ON documents (type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_extractions_org ON extractions (organization_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_org ON projects (organization_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inbound_emails_org ON inbound_emails(organization_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inbound_emails_status ON inbound_emails(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inbound_emails_msgid ON inbound_emails(message_id)")
        
        # Email Settings table (per organization)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_settings (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL UNIQUE,
                smtp_host TEXT DEFAULT 'smtp.gmail.com',
                smtp_port INTEGER DEFAULT 587,
                smtp_username TEXT,
                smtp_password TEXT,
                from_email TEXT,
                from_name TEXT DEFAULT 'Mercura',
                use_tls INTEGER DEFAULT 1,
                is_enabled INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_settings_org ON email_settings(organization_id)")
        
        # Alerts table (per organization)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                user_id TEXT,
                alert_type TEXT NOT NULL,
                priority TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                action_link TEXT,
                action_text TEXT,
                related_entity_type TEXT,
                related_entity_id TEXT,
                is_read INTEGER DEFAULT 0,
                is_dismissed INTEGER DEFAULT 0,
                read_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_org ON alerts(organization_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_unread ON alerts(organization_id, is_read, is_dismissed)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(alert_type, related_entity_id)")
        
        # Subscriptions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL UNIQUE,
                paddle_subscription_id TEXT,
                paddle_customer_id TEXT,
                plan_id TEXT NOT NULL,
                plan_name TEXT,
                status TEXT NOT NULL DEFAULT 'trial',
                seats_total INTEGER NOT NULL DEFAULT 1,
                seats_used INTEGER NOT NULL DEFAULT 0,
                price_per_seat REAL NOT NULL,
                total_amount REAL NOT NULL DEFAULT 0,
                billing_interval TEXT NOT NULL DEFAULT 'monthly',
                current_period_start TEXT,
                current_period_end TEXT,
                trial_ends_at TEXT,
                cancel_at_period_end INTEGER DEFAULT 0,
                canceled_at TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_org ON subscriptions(organization_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_paddle ON subscriptions(paddle_subscription_id)")
        
        # Invoices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                subscription_id TEXT,
                paddle_payment_id TEXT,
                invoice_number TEXT,
                amount REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'USD',
                status TEXT NOT NULL,
                paid_at TEXT,
                period_start TEXT,
                period_end TEXT,
                receipt_url TEXT,
                pdf_url TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_org ON invoices(organization_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_subscription ON invoices(subscription_id)")
        
        # Seat assignments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seat_assignments (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                subscription_id TEXT NOT NULL,
                user_id TEXT,
                email TEXT NOT NULL,
                name TEXT,
                is_active INTEGER DEFAULT 1,
                assigned_at TEXT NOT NULL,
                last_login_at TEXT,
                metadata TEXT,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_seats_org ON seat_assignments(organization_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_seats_subscription ON seat_assignments(subscription_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_seats_user ON seat_assignments(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_seats_email ON seat_assignments(email)")
        
        # Cancellation feedback (exit survey when user cancels subscription)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cancellation_feedback (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                subscription_id TEXT NOT NULL,
                reason TEXT,
                feedback_text TEXT,
                canceled_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cancellation_feedback_org ON cancellation_feedback(organization_id)")
        
        # Custom Domains table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_domains (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL UNIQUE,
                domain TEXT UNIQUE NOT NULL,
                status TEXT CHECK (status IN ('pending', 'verified', 'active', 'failed', 'deleted')) DEFAULT 'pending',
                verification_token TEXT NOT NULL,
                dns_records TEXT NOT NULL,
                ssl_status TEXT CHECK (ssl_status IN ('pending', 'active', 'failed')) DEFAULT 'pending',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                verified_at TEXT,
                metadata TEXT,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_custom_domains_domain ON custom_domains(domain)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_custom_domains_status ON custom_domains(status)")
        
        # Organization indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_organizations_slug ON organizations(slug)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_organizations_owner ON organizations(owner_user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_org_members_org ON organization_members(organization_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_org_members_user ON organization_members(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_org_invites_org ON organization_invitations(organization_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_org_invites_invited_by ON organization_invitations(invited_by)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_org_invites_email ON organization_invitations(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_org_invites_token ON organization_invitations(token)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_org ON sessions(organization_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reset_tokens_user ON password_reset_tokens(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reset_tokens_token ON password_reset_tokens(token)")
        
        conn.commit()
        _ensure_default_organization(conn)
        conn.commit()
        logger.info("Database initialized successfully")


def _ensure_default_organization(conn) -> None:
    """Ensure default organization exists (for X-User-ID fallback and init)."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM organizations WHERE id = ?", ("default",))
    if cursor.fetchone():
        return
    now = datetime.utcnow().isoformat()
    # Use first admin user as owner, or placeholder
    cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
    row = cursor.fetchone()
    owner_id = row["id"] if row else "admin-001"
    cursor.execute("""
        INSERT INTO organizations (id, name, slug, owner_user_id, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'active', ?, ?)
    """, ("default", "Default Organization", "default", owner_id, now, now))
    cursor.execute("SELECT id FROM organization_members WHERE organization_id = ? AND user_id = ?", ("default", owner_id))
    if not cursor.fetchone():
        import uuid
        cursor.execute("""
            INSERT INTO organization_members (id, organization_id, user_id, role, joined_at)
            VALUES (?, 'default', ?, 'admin', ?)
        """, (str(uuid.uuid4()), owner_id, now))


def get_or_create_default_organization() -> str:
    """Return default organization id, creating it if needed (for X-User-ID / dev fallback)."""
    with get_db() as conn:
        _ensure_default_organization(conn)
        conn.commit()
    return "default"


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


# Customer operations
def create_customer(customer: Dict[str, Any]) -> bool:
    """Create a new customer."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO customers (id, organization_id, name, email, company, phone, address, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer["id"],
                customer["organization_id"],
                customer["name"],
                customer.get("email"),
                customer.get("company"),
                customer.get("phone"),
                customer.get("address"),
                customer["created_at"],
                customer["updated_at"]
            ))
            conn.commit()
            return True
    except sqlite3.IntegrityError as e:
        logger.error(f"Customer creation failed: {e}")
        return False


def get_customer_by_id(customer_id: str, organization_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get customer by ID.
    If organization_id is provided, ensures the customer belongs to that organization.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        if organization_id:
            cursor.execute("SELECT * FROM customers WHERE id = ? AND organization_id = ?", (customer_id, organization_id))
        else:
            # TODO: Deprecate calling without organization_id
            cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
            
        row = cursor.fetchone()
        return dict(row) if row else None


def get_customer_by_email(email: str, organization_id: str) -> Optional[Dict[str, Any]]:
    """Get customer by email within an organization."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE email = ? AND organization_id = ?", (email, organization_id))
        row = cursor.fetchone()
        return dict(row) if row else None


def list_customers(organization_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """List all customers for an organization."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM customers WHERE organization_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (organization_id, limit, offset)
        )
        return [dict(row) for row in cursor.fetchall()]


def update_customer(customer_id: str, updates: Dict[str, Any], organization_id: Optional[str] = None) -> bool:
    """
    Update customer fields.
    If organization_id is provided, ensures ownership.
    """
    allowed_fields = ["name", "email", "company", "phone", "address"]
    set_clause = ", ".join([f"{k} = ?" for k in updates.keys() if k in allowed_fields])
    if not set_clause:
        return False
    
    values = [updates[k] for k in updates.keys() if k in allowed_fields]
    values.append(datetime.utcnow().isoformat())
    values.append(customer_id)
    
    query = f"UPDATE customers SET {set_clause}, updated_at = ? WHERE id = ?"
    if organization_id:
        query += " AND organization_id = ?"
        values.append(organization_id)
        
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        return cursor.rowcount > 0


# Product operations
def create_product(product: Dict[str, Any]) -> bool:
    """Create a new product."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products (id, organization_id, sku, name, description, price, cost, category, competitor_sku, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product["id"],
                product["organization_id"],
                product["sku"],
                product["name"],
                product.get("description"),
                product["price"],
                product.get("cost"),
                product.get("category"),
                product.get("competitor_sku"),
                product["created_at"],
                product["updated_at"]
            ))
            conn.commit()
            return True
    except sqlite3.IntegrityError as e:
        logger.error(f"Product creation failed: {e}")
        return False


def get_product_by_sku(sku: str, organization_id: str) -> Optional[Dict[str, Any]]:
    """Get product by SKU within organization."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE sku = ? AND organization_id = ?", (sku, organization_id))
        row = cursor.fetchone()
        return dict(row) if row else None


def list_products(organization_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """List all products for an organization."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM products WHERE organization_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (organization_id, limit, offset)
        )
        return [dict(row) for row in cursor.fetchall()]


# Quote operations
def get_quote_with_items(quote_id: str, organization_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get quote with all items. If organization_id provided, validates ownership."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get quote
        if organization_id:
            cursor.execute("""
                SELECT q.*, c.name as customer_name, p.name as project_name, u.name as assignee_name
                FROM quotes q
                LEFT JOIN customers c ON q.customer_id = c.id
                LEFT JOIN projects p ON q.project_id = p.id
                LEFT JOIN users u ON q.assigned_user_id = u.id
                WHERE q.id = ? AND q.organization_id = ?
            """, (quote_id, organization_id))
        else:
            cursor.execute("""
                SELECT q.*, c.name as customer_name, p.name as project_name, u.name as assignee_name
                FROM quotes q
                LEFT JOIN customers c ON q.customer_id = c.id
                LEFT JOIN projects p ON q.project_id = p.id
                LEFT JOIN users u ON q.assigned_user_id = u.id
                WHERE q.id = ?
            """, (quote_id,))
            
        row = cursor.fetchone()
        if not row:
            return None
        
        
        quote = dict(row)
        quote["metadata"] = json.loads(quote.get("metadata") or "{}")
        
        # Get items
        cursor.execute("SELECT * FROM quote_items WHERE quote_id = ?", (quote_id,))
        quote["items"] = [dict(r) for r in cursor.fetchall()]
        
        return quote


def create_quote(quote: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a new quote and return the created quote."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO quotes (id, organization_id, customer_id, project_id, assigned_user_id, status, subtotal, tax_rate, tax_amount, total, notes, token, created_at, updated_at, expires_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                quote["id"],
                quote["organization_id"],
                quote["customer_id"],
                quote.get("project_id"),
                quote.get("assigned_user_id"),
                quote.get("status", "draft"),
                quote.get("subtotal", 0),
                quote.get("tax_rate", 0),
                quote.get("tax_amount", 0),
                quote.get("total", 0),
                quote.get("notes"),
                quote["token"],
                quote["created_at"],
                quote["updated_at"],
                quote.get("expires_at"),
                json.dumps(quote.get("metadata", {}))
            ))
            conn.commit()
            # Return the created quote
            return get_quote_with_items(quote["id"], quote["organization_id"])
    except sqlite3.IntegrityError as e:
        logger.error(f"Quote creation failed: {e}")
        return None


def add_quote_item(item: Dict[str, Any]) -> bool:
    """Add item to quote."""
    # Note: Authorization should be checked before calling this
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO quote_items (id, quote_id, product_id, product_name, sku, description, quantity, unit_price, total_price, competitor_sku)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["id"],
            item["quote_id"],
            item.get("product_id"),
            item.get("product_name"),
            item.get("sku"),
            item.get("description"),
            item["quantity"],
            item["unit_price"],
            item["total_price"],
            item.get("competitor_sku")
        ))
        conn.commit()
        return True


def list_quotes(organization_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """List all quotes for an organization with customer and project names."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT q.*, c.name as customer_name, p.name as project_name, u.name as assignee_name
            FROM quotes q
            LEFT JOIN customers c ON q.customer_id = c.id
            LEFT JOIN projects p ON q.project_id = p.id
            LEFT JOIN users u ON q.assigned_user_id = u.id
            WHERE q.organization_id = ?
            ORDER BY q.created_at DESC
            LIMIT ? OFFSET ?
        """, (organization_id, limit, offset))
        results = []
        for row in cursor.fetchall():
            res = dict(row)
            res["metadata"] = json.loads(res.get("metadata") or "{}")
            results.append(res)
        return results


def update_quote(quote_id: str, updates: Dict[str, Any], organization_id: str) -> bool:
    """Update quote fields."""
    allowed_fields = ["status", "assigned_user_id", "notes", "project_id"]
    set_parts = []
    values = []
    
    for k, v in updates.items():
        if k in allowed_fields:
            set_parts.append(f"{k} = ?")
            values.append(v)
        elif k == "metadata":
            set_parts.append("metadata = ?")
            values.append(json.dumps(v))
    
    if not set_parts:
        return False
    
    values.extend([datetime.utcnow().isoformat(), quote_id, organization_id])
    query = f"UPDATE quotes SET {', '.join(set_parts)}, updated_at = ? WHERE id = ? AND organization_id = ?"
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        return cursor.rowcount > 0


def get_quote_by_token(token: str) -> Optional[Dict[str, Any]]:
    """Get quote by public token."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quotes WHERE token = ?", (token,))
        row = cursor.fetchone()
        if not row:
            return None
        
        quote = dict(row)
        
        # Get items
        cursor.execute("SELECT * FROM quote_items WHERE quote_id = ?", (quote["id"],))
        quote["items"] = [dict(r) for r in cursor.fetchall()]
        
        return quote


# Competitor operations
def save_competitor(competitor: Dict[str, Any]) -> bool:
    """Save or update competitor data."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO competitors (id, organization_id, url, name, title, description, keywords, pricing, features, last_updated, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                competitor.get("id") or competitor["url"],
                competitor["organization_id"],
                competitor["url"],
                competitor.get("name", "Unknown"),
                competitor.get("title"),
                competitor.get("description"),
                json.dumps(competitor.get("keywords", [])),
                competitor.get("pricing"),
                json.dumps(competitor.get("features", [])),
                competitor.get("last_updated", datetime.utcnow().isoformat()),
                competitor.get("error")
            ))
            conn.commit()
            return True
    except sqlite3.IntegrityError as e:
        logger.error(f"Competitor save failed: {e}")
        return False


def get_competitor_by_url(url: str, organization_id: str) -> Optional[Dict[str, Any]]:
    """Get competitor by URL for an organization."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM competitors WHERE url = ? AND organization_id = ?", (url, organization_id))
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data["keywords"] = json.loads(data.get("keywords", "[]"))
            data["features"] = json.loads(data.get("features", "[]"))
            return data
        return None


def list_competitors(organization_id: str) -> List[Dict[str, Any]]:
    """List all competitors for an organization."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM competitors WHERE organization_id = ? ORDER BY last_updated DESC", (organization_id,))
        results = []
        for row in cursor.fetchall():
            data = dict(row)
            data["keywords"] = json.loads(data.get("keywords", "[]"))
            data["features"] = json.loads(data.get("features", "[]"))
            results.append(data)
        return results


# Document operations (for RAG)
def save_document(doc: Dict[str, Any]) -> bool:
    """Save document for RAG."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO documents (id, organization_id, content, source, type, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            doc["id"],
            doc["organization_id"],
            doc["content"],
            doc["source"],
            doc["type"],
            json.dumps(doc.get("metadata", {})),
            doc.get("created_at", datetime.utcnow().isoformat())
        ))
        conn.commit()
        return True


def list_documents(organization_id: str, doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """List documents for an organization, optionally filtered by type."""
    with get_db() as conn:
        cursor = conn.cursor()
        if doc_type:
            cursor.execute("SELECT * FROM documents WHERE organization_id = ? AND type = ? ORDER BY created_at DESC", (organization_id, doc_type))
        else:
            cursor.execute("SELECT * FROM documents WHERE organization_id = ? ORDER BY created_at DESC", (organization_id,))
        
        results = []
        for row in cursor.fetchall():
            data = dict(row)
            data["metadata"] = json.loads(data.get("metadata", "{}"))
            results.append(data)
        return results


# Extraction operations
def save_extraction(extraction: Dict[str, Any]) -> bool:
    """Save data extraction result."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO extractions (id, organization_id, source_type, source_content, parsed_data, confidence_score, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            extraction["id"],
            extraction["organization_id"],
            extraction["source_type"],
            extraction.get("source_content"),
            json.dumps(extraction["parsed_data"]),
            extraction.get("confidence_score"),
            extraction.get("status", "pending"),
            extraction.get("created_at", datetime.utcnow().isoformat())
        ))
        conn.commit()
        return True


def list_extractions(organization_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """List extractions for an organization, optionally filtered by status."""
    with get_db() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM extractions WHERE organization_id = ? AND status = ? ORDER BY created_at DESC", (organization_id, status))
        else:
            cursor.execute("SELECT * FROM extractions WHERE organization_id = ? ORDER BY created_at DESC", (organization_id,))
        
        results = []
        for row in cursor.fetchall():
            data = dict(row)
            data["parsed_data"] = json.loads(data.get("parsed_data", "{}"))
            results.append(data)
        return results


def get_extraction(extraction_id: str, organization_id: str) -> Optional[Dict[str, Any]]:
    """Get single extraction by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM extractions WHERE id = ? AND organization_id = ?",
            (extraction_id, organization_id)
        )
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data["parsed_data"] = json.loads(data.get("parsed_data", "{}"))
            return data
        return None


# Integration Secret operations
def save_integration_secret(organization_id: str, integration_type: str, encrypted_data: str) -> bool:
    """Save or update encrypted integration secret."""
    import uuid
    now = datetime.utcnow().isoformat()
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO integration_secrets (id, organization_id, integration_type, encrypted_data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(organization_id, integration_type) DO UPDATE SET
                    encrypted_data = excluded.encrypted_data,
                    updated_at = excluded.updated_at
            """, (str(uuid.uuid4()), organization_id, integration_type, encrypted_data, now, now))
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Failed to save integration secret: {e}")
        return False


def get_integration_secret(organization_id: str, integration_type: str) -> Optional[str]:
    """Get encrypted integration secret."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT encrypted_data FROM integration_secrets WHERE organization_id = ? AND integration_type = ?",
            (organization_id, integration_type)
        )
        row = cursor.fetchone()
        return row["encrypted_data"] if row else None


def delete_integration_secret(organization_id: str, integration_type: str) -> bool:
    """Delete integration secret."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM integration_secrets WHERE organization_id = ? AND integration_type = ?",
            (organization_id, integration_type)
        )
        conn.commit()
        return cursor.rowcount > 0


# Project operations
def create_project(project: Dict[str, Any]) -> bool:
    """Create a new project."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO projects (id, organization_id, name, address, status, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project["id"],
                project["organization_id"],
                project["name"],
                project.get("address"),
                project.get("status", "active"),
                project["created_at"],
                project["updated_at"],
                json.dumps(project.get("metadata", {}))
            ))
            conn.commit()
            return True
    except sqlite3.IntegrityError as e:
        logger.error(f"Project creation failed: {e}")
        return False

def get_project_by_id(project_id: str, organization_id: str) -> Optional[Dict[str, Any]]:
    """Get project by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ? AND organization_id = ?", (project_id, organization_id))
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data["metadata"] = json.loads(data.get("metadata", "{}"))
            return data
        return None

def list_projects(organization_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """List all projects for an organization."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM projects WHERE organization_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (organization_id, limit, offset)
        )
        results = []
        for row in cursor.fetchall():
            data = dict(row)
            data["metadata"] = json.loads(data.get("metadata", "{}"))
            results.append(data)
        return results

def update_project(project_id: str, updates: Dict[str, Any], organization_id: str) -> bool:
    """Update project fields."""
    allowed_fields = ["name", "address", "status", "metadata"]
    set_parts = []
    values = []
    
    for k, v in updates.items():
        if k in allowed_fields:
            if k == "metadata":
                set_parts.append(f"{k} = ?")
                values.append(json.dumps(v))
            else:
                set_parts.append(f"{k} = ?")
                values.append(v)
    
    if not set_parts:
        return False
    
    values.extend([datetime.utcnow().isoformat(), project_id, organization_id])
    query = f"UPDATE projects SET {', '.join(set_parts)}, updated_at = ? WHERE id = ? AND organization_id = ?"
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        return cursor.rowcount > 0

def get_quotes_by_project(project_id: str, organization_id: str) -> List[Dict[str, Any]]:
    """Get all quotes belonging to a project."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM quotes WHERE project_id = ? AND organization_id = ? ORDER BY created_at DESC",
            (project_id, organization_id)
        )
        return [dict(row) for row in cursor.fetchall()]


# Inbound Email Operations
def create_inbound_email(email: Dict[str, Any]) -> bool:
    """Create a new inbound email record."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO inbound_emails (
                    id, organization_id, sender_email, recipient_email, 
                    subject_line, body_plain, body_html, received_at,
                    status, error_message, has_attachments, attachment_count,
                    message_id, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                email["id"],
                email["organization_id"],
                email["sender_email"],
                email["recipient_email"],
                email.get("subject_line"),
                email.get("body_plain"),
                email.get("body_html"),
                email["received_at"],
                email.get("status", "pending"),
                email.get("error_message"),
                1 if email.get("has_attachments") else 0,
                email.get("attachment_count", 0),
                email.get("message_id"),
                json.dumps(email.get("metadata", {}))
            ))
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Failed to create inbound email: {e}")
        return False

def get_email_by_message_id(message_id: str) -> Optional[Dict[str, Any]]:
    """Get email by its Message-ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inbound_emails WHERE message_id = ?", (message_id,))
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data["metadata"] = json.loads(data.get("metadata", "{}"))
            return data
        return None

def get_inbound_email(email_id: str) -> Optional[Dict[str, Any]]:
    """Get email by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inbound_emails WHERE id = ?", (email_id,))
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data["metadata"] = json.loads(data.get("metadata", "{}"))
            return data
        return None

def update_email_status(email_id: str, status: str, error_message: Optional[str] = None) -> bool:
    """Update the status of an inbound email."""
    with get_db() as conn:
        cursor = conn.cursor()
        if error_message:
            cursor.execute(
                "UPDATE inbound_emails SET status = ?, error_message = ? WHERE id = ?",
                (status, error_message, email_id)
            )
        else:
            cursor.execute(
                "UPDATE inbound_emails SET status = ? WHERE id = ?",
                (status, email_id)
            )
        conn.commit()
        return cursor.rowcount > 0

def list_emails(organization_id: str, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """List inbound emails for an organization."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM inbound_emails WHERE organization_id = ?"
        params = [organization_id]
        
        if status:
            query += " AND status = ?"
            params.append(status)
            
        query += " ORDER BY received_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        results = []
        for row in cursor.fetchall():
            data = dict(row)
            data["metadata"] = json.loads(data.get("metadata", "{}"))
            results.append(data)
        return results

def get_quotes_by_email(email_id: str, organization_id: str) -> List[Dict[str, Any]]:
    """Get all quotes created from a specific email."""
    with get_db() as conn:
        cursor = conn.cursor()
        # Find quotes where metadata['source_email_id'] == email_id
        # In SQLite we might need to search the JSON string in metadata
        cursor.execute("""
            SELECT * FROM quotes 
            WHERE organization_id = ? AND metadata LIKE ?
            ORDER BY created_at DESC
        """, (organization_id, f'%"source_email_id": "{email_id}"%'))
        
        results = []
        for row in cursor.fetchall():
            q_id = row["id"]
            # Fetch with items
            q = get_quote_with_items(q_id, organization_id=organization_id)
            if q:
                results.append(q)
        return results

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email address."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_organization_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """Get organization by slug."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM organizations WHERE slug = ?", (slug,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_organization(organization_id: str) -> Optional[Dict[str, Any]]:
    """Get organization by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM organizations WHERE id = ?", (organization_id,))
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data["settings"] = json.loads(data.get("settings", "{}"))
            data["branding"] = json.loads(data.get("branding", "{}"))
            data["metadata"] = json.loads(data.get("metadata", "{}"))
            return data
        return None


# Email Settings CRUD
def get_email_settings(organization_id: str) -> Optional[Dict[str, Any]]:
    """Get email settings for an organization."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM email_settings WHERE organization_id = ?", (organization_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def create_or_update_email_settings(
    organization_id: str,
    smtp_host: str = 'smtp.gmail.com',
    smtp_port: int = 587,
    smtp_username: str = '',
    smtp_password: str = '',
    from_email: str = '',
    from_name: str = 'Mercura',
    use_tls: bool = True,
    is_enabled: bool = False
) -> Dict[str, Any]:
    """Create or update email settings for an organization."""
    import uuid
    now = datetime.utcnow().isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if settings exist
        cursor.execute("SELECT id FROM email_settings WHERE organization_id = ?", (organization_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update
            cursor.execute("""
                UPDATE email_settings SET
                    smtp_host = ?,
                    smtp_port = ?,
                    smtp_username = ?,
                    smtp_password = ?,
                    from_email = ?,
                    from_name = ?,
                    use_tls = ?,
                    is_enabled = ?,
                    updated_at = ?
                WHERE organization_id = ?
            """, (
                smtp_host, smtp_port, smtp_username, smtp_password,
                from_email or smtp_username, from_name, int(use_tls), int(is_enabled),
                now, organization_id
            ))
        else:
            # Create
            settings_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO email_settings (
                    id, organization_id, smtp_host, smtp_port, smtp_username,
                    smtp_password, from_email, from_name, use_tls, is_enabled,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                settings_id, organization_id, smtp_host, smtp_port, smtp_username,
                smtp_password, from_email or smtp_username, from_name, int(use_tls), int(is_enabled),
                now, now
            ))
        
        conn.commit()
        return get_email_settings(organization_id) or {}


def delete_email_settings(organization_id: str) -> bool:
    """Delete email settings for an organization."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM email_settings WHERE organization_id = ?", (organization_id,))
        conn.commit()
        return cursor.rowcount > 0


# Alerts CRUD
def create_alert(alert: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a new alert."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO alerts (
                    id, organization_id, user_id, alert_type, priority, title, message,
                    action_link, action_text, related_entity_type, related_entity_id,
                    is_read, is_dismissed, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?)
            """, (
                alert["id"],
                alert["organization_id"],
                alert.get("user_id"),
                alert["alert_type"],
                alert["priority"],
                alert["title"],
                alert["message"],
                alert.get("action_link"),
                alert.get("action_text"),
                alert.get("related_entity_type"),
                alert.get("related_entity_id"),
                alert["created_at"]
            ))
            conn.commit()
            return get_alert(alert["id"], alert["organization_id"])
    except Exception as e:
        logger.error(f"Failed to create alert: {e}")
        return None


def get_alert(alert_id: str, organization_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific alert."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM alerts WHERE id = ? AND organization_id = ?
        """, (alert_id, organization_id))
        row = cursor.fetchone()
        return dict(row) if row else None


def list_alerts(
    organization_id: str,
    user_id: Optional[str] = None,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """List alerts for an organization."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM alerts WHERE organization_id = ? AND is_dismissed = 0"
        params = [organization_id]
        
        if user_id:
            query += " AND (user_id = ? OR user_id IS NULL)"
            params.append(user_id)
        
        if unread_only:
            query += " AND is_read = 0"
        
        query += " ORDER BY CASE WHEN priority = 'high' THEN 0 ELSE 1 END, created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def get_unread_alert_count(organization_id: str, user_id: Optional[str] = None) -> int:
    """Get count of unread alerts."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT COUNT(*) as count FROM alerts WHERE organization_id = ? AND is_read = 0 AND is_dismissed = 0"
        params = [organization_id]
        
        if user_id:
            query += " AND (user_id = ? OR user_id IS NULL)"
            params.append(user_id)
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        return row["count"] if row else 0


def mark_alert_read(alert_id: str, organization_id: str) -> bool:
    """Mark an alert as read."""
    with get_db() as conn:
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute("""
            UPDATE alerts SET is_read = 1, read_at = ? 
            WHERE id = ? AND organization_id = ?
        """, (now, alert_id, organization_id))
        conn.commit()
        return cursor.rowcount > 0


def mark_all_alerts_read(organization_id: str, user_id: Optional[str] = None) -> int:
    """Mark all alerts as read."""
    with get_db() as conn:
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        
        query = "UPDATE alerts SET is_read = 1, read_at = ? WHERE organization_id = ? AND is_read = 0"
        params = [now, organization_id]
        
        if user_id:
            query += " AND (user_id = ? OR user_id IS NULL)"
            params.append(user_id)
        
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount


def dismiss_alert(alert_id: str, organization_id: str) -> bool:
    """Dismiss/delete an alert."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE alerts SET is_dismissed = 1 
            WHERE id = ? AND organization_id = ?
        """, (alert_id, organization_id))
        conn.commit()
        return cursor.rowcount > 0


def alert_exists(organization_id: str, alert_type: str, related_entity_id: str, unread_only: bool = True) -> bool:
    """Check if an alert already exists for an entity."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT 1 FROM alerts 
            WHERE organization_id = ? AND alert_type = ? AND related_entity_id = ?
        """
        params = [organization_id, alert_type, related_entity_id]
        
        if unread_only:
            query += " AND is_read = 0 AND is_dismissed = 0"
        
        cursor.execute(query, params)
        return cursor.fetchone() is not None


def auto_resolve_alerts(organization_id: str) -> int:
    """Auto-resolve alerts when conditions change."""
    with get_db() as conn:
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        
        # Get follow-up alerts for quotes that are no longer 'sent'
        cursor.execute("""
            SELECT a.id, a.related_entity_id FROM alerts a
            WHERE a.organization_id = ? 
            AND a.alert_type = 'follow_up_needed'
            AND a.is_read = 0 
            AND a.is_dismissed = 0
        """, (organization_id,))
        
        alerts_to_check = cursor.fetchall()
        resolved_count = 0
        
        for alert in alerts_to_check:
            quote_id = alert["related_entity_id"]
            # Check if quote status changed
            cursor.execute("SELECT status FROM quotes WHERE id = ?", (quote_id,))
            quote_row = cursor.fetchone()
            
            if quote_row and quote_row["status"] != "sent":
                # Auto-resolve
                cursor.execute("""
                    UPDATE alerts SET is_read = 1, read_at = ? 
                    WHERE id = ?
                """, (now, alert["id"]))
                resolved_count += 1
        
        conn.commit()
        return resolved_count


# Subscription CRUD
def get_subscription(organization_id: str) -> Optional[Dict[str, Any]]:
    """Get subscription for an organization."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM subscriptions WHERE organization_id = ?", (organization_id,))
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data["metadata"] = json.loads(data.get("metadata", "{}"))
            return data
        return None


def get_subscription_by_paddle_id(paddle_subscription_id: str) -> Optional[Dict[str, Any]]:
    """Get subscription by Paddle subscription ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM subscriptions WHERE paddle_subscription_id = ?", (paddle_subscription_id,))
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data["metadata"] = json.loads(data.get("metadata", "{}"))
            return data
        return None


def save_cancellation_feedback(
    organization_id: str,
    subscription_id: str,
    reason: Optional[str] = None,
    feedback_text: Optional[str] = None,
) -> bool:
    """Store exit survey feedback when a subscription is canceled."""
    import uuid
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                INSERT INTO cancellation_feedback (
                    id, organization_id, subscription_id, reason, feedback_text, canceled_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                organization_id,
                subscription_id,
                reason or "",
                feedback_text or "",
                now,
                now,
            ))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Failed to save cancellation feedback: {e}")
        return False


def create_subscription(subscription: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a new subscription."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                INSERT INTO subscriptions (
                    id, organization_id, paddle_subscription_id, paddle_customer_id,
                    plan_id, plan_name, status, seats_total, seats_used,
                    price_per_seat, total_amount, billing_interval,
                    current_period_start, current_period_end, trial_ends_at,
                    metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                subscription["id"],
                subscription["organization_id"],
                subscription.get("paddle_subscription_id"),
                subscription.get("paddle_customer_id"),
                subscription["plan_id"],
                subscription.get("plan_name"),
                subscription.get("status", "active"),
                subscription.get("seats_total", 1),
                subscription.get("seats_used", 0),
                subscription.get("price_per_seat", 0),
                subscription.get("total_amount", 0),
                subscription.get("billing_interval", "monthly"),
                subscription.get("current_period_start"),
                subscription.get("current_period_end"),
                subscription.get("trial_ends_at"),
                json.dumps(subscription.get("metadata", {})),
                now,
                now
            ))
            conn.commit()
            return get_subscription(subscription["organization_id"])
    except Exception as e:
        logger.error(f"Failed to create subscription: {e}")
        return None


def update_subscription(organization_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update subscription fields."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            
            # Build update query
            allowed_fields = [
                "paddle_subscription_id", "paddle_customer_id", "plan_id", "plan_name",
                "status", "seats_total", "seats_used", "price_per_seat", "total_amount",
                "billing_interval", "current_period_start", "current_period_end",
                "trial_ends_at", "cancel_at_period_end", "canceled_at"
            ]
            
            fields = []
            values = []
            for field in allowed_fields:
                if field in updates:
                    fields.append(f"{field} = ?")
                    values.append(updates[field])
            
            if not fields:
                return get_subscription(organization_id)
            
            fields.append("updated_at = ?")
            values.append(now)
            values.append(organization_id)
            
            cursor.execute(f"""
                UPDATE subscriptions SET {', '.join(fields)}
                WHERE organization_id = ?
            """, values)
            conn.commit()
            return get_subscription(organization_id)
    except Exception as e:
        logger.error(f"Failed to update subscription: {e}")
        return None


def delete_subscription(organization_id: str) -> bool:
    """Delete a subscription."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM subscriptions WHERE organization_id = ?", (organization_id,))
        conn.commit()
        return cursor.rowcount > 0


# Invoice CRUD
def create_invoice(invoice: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a new invoice."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                INSERT INTO invoices (
                    id, organization_id, subscription_id, paddle_payment_id,
                    invoice_number, amount, currency, status, paid_at,
                    period_start, period_end, receipt_url, pdf_url,
                    metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice["id"],
                invoice["organization_id"],
                invoice.get("subscription_id"),
                invoice.get("paddle_payment_id"),
                invoice.get("invoice_number"),
                invoice["amount"],
                invoice.get("currency", "USD"),
                invoice.get("status", "pending"),
                invoice.get("paid_at"),
                invoice.get("period_start"),
                invoice.get("period_end"),
                invoice.get("receipt_url"),
                invoice.get("pdf_url"),
                json.dumps(invoice.get("metadata", {})),
                now
            ))
            conn.commit()
            return get_invoice(invoice["id"], invoice["organization_id"])
    except Exception as e:
        logger.error(f"Failed to create invoice: {e}")
        return None


def get_invoice(invoice_id: str, organization_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific invoice."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM invoices WHERE id = ? AND organization_id = ?
        """, (invoice_id, organization_id))
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data["metadata"] = json.loads(data.get("metadata", "{}"))
            return data
        return None


def list_invoices(organization_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """List invoices for an organization."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM invoices WHERE organization_id = ?
            ORDER BY created_at DESC LIMIT ?
        """, (organization_id, limit))
        results = []
        for row in cursor.fetchall():
            data = dict(row)
            data["metadata"] = json.loads(data.get("metadata", "{}"))
            results.append(data)
        return results


def update_invoice_status(invoice_id: str, organization_id: str, status: str, paid_at: Optional[str] = None) -> bool:
    """Update invoice status."""
    with get_db() as conn:
        cursor = conn.cursor()
        if paid_at:
            cursor.execute("""
                UPDATE invoices SET status = ?, paid_at = ?
                WHERE id = ? AND organization_id = ?
            """, (status, paid_at, invoice_id, organization_id))
        else:
            cursor.execute("""
                UPDATE invoices SET status = ?
                WHERE id = ? AND organization_id = ?
            """, (status, invoice_id, organization_id))
        conn.commit()
        return cursor.rowcount > 0


# Seat Assignment CRUD
def create_seat_assignment(assignment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a seat assignment."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                INSERT INTO seat_assignments (
                    id, organization_id, subscription_id, user_id,
                    email, name, is_active, assigned_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (
                assignment["id"],
                assignment["organization_id"],
                assignment["subscription_id"],
                assignment.get("user_id"),
                assignment["email"],
                assignment.get("name"),
                now,
                json.dumps(assignment.get("metadata", {}))
            ))
            # Update seats_used in same transaction to avoid partial state on crash
            cursor.execute("""
                UPDATE subscriptions 
                SET seats_used = (SELECT COUNT(*) FROM seat_assignments 
                                  WHERE organization_id = ? AND is_active = 1)
                WHERE organization_id = ?
            """, (assignment["organization_id"], assignment["organization_id"]))
            conn.commit()
            return get_seat_assignment(assignment["id"], assignment["organization_id"])
    except Exception as e:
        logger.error(f"Failed to create seat assignment: {e}")
        return None


def get_seat_assignment(assignment_id: str, organization_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific seat assignment."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM seat_assignments WHERE id = ? AND organization_id = ?
        """, (assignment_id, organization_id))
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data["metadata"] = json.loads(data.get("metadata", "{}"))
            return data
        return None


def list_seat_assignments(organization_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
    """List seat assignments for an organization."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM seat_assignments WHERE organization_id = ?"
        params = [organization_id]
        if active_only:
            query += " AND is_active = 1"
        query += " ORDER BY assigned_at DESC"
        cursor.execute(query, params)
        results = []
        for row in cursor.fetchall():
            data = dict(row)
            data["metadata"] = json.loads(data.get("metadata", "{}"))
            results.append(data)
        return results


def deactivate_seat(assignment_id: str, organization_id: str) -> bool:
    """Deactivate a seat assignment."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE seat_assignments SET is_active = 0
            WHERE id = ? AND organization_id = ?
        """, (assignment_id, organization_id))
        rows_updated = cursor.rowcount
        # Update seats_used in same transaction to avoid partial state on crash
        cursor.execute("""
            UPDATE subscriptions 
            SET seats_used = (SELECT COUNT(*) FROM seat_assignments 
                              WHERE organization_id = ? AND is_active = 1)
            WHERE organization_id = ?
        """, (organization_id, organization_id))
        conn.commit()
        return rows_updated > 0


# ========== CUSTOM DOMAIN OPERATIONS ==========

def get_organization_by_custom_domain(domain: str) -> Optional[Dict[str, Any]]:
    """Get organization by custom domain."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.* FROM organizations o
            JOIN custom_domains cd ON o.id = cd.organization_id
            WHERE cd.domain = ? AND cd.status = 'active'
        """, (domain.lower(),))
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data["settings"] = json.loads(data.get("settings", "{}"))
            data["branding"] = json.loads(data.get("branding", "{}"))
            data["metadata"] = json.loads(data.get("metadata", "{}"))
            return data
        return None


def get_custom_domain(organization_id: str) -> Optional[Dict[str, Any]]:
    """Get custom domain for an organization."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM custom_domains 
            WHERE organization_id = ?
            ORDER BY created_at DESC LIMIT 1
        """, (organization_id,))
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data["dns_records"] = json.loads(data.get("dns_records", "[]"))
            data["metadata"] = json.loads(data.get("metadata", "{}"))
            return data
        return None


def create_custom_domain(domain_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a custom domain entry."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                INSERT INTO custom_domains (
                    id, organization_id, domain, status,
                    verification_token, dns_records, ssl_status,
                    created_at, updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                domain_data["id"],
                domain_data["organization_id"],
                domain_data["domain"].lower(),
                domain_data.get("status", "pending"),
                domain_data.get("verification_token"),
                json.dumps(domain_data.get("dns_records", [])),
                domain_data.get("ssl_status", "pending"),
                now,
                now,
                json.dumps(domain_data.get("metadata", {}))
            ))
            conn.commit()
            return get_custom_domain(domain_data["organization_id"])
    except sqlite3.IntegrityError as e:
        logger.error(f"Custom domain creation failed: {e}")
        return None


def update_custom_domain_status(
    organization_id: str, 
    status: str, 
    ssl_status: Optional[str] = None
) -> bool:
    """Update custom domain verification status."""
    with get_db() as conn:
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        if ssl_status:
            cursor.execute("""
                UPDATE custom_domains 
                SET status = ?, ssl_status = ?, updated_at = ?, verified_at = ?
                WHERE organization_id = ?
            """, (status, ssl_status, now, now, organization_id))
        else:
            cursor.execute("""
                UPDATE custom_domains 
                SET status = ?, updated_at = ?, verified_at = ?
                WHERE organization_id = ? AND status != 'active'
            """, (status, now, now, organization_id))
        conn.commit()
        return cursor.rowcount > 0


def delete_custom_domain(organization_id: str) -> bool:
    """Remove custom domain from organization."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM custom_domains WHERE organization_id = ?
        """, (organization_id,))
        conn.commit()
        return cursor.rowcount > 0


def check_domain_exists(domain: str) -> bool:
    """Check if a domain is already registered by another org."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM custom_domains 
            WHERE domain = ? AND status != 'deleted'
        """, (domain.lower(),))
        return cursor.fetchone()[0] > 0


# Initialize on module load
init_db()
