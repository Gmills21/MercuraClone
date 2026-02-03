"""
Database Migration Script
Adds organization_id to all data tables for proper multi-tenancy.

⚠️ CRITICAL: This script adds data isolation to prevent data leakage between companies.
"""

import sqlite3
import os
from loguru import logger
from datetime import datetime

# Database path
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_PATH = os.path.join(DB_DIR, "mercura.db")


def migrate_add_organization_id():
    """
    Add organization_id column to all data tables.
    This is THE critical multi-tenancy fix.
    """
    logger.info("=" * 60)
    logger.info("STARTING MULTI-TENANCY MIGRATION")
    logger.info("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Tables that need organization_id
        tables_to_migrate = [
            ("customers", "organization_id TEXT NOT NULL DEFAULT 'default'"),
            ("products", "organization_id TEXT NOT NULL DEFAULT 'default'"),
            ("quotes", "organization_id TEXT NOT NULL DEFAULT 'default'"),
            ("documents", "organization_id TEXT NOT NULL DEFAULT 'default'"),
            ("competitors", "organization_id TEXT NOT NULL DEFAULT 'default'"),
            ("extractions", "organization_id TEXT NOT NULL DEFAULT 'default'"),
        ]
        
        for table_name, column_def in tables_to_migrate:
            # Check if column already exists
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "organization_id" not in columns:
                logger.info(f"Adding organization_id to {table_name}...")
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_def}")
                
                # Create index on organization_id
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{table_name}_org_id 
                    ON {table_name}(organization_id)
                """)
                
                logger.success(f"✓ Added organization_id to {table_name}")
            else:
                logger.info(f"✓ {table_name} already has organization_id column")
        
        # Add user_id to quotes table if missing (for attribution)
        cursor.execute("PRAGMA table_info(quotes)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "user_id" not in columns:
            logger.info("Adding user_id to quotes...")
            cursor.execute("""
                ALTER TABLE quotes 
                ADD COLUMN user_id TEXT
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_quotes_user_id 
                ON quotes(user_id)
            """)
            logger.success("✓ Added user_id to quotes")
        
        # Add user_id to customers table if missing
        cursor.execute("PRAGMA table_info(customers)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "user_id" not in columns:
            logger.info("Adding user_id to customers...")
            cursor.execute("""
                ALTER TABLE customers 
                ADD COLUMN user_id TEXT
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_customers_user_id 
                ON customers(user_id)
            """)
            logger.success("✓ Added user_id to customers")
        
        # Add user_id to products table if missing
        cursor.execute("PRAGMA table_info(products)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "user_id" not in columns:
            logger.info("Adding user_id to products...")
            cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN user_id TEXT
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_products_user_id 
                ON products(user_id)
            """)
            logger.success("✓ Added user_id to products")
        
        conn.commit()
        
        logger.info("=" * 60)
        logger.success("✓ MIGRATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info("Multi-tenancy data isolation is now active!")
        logger.info("All queries MUST now filter by organization_id/user_id")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def verify_migration():
    """Verify that migration was successful."""
    logger.info("Verifying migration...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables = ["customers", "products", "quotes", "documents", "competitors", "extractions"]
    all_good = True
    
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "organization_id" in columns:
            logger.success(f"✓ {table} has organization_id")
        else:
            logger.error(f"✗ {table} MISSING organization_id")
            all_good = False
    
    conn.close()
    
    if all_good:
        logger.success("✓ All tables have organization_id - migration verified!")
    else:
        logger.error("✗ Migration incomplete - some tables are missing organization_id")
    
    return all_good


if __name__ == "__main__":
    logger.info("Running database migration for multi-tenancy...")
    migrate_add_organization_id()
    verify_migration()
