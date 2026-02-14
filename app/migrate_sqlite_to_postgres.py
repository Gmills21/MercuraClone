"""
Database Migration Utility
Migrate data from SQLite to PostgreSQL.

Usage:
    # Set environment variables
    export SOURCE_DB="sqlite:///mercura.db"
    export TARGET_DB="postgresql://user:pass@localhost/mercura"
    
    # Run migration
    python -m app.migrate_sqlite_to_postgres
"""

import os
import sys
from typing import Type

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Import models
from app.models_sqlalchemy import Base
from app.database_sqlite import get_db as get_sqlite_db, DB_PATH


def migrate_table(sqlite_session, postgres_session, model_class: Type, batch_size: int = 100):
    """Migrate a single table from SQLite to PostgreSQL."""
    table_name = model_class.__tablename__
    logger.info(f"Migrating table: {table_name}")
    
    # Get count
    count = sqlite_session.query(model_class).count()
    logger.info(f"  Found {count} records")
    
    if count == 0:
        logger.info(f"  Skipping empty table")
        return
    
    # Migrate in batches
    offset = 0
    migrated = 0
    
    while offset < count:
        records = sqlite_session.query(model_class).offset(offset).limit(batch_size).all()
        
        for record in records:
            # Create a new instance for PostgreSQL
            # Convert SQLAlchemy object to dict, then create new instance
            from sqlalchemy import inspect
            
            mapper = inspect(model_class)
            data = {}
            for column in mapper.columns:
                data[column.name] = getattr(record, column.name)
            
            # Create new record
            new_record = model_class(**data)
            postgres_session.merge(new_record)  # merge handles conflicts
        
        postgres_session.commit()
        migrated += len(records)
        offset += batch_size
        
        if offset % 1000 == 0 or offset >= count:
            logger.info(f"  Migrated {migrated}/{count} records")
    
    logger.info(f"  Completed: {migrated} records migrated")


def migrate_data(source_url: str, target_url: str):
    """Migrate all data from source to target database."""
    logger.info(f"Migrating from: {source_url}")
    logger.info(f"Migrating to: {target_url}")
    
    # Create engines
    source_engine = create_engine(source_url)
    target_engine = create_engine(target_url)
    
    # Create sessions
    SourceSession = sessionmaker(bind=source_engine)
    TargetSession = sessionmaker(bind=target_engine)
    
    # Create tables in target
    logger.info("Creating tables in target database...")
    Base.metadata.create_all(bind=target_engine)
    
    # Import models
    from app.models_sqlalchemy import (
        User, Organization, OrganizationMember, OrganizationInvitation,
        Customer, Product, Project, Quote, QuoteItem,
        InboundEmail, PasswordResetToken, Competitor, Extraction,
        Session, IntegrationSecret
    )
    
    # Order matters for foreign keys
    tables = [
        User,  # Users first (no FK dependencies)
        Organization,
        OrganizationMember,
        OrganizationInvitation,
        Customer,
        Product,
        Project,
        Quote,
        QuoteItem,
        InboundEmail,
        PasswordResetToken,
        Competitor,
        Extraction,
        Session,
        IntegrationSecret,
    ]
    
    with SourceSession() as source_session:
        with TargetSession() as target_session:
            for model_class in tables:
                try:
                    migrate_table(source_session, target_session, model_class)
                except Exception as e:
                    logger.error(f"Failed to migrate {model_class.__tablename__}: {e}")
                    raise
    
    logger.info("Migration completed successfully!")


def main():
    """Main entry point."""
    # Get database URLs
    source_url = os.getenv("SOURCE_DB", f"sqlite:///{DB_PATH}")
    target_url = os.getenv("TARGET_DB")
    
    if not target_url:
        print("Error: TARGET_DB environment variable not set")
        print("\nExample:")
        print('  export TARGET_DB="postgresql://user:password@localhost/mercura"')
        print("\nOr set in .env file:")
        print('  TARGET_DB=postgresql://user:password@localhost/mercura')
        sys.exit(1)
    
    if "postgresql" not in target_url.lower():
        print("Warning: Target doesn't look like PostgreSQL URL")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    # Confirm
    print("\nMigration plan:")
    print(f"  From: {source_url}")
    print(f"  To:   {target_url}")
    print("\nThis will:")
    print("  1. Create tables in target database")
    print("  2. Copy all data from source to target")
    print("  3. Preserve relationships and foreign keys")
    print("\nNote: Existing data in target will be updated (not deleted)")
    
    response = input("\nProceed? (y/N): ")
    if response.lower() != 'y':
        print("Aborted")
        sys.exit(0)
    
    # Run migration
    try:
        migrate_data(source_url, target_url)
        print("\nMigration completed!")
        print("\nNext steps:")
        print("  1. Update your .env file:")
        print(f'     DATABASE_URL={target_url}')
        print("  2. Restart your application")
        print("  3. Verify data is intact")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
