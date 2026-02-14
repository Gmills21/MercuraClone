"""
Database Migration System for OpenMercura

Production-grade database schema management with:
- Version-controlled migrations
- Transaction safety
- Rollback support
- Schema validation
"""

import os
import sqlite3
import hashlib
import json
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from app.database_sqlite import get_db, DB_PATH


@dataclass
class Migration:
    """Represents a database migration."""
    version: int
    name: str
    description: str
    up_sql: str
    down_sql: Optional[str] = None
    checksum: Optional[str] = None
    applied_at: Optional[str] = None


class MigrationManager:
    """
    Manages database migrations.
    
    Features:
    - Version-controlled schema changes
    - Transaction-safe migrations
    - Checksum verification
    - Rollback support
    - Migration history tracking
    """
    
    def __init__(self, migrations_dir: str = "migrations"):
        self.migrations_dir = Path(migrations_dir)
        self.migrations_dir.mkdir(exist_ok=True)
        self._init_migration_table()
    
    def _init_migration_table(self):
        """Initialize the migrations tracking table."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS _migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    applied_at TEXT NOT NULL,
                    execution_time_ms INTEGER,
                    success INTEGER NOT NULL DEFAULT 1
                )
            """)
            conn.commit()
    
    def _calculate_checksum(self, sql: str) -> str:
        """Calculate MD5 checksum of SQL."""
        return hashlib.md5(sql.encode('utf-8')).hexdigest()
    
    def get_current_version(self) -> int:
        """Get current database version."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(version) FROM _migrations WHERE success = 1")
            result = cursor.fetchone()
            return result[0] or 0
    
    def get_migration_history(self) -> List[Dict]:
        """Get list of applied migrations."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT version, name, description, applied_at, execution_time_ms, success
                FROM _migrations
                ORDER BY version DESC
            """)
            return [
                {
                    "version": row[0],
                    "name": row[1],
                    "description": row[2],
                    "applied_at": row[3],
                    "execution_time_ms": row[4],
                    "success": bool(row[5])
                }
                for row in cursor.fetchall()
            ]
    
    def create_migration(self, name: str, description: str, up_sql: str, down_sql: Optional[str] = None) -> int:
        """
        Create a new migration file.
        
        Args:
            name: Migration name (e.g., "add_user_indexes")
            description: Human-readable description
            up_sql: SQL to apply the migration
            down_sql: SQL to rollback (optional)
            
        Returns:
            Migration version number
        """
        version = self.get_current_version() + 1
        
        migration = {
            "version": version,
            "name": name,
            "description": description,
            "up_sql": up_sql,
            "down_sql": down_sql,
            "created_at": datetime.utcnow().isoformat()
        }
        
        filename = f"{version:04d}_{name}.json"
        filepath = self.migrations_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(migration, f, indent=2)
        
        logger.info(f"Created migration {version}: {name}")
        return version
    
    def load_migrations(self) -> List[Migration]:
        """Load all migration files from disk."""
        migrations = []
        
        for filepath in sorted(self.migrations_dir.glob("*.json")):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                migration = Migration(
                    version=data["version"],
                    name=data["name"],
                    description=data["description"],
                    up_sql=data["up_sql"],
                    down_sql=data.get("down_sql"),
                    checksum=self._calculate_checksum(data["up_sql"]),
                    applied_at=data.get("created_at")
                )
                migrations.append(migration)
            except Exception as e:
                logger.error(f"Failed to load migration {filepath}: {e}")
        
        return sorted(migrations, key=lambda m: m.version)
    
    def migrate(self, target_version: Optional[int] = None) -> bool:
        """
        Run pending migrations.
        
        Args:
            target_version: Target version to migrate to (None = latest)
            
        Returns:
            True if successful
        """
        current_version = self.get_current_version()
        migrations = self.load_migrations()
        
        # Filter migrations to apply
        pending = [m for m in migrations if m.version > current_version]
        
        if target_version:
            pending = [m for m in pending if m.version <= target_version]
        
        if not pending:
            logger.info("No pending migrations")
            return True
        
        logger.info(f"Applying {len(pending)} migrations (current: {current_version})")
        
        for migration in pending:
            if not self._apply_migration(migration):
                logger.error(f"Migration {migration.version} failed. Stopping.")
                return False
        
        return True
    
    def _apply_migration(self, migration: Migration) -> bool:
        """Apply a single migration with transaction safety."""
        start_time = datetime.utcnow()
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if already applied
            cursor.execute(
                "SELECT checksum FROM _migrations WHERE version = ?",
                (migration.version,)
            )
            existing = cursor.fetchone()
            
            if existing:
                if existing[0] != migration.checksum:
                    logger.error(
                        f"Migration {migration.version} checksum mismatch! "
                        f"Expected: {migration.checksum}, Found: {existing[0]}"
                    )
                    return False
                logger.info(f"Migration {migration.version} already applied, skipping")
                return True
            
            try:
                # Execute migration in transaction
                cursor.executescript(migration.up_sql)
                
                # Record migration
                execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                cursor.execute("""
                    INSERT INTO _migrations (version, name, description, checksum, applied_at, execution_time_ms, success)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (
                    migration.version,
                    migration.name,
                    migration.description,
                    migration.checksum,
                    datetime.utcnow().isoformat(),
                    execution_time
                ))
                
                conn.commit()
                logger.info(f"Applied migration {migration.version}: {migration.name} ({execution_time}ms)")
                return True
                
            except Exception as e:
                conn.rollback()
                
                # Record failed migration
                cursor.execute("""
                    INSERT INTO _migrations (version, name, description, checksum, applied_at, success)
                    VALUES (?, ?, ?, ?, ?, 0)
                """, (
                    migration.version,
                    migration.name,
                    migration.description,
                    migration.checksum,
                    datetime.utcnow().isoformat()
                ))
                conn.commit()
                
                logger.error(f"Migration {migration.version} failed: {e}")
                return False
    
    def rollback(self, steps: int = 1) -> bool:
        """
        Rollback migrations.
        
        Args:
            steps: Number of migrations to rollback
            
        Returns:
            True if successful
        """
        history = self.get_migration_history()
        migrations_to_rollback = [m for m in history if m["success"]][:steps]
        
        if not migrations_to_rollback:
            logger.info("No migrations to rollback")
            return True
        
        for migration_info in migrations_to_rollback:
            version = migration_info["version"]
            
            # Load full migration
            filepath = self.migrations_dir / f"{version:04d}_*.json"
            matching = list(self.migrations_dir.glob(f"{version:04d}_*.json"))
            
            if not matching:
                logger.error(f"Migration file not found for version {version}")
                return False
            
            with open(matching[0], 'r') as f:
                data = json.load(f)
            
            if not data.get("down_sql"):
                logger.error(f"Migration {version} has no rollback script")
                return False
            
            with get_db() as conn:
                cursor = conn.cursor()
                try:
                    cursor.executescript(data["down_sql"])
                    cursor.execute(
                        "DELETE FROM _migrations WHERE version = ?",
                        (version,)
                    )
                    conn.commit()
                    logger.info(f"Rolled back migration {version}")
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Rollback of migration {version} failed: {e}")
                    return False
        
        return True
    
    def verify(self) -> Tuple[bool, List[str]]:
        """
        Verify database schema integrity.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check for migrations with mismatched checksums
            cursor.execute("SELECT version, checksum FROM _migrations WHERE success = 1")
            applied = {row[0]: row[1] for row in cursor.fetchall()}
            
            for migration in self.load_migrations():
                if migration.version in applied:
                    if migration.checksum != applied[migration.version]:
                        issues.append(
                            f"Migration {migration.version} checksum mismatch"
                        )
            
            # Check for missing indexes on foreign keys
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                if table.startswith("_"):
                    continue
                
                cursor.execute(f"PRAGMA foreign_key_list({table})")
                fks = cursor.fetchall()
                
                cursor.execute(f"PRAGMA index_list({table})")
                indexes = {row[1] for row in cursor.fetchall()}
                
                for fk in fks:
                    col_name = fk[3]  # from column
                    expected_idx = f"idx_{table}_{col_name}"
                    if expected_idx not in indexes and f"idx_{table}_{col_name}_" not in " ".join(indexes):
                        issues.append(f"Table '{table}' missing index on FK column '{col_name}'")
        
        return len(issues) == 0, issues


# Global migration manager instance
migration_manager = MigrationManager()


# =============================================================================
# DATABASE INDEXES MIGRATION
# =============================================================================

def create_performance_indexes_migration():
    """Create migration for performance-critical indexes."""
    
    up_sql = """
