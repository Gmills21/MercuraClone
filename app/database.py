"""
Unified Database Interface
Automatically selects between SQLite (legacy) and SQLAlchemy (PostgreSQL/SQLite)
based on the DATABASE_URL environment variable.
"""

import os
from loguru import logger

# Check which database to use
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///mercura.db")
USE_SQLALCHEMY = os.getenv("USE_SQLALCHEMY", "auto").lower()

# Auto-detect: use SQLAlchemy for PostgreSQL, legacy for SQLite
if USE_SQLALCHEMY == "auto":
    USE_SQLALCHEMY = "postgresql" in DATABASE_URL.lower()
elif USE_SQLALCHEMY in ("true", "1", "yes"):
    USE_SQLALCHEMY = True
else:
    USE_SQLALCHEMY = False

if USE_SQLALCHEMY:
    logger.info("Using SQLAlchemy database layer (PostgreSQL/SQLite)")
    
    # Import SQLAlchemy components
    from app.database_sqlalchemy import (
        engine,
        SessionLocal,
        Base,
        get_db_session,
        get_db_context,
        init_database as init_db,
        get_database_info
    )
    from app.models_sqlalchemy import (
        User, Organization, Customer, Product, Quote, QuoteItem,
        OrganizationMember, OrganizationInvitation, Project,
        InboundEmail, PasswordResetToken, Competitor, Extraction,
        Session, IntegrationSecret
    )
    
    # Flag for checking which mode we're in
    IS_SQLALCHEMY = True
    
    # Compatibility wrapper for get_db
    def get_db():
        """Get database session (compatible with legacy code)."""
        return get_db_context()
    
else:
    logger.info("Using legacy SQLite database layer")
    
    # Import legacy SQLite components
    from app.database_sqlite import (
        get_db,
        init_db,
        get_db as get_db_context  # Legacy get_db is a context manager
    )
    
    # Flag for checking which mode we're in
    IS_SQLALCHEMY = False
    
    # Stub functions for SQLAlchemy-only features
    def get_db_session():
        """Not available in legacy mode."""
        raise NotImplementedError("get_db_session requires SQLAlchemy mode")
    
    def get_database_info():
        """Get database info for legacy mode."""
        from app.database_sqlite import DB_PATH
        return {
            "type": "sqlite",
            "mode": "legacy",
            "file_path": DB_PATH
        }
    
    def init_database():
        """Initialize database in legacy mode."""
        init_db()


def get_database_status() -> dict:
    """Get current database status and configuration."""
    return {
        "is_sqlalchemy": IS_SQLALCHEMY,
        "database_url_masked": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL,
        "info": get_database_info()
    }


# On module load, log the configuration
logger.info(f"Database mode: {'SQLAlchemy' if IS_SQLALCHEMY else 'Legacy SQLite'}")
logger.info(f"Database URL type: {'PostgreSQL' if 'postgresql' in DATABASE_URL.lower() else 'SQLite'}")
