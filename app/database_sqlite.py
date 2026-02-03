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

# Database path
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_PATH = os.path.join(DB_DIR, "mercura.db")

# Ensure data directory exists
os.makedirs(DB_DIR, exist_ok=True)


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
        
        # Create default admin user if no users exist
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            import hashlib
            import secrets
            salt = secrets.token_hex(16)
            pwdhash = hashlib.pbkdf2_hmac('sha256', 'admin123'.encode(), salt.encode(), 100000)
            password_hash = salt + pwdhash.hex()
            
            now = datetime.utcnow().isoformat()
            cursor.execute("""
                INSERT INTO users (id, email, name, password_hash, role, company_id, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, ('admin-001', 'admin@openmercura.local', 'System Admin', password_hash, 'admin', 'default', now, 1))
            logger.info("Created default admin user: admin@openmercura.local / admin123")
        
        # Customers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                company TEXT,
                phone TEXT,
                address TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                sku TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                cost REAL,
                category TEXT,
                competitor_sku TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Quotes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotes (
                id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
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
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        """)
        
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competitors (
                id TEXT PRIMARY KEY,
                url TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                title TEXT,
                description TEXT,
                keywords TEXT,
                pricing TEXT,
                features TEXT,
                last_updated TEXT NOT NULL,
                error TEXT
            )
        """)
        
        # Documents table (for RAG)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                source TEXT NOT NULL,
                type TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # Extractions table (CRM data capture)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extractions (
                id TEXT PRIMARY KEY,
                source_type TEXT NOT NULL,
                source_content TEXT,
                parsed_data TEXT NOT NULL,
                confidence_score REAL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                processed_at TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_email ON customers (email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_sku ON products (sku)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotes_customer ON quotes (customer_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quote_items_quote ON quote_items (quote_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_competitors_url ON competitors (url)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_type ON documents (type)")
        
        conn.commit()
        logger.info("Database initialized successfully")


# Customer operations
def create_customer(customer: Dict[str, Any]) -> bool:
    """Create a new customer."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO customers (id, name, email, company, phone, address, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer["id"],
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


def get_customer_by_id(customer_id: str) -> Optional[Dict[str, Any]]:
    """Get customer by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_customer_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get customer by email."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE email = ?", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None


def list_customers(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """List all customers."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM customers ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [dict(row) for row in cursor.fetchall()]


def update_customer(customer_id: str, updates: Dict[str, Any]) -> bool:
    """Update customer fields."""
    allowed_fields = ["name", "email", "company", "phone", "address"]
    set_clause = ", ".join([f"{k} = ?" for k in updates.keys() if k in allowed_fields])
    if not set_clause:
        return False
    
    values = [updates[k] for k in updates.keys() if k in allowed_fields]
    values.append(datetime.utcnow().isoformat())
    values.append(customer_id)
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE customers SET {set_clause}, updated_at = ?
            WHERE id = ?
        """, values)
        conn.commit()
        return cursor.rowcount > 0


# Product operations
def create_product(product: Dict[str, Any]) -> bool:
    """Create a new product."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO products (id, sku, name, description, price, cost, category, competitor_sku, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product["id"],
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


def get_product_by_sku(sku: str) -> Optional[Dict[str, Any]]:
    """Get product by SKU."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE sku = ?", (sku,))
        row = cursor.fetchone()
        return dict(row) if row else None


def list_products(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """List all products."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM products ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [dict(row) for row in cursor.fetchall()]


# Quote operations
def get_quote_with_items(quote_id: str) -> Optional[Dict[str, Any]]:
    """Get quote with all items."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get quote
        cursor.execute("SELECT * FROM quotes WHERE id = ?", (quote_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        quote = dict(row)
        
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
                INSERT INTO quotes (id, customer_id, status, subtotal, tax_rate, tax_amount, total, notes, token, created_at, updated_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                quote["id"],
                quote["customer_id"],
                quote.get("status", "draft"),
                quote.get("subtotal", 0),
                quote.get("tax_rate", 0),
                quote.get("tax_amount", 0),
                quote.get("total", 0),
                quote.get("notes"),
                quote["token"],
                quote["created_at"],
                quote["updated_at"],
                quote.get("expires_at")
            ))
            conn.commit()
            # Return the created quote
            return get_quote_with_items(quote["id"])
    except sqlite3.IntegrityError as e:
        logger.error(f"Quote creation failed: {e}")
        return None


def add_quote_item(item: Dict[str, Any]) -> bool:
    """Add item to quote."""
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


def list_quotes(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """List all quotes."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM quotes ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [dict(row) for row in cursor.fetchall()]


# Competitor operations
def save_competitor(competitor: Dict[str, Any]) -> bool:
    """Save or update competitor data."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO competitors (id, url, name, title, description, keywords, pricing, features, last_updated, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            competitor.get("id") or competitor["url"],
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


def get_competitor_by_url(url: str) -> Optional[Dict[str, Any]]:
    """Get competitor by URL."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM competitors WHERE url = ?", (url,))
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data["keywords"] = json.loads(data.get("keywords", "[]"))
            data["features"] = json.loads(data.get("features", "[]"))
            return data
        return None


def list_competitors() -> List[Dict[str, Any]]:
    """List all competitors."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM competitors ORDER BY last_updated DESC")
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
            INSERT INTO documents (id, content, source, type, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            doc["id"],
            doc["content"],
            doc["source"],
            doc["type"],
            json.dumps(doc.get("metadata", {})),
            doc.get("created_at", datetime.utcnow().isoformat())
        ))
        conn.commit()
        return True


def list_documents(doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """List documents, optionally filtered by type."""
    with get_db() as conn:
        cursor = conn.cursor()
        if doc_type:
            cursor.execute("SELECT * FROM documents WHERE type = ? ORDER BY created_at DESC", (doc_type,))
        else:
            cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
        
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
            INSERT INTO extractions (id, source_type, source_content, parsed_data, confidence_score, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            extraction["id"],
            extraction["source_type"],
            extraction.get("source_content"),
            json.dumps(extraction["parsed_data"]),
            extraction.get("confidence_score"),
            extraction.get("status", "pending"),
            extraction.get("created_at", datetime.utcnow().isoformat())
        ))
        conn.commit()
        return True


def list_extractions(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """List extractions, optionally filtered by status."""
    with get_db() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM extractions WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM extractions ORDER BY created_at DESC")
        
        results = []
        for row in cursor.fetchall():
            data = dict(row)
            data["parsed_data"] = json.loads(data.get("parsed_data", "{}"))
            results.append(data)
        return results


# Initialize on module load
init_db()
