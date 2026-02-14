"""
Database Layer with SQLAlchemy
Supports both SQLite (dev) and PostgreSQL (production)
"""

import os
from typing import Generator, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from loguru import logger

from app.config import settings


# Get database URL from settings
database_url = settings.database_url

# Convert SQLite URL for SQLAlchemy if needed
if database_url.startswith("sqlite:///"):
    # SQLAlchemy handles sqlite URLs directly
    SQLALCHEMY_DATABASE_URL = database_url
    # Add connect args for SQLite
    connect_args = {"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
else:
    SQLALCHEMY_DATABASE_URL = database_url
    connect_args = {}

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=300,    # Recycle connections after 5 minutes
    echo=settings.debug  # Log SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# SQLite-specific optimizations
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key support for SQLite."""
    if "sqlite" in SQLALCHEMY_DATABASE_URL:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db_session() -> Generator[Session, None, None]:
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_database():
    """Initialize database - create all tables."""
    logger.info(f"Initializing database: {SQLALCHEMY_DATABASE_URL.split('@')[-1] if '@' in SQLALCHEMY_DATABASE_URL else SQLALCHEMY_DATABASE_URL}")
    
    # Import all models to ensure they're registered
    from app import models_sqlalchemy
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    logger.info("Database tables created")
    
    # Run seed data if needed
    _seed_initial_data()


def _seed_initial_data():
    """Seed initial data if database is empty."""
    db = SessionLocal()
    try:
        # Check if we have any users
        from app.models_sqlalchemy import User
        user_count = db.query(User).count()
        
        if user_count == 0:
            logger.info("Creating default admin user...")
            import uuid
            from datetime import datetime
            from app.auth import _hash_password
            
            admin_user = User(
                id=str(uuid.uuid4()),
                email="admin@openmercura.local",
                name="System Admin",
                password_hash=_hash_password("admin123"),
                role="admin",
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(admin_user)
            db.commit()
            logger.info("Default admin user created: admin@openmercura.local / admin123")
    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


def get_database_info() -> dict:
    """Get information about the current database."""
    is_sqlite = "sqlite" in SQLALCHEMY_DATABASE_URL
    
    info = {
        "type": "sqlite" if is_sqlite else "postgresql",
        "url_masked": SQLALCHEMY_DATABASE_URL.split("@")[-1] if "@" in SQLALCHEMY_DATABASE_URL else SQLALCHEMY_DATABASE_URL,
        "sqlalchemy_available": True
    }
    
    if is_sqlite:
        # Get SQLite file info
        db_path = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "")
        if os.path.exists(db_path):
            info["file_size_mb"] = round(os.path.getsize(db_path) / (1024 * 1024), 2)
            info["file_path"] = os.path.abspath(db_path)
    
    return info