-- Performance indexes for high-traffic queries

-- Quotes indexes for dashboard loading
CREATE INDEX IF NOT EXISTS idx_quotes_org_status ON quotes(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_quotes_created ON quotes(organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_quotes_expires ON quotes(expires_at) WHERE expires_at IS NOT NULL;

-- Customers indexes for search
CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_customers_company ON customers(company COLLATE NOCASE);

-- Products indexes for catalog
CREATE INDEX IF NOT EXISTS idx_products_category ON products(organization_id, category);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name COLLATE NOCASE);

-- Quote items for aggregation
CREATE INDEX IF NOT EXISTS idx_quote_items_product ON quote_items(product_id);

-- Alerts for notification queries
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_priority ON alerts(priority, created_at DESC);

-- Inbound emails for processing
CREATE INDEX IF NOT EXISTS idx_inbound_emails_received ON inbound_emails(received_at DESC);
CREATE INDEX IF NOT EXISTS idx_inbound_emails_sender ON inbound_emails(sender_email);

-- Competitors for analysis
CREATE INDEX IF NOT EXISTS idx_competitors_updated ON competitors(last_updated DESC);

-- Users for auth
CREATE INDEX IF NOT EXISTS idx_users_email_active ON users(email, is_active) WHERE is_active = 1;

-- Analytics for reporting
CREATE INDEX IF NOT EXISTS idx_analytics_date ON analytics_events(organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_type ON analytics_events(event_type, created_at DESC);
"""
    
    down_sql = """
DROP INDEX IF EXISTS idx_quotes_org_status;
DROP INDEX IF EXISTS idx_quotes_created;
DROP INDEX IF EXISTS idx_quotes_expires;
DROP INDEX IF EXISTS idx_customers_name;
DROP INDEX IF EXISTS idx_customers_company;
DROP INDEX IF EXISTS idx_products_category;
DROP INDEX IF EXISTS idx_products_name;
DROP INDEX IF EXISTS idx_quote_items_product;
DROP INDEX IF EXISTS idx_alerts_created;
DROP INDEX IF EXISTS idx_alerts_priority;
DROP INDEX IF EXISTS idx_inbound_emails_received;
DROP INDEX IF EXISTS idx_inbound_emails_sender;
DROP INDEX IF EXISTS idx_competitors_updated;
DROP INDEX IF EXISTS idx_users_email_active;
DROP INDEX IF EXISTS idx_analytics_date;
DROP INDEX IF EXISTS idx_analytics_type;
"""
    
    return migration_manager.create_migration(
        name="performance_indexes",
        description="Add performance-critical indexes for production workload",
        up_sql=up_sql,
        down_sql=down_sql
    )


# =============================================================================
# CLI COMMANDS
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migrations.py <command> [args]")
        print("Commands:")
        print("  status              - Show migration status")
        print("  migrate [version]   - Run pending migrations")
        print("  rollback [steps]    - Rollback migrations")
        print("  create <name>       - Create new migration template")
        print("  verify              - Verify schema integrity")
        print("  create-indexes      - Create performance indexes migration")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "status":
        current = migration_manager.get_current_version()
        history = migration_manager.get_migration_history()
        pending = len([m for m in migration_manager.load_migrations() if m.version > current])
        
        print(f"Current version: {current}")
        print(f"Pending migrations: {pending}")
        print(f"\nLast 5 applied migrations:")
        for m in history[:5]:
            status = "✓" if m["success"] else "✗"
            print(f"  {status} {m['version']:04d} - {m['name']} ({m['applied_at'][:10]})")
    
    elif cmd == "migrate":
        target = int(sys.argv[2]) if len(sys.argv) > 2 else None
        success = migration_manager.migrate(target)
        sys.exit(0 if success else 1)
    
    elif cmd == "rollback":
        steps = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        success = migration_manager.rollback(steps)
        sys.exit(0 if success else 1)
    
    elif cmd == "create":
        if len(sys.argv) < 3:
            print("Usage: python migrations.py create <name>")
            sys.exit(1)
        name = sys.argv[2]
        version = migration_manager.create_migration(name, "TODO: Add description", "-- TODO: Add migration SQL")
        print(f"Created migration {version}: {name}")
    
    elif cmd == "verify":
        is_valid, issues = migration_manager.verify()
        if is_valid:
            print("✓ Database schema is valid")
        else:
            print("✗ Schema issues found:")
            for issue in issues:
                print(f"  - {issue}")
        sys.exit(0 if is_valid else 1)
    
    elif cmd == "create-indexes":
        version = create_performance_indexes_migration()
        print(f"Created indexes migration: version {version}")
    
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
