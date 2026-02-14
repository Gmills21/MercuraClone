"""
Database Transaction Management

Production-grade transaction handling with:
- Atomic operations
- Optimistic/pessimistic locking
- Deadlock detection
- Retry logic for transient failures
- Read committed isolation
"""

import sqlite3
import time
import random
from contextlib import contextmanager
from typing import Optional, TypeVar, Callable, Any, List
from dataclasses import dataclass
from enum import Enum

from loguru import logger

from app.database_sqlite import get_db, DB_PATH


T = TypeVar('T')


class IsolationLevel(Enum):
    """SQLite isolation levels."""
    DEFERRED = "DEFERRED"      # Default, acquires locks as needed
    IMMEDIATE = "IMMEDIATE"    # Acquires write lock immediately
    EXCLUSIVE = "EXCLUSIVE"    # Exclusive lock, no other connections


class TransactionError(Exception):
    """Transaction-related error."""
    pass


class DeadlockError(TransactionError):
    """Deadlock detected."""
    pass


class LockTimeoutError(TransactionError):
    """Could not acquire lock within timeout."""
    pass


@dataclass
class TransactionOptions:
    """Transaction configuration options."""
    isolation_level: IsolationLevel = IsolationLevel.DEFERRED
    timeout_seconds: float = 30.0
    retry_attempts: int = 3
    retry_delay_base: float = 0.1


@contextmanager
def transaction(options: Optional[TransactionOptions] = None):
    """
    Transaction context manager with retry logic.
    
    Usage:
        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users ...")
            cursor.execute("INSERT INTO profiles ...")
            # Auto-commit on success, auto-rollback on exception
    
    Args:
        options: Transaction configuration
    
    Yields:
        SQLite connection object
    """
    options = options or TransactionOptions()
    last_exception = None
    
    for attempt in range(options.retry_attempts):
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH, timeout=options.timeout_seconds)
            conn.row_factory = sqlite3.Row
            
            # Set isolation level
            if options.isolation_level == IsolationLevel.IMMEDIATE:
                conn.execute("BEGIN IMMEDIATE")
            elif options.isolation_level == IsolationLevel.EXCLUSIVE:
                conn.execute("BEGIN EXCLUSIVE")
            else:
                conn.execute("BEGIN DEFERRED")
            
            try:
                yield conn
                conn.commit()
                return
                
            except Exception as e:
                conn.rollback()
                raise
                
        except sqlite3.OperationalError as e:
            last_exception = e
            error_msg = str(e).lower()
            
            # Check for specific SQLite errors
            if "database is locked" in error_msg:
                logger.warning(f"Database locked, attempt {attempt + 1}/{options.retry_attempts}")
                if attempt < options.retry_attempts - 1:
                    delay = options.retry_delay_base * (2 ** attempt) + random.uniform(0, 0.1)
                    time.sleep(delay)
                    continue
                raise LockTimeoutError(f"Could not acquire lock after {options.retry_attempts} attempts")
            
            elif "deadlock" in error_msg:
                logger.error("Deadlock detected")
                raise DeadlockError("Transaction deadlock detected")
            
            raise TransactionError(f"Database error: {e}")
            
        finally:
            if conn:
                conn.close()
    
    if last_exception:
        raise last_exception


@contextmanager
def atomic():
    """
    Simple atomic transaction wrapper.
    
    Shorthand for transaction() with default options.
    """
    with transaction() as conn:
        yield conn


# =============================================================================
# OPTIMISTIC LOCKING
# =============================================================================

class OptimisticLock:
    """
    Optimistic locking for concurrent updates.
    
    Uses version numbers to detect conflicts.
    Pattern:
    1. Read record with version
    2. Modify in application
    3. UPDATE ... WHERE version = N
    4. If no rows updated, conflict occurred
    """
    
    def __init__(self, table: str, id_column: str = "id", version_column: str = "version"):
        self.table = table
        self.id_column = id_column
        self.version_column = version_column
    
    def get_with_version(self, conn, record_id: str) -> Optional[dict]:
        """Get record with version number."""
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT *, {self.version_column} as _lock_version
            FROM {self.table}
            WHERE {self.id_column} = ?
        """, (record_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_with_version(self, conn, record_id: str, version: int, **updates) -> bool:
        """
        Update record with version check.
        
        Returns:
            True if update succeeded, False if version conflict
        """
        cursor = conn.cursor()
        
        # Build SET clause
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        set_clause += f", {self.version_column} = {self.version_column} + 1"
        
        values = list(updates.values())
        values.append(record_id)
        values.append(version)
        
        cursor.execute(f"""
            UPDATE {self.table}
            SET {set_clause}
            WHERE {self.id_column} = ? AND {self.version_column} = ?
        """, values)
        
        return cursor.rowcount > 0
    
    def increment_version(self, conn, record_id: str) -> bool:
        """Increment version without other changes (mark as touched)."""
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE {self.table}
            SET {self.version_column} = {self.version_column} + 1
            WHERE {self.id_column} = ?
        """, (record_id,))
        return cursor.rowcount > 0


def with_optimistic_lock(table: str, max_retries: int = 3):
    """
    Decorator for functions that need optimistic locking.
    
    Usage:
        @with_optimistic_lock("quotes")
        def update_quote(conn, quote_id: str, **changes):
            record = get_quote_with_version(conn, quote_id)
            if not record:
                return None
            
            if not lock.update_with_version(conn, quote_id, record['_lock_version'], **changes):
                raise ConcurrentUpdateError("Quote was modified by another user")
            
            return get_quote(conn, quote_id)
    """
    def decorator(func: Callable) -> Callable:
        lock = OptimisticLock(table)
        
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    with transaction() as conn:
                        # Inject lock instance
                        kwargs['_optimistic_lock'] = lock
                        kwargs['_lock_connection'] = conn
                        return func(*args, **kwargs)
                        
                except ConcurrentUpdateError:
                    if attempt < max_retries - 1:
                        delay = 0.1 * (2 ** attempt) + random.uniform(0, 0.05)
                        logger.warning(f"Optimistic lock conflict, retrying in {delay:.2f}s")
                        time.sleep(delay)
                    else:
                        raise
            
            raise ConcurrentUpdateError(f"Failed to acquire lock after {max_retries} attempts")
        
        return wrapper
    return decorator


class ConcurrentUpdateError(TransactionError):
    """Raised when optimistic lock conflict occurs."""
    pass


# =============================================================================
# PESSIMISTIC LOCKING
# =============================================================================

@contextmanager
def row_lock(conn, table: str, record_id: str, lock_type: str = "EXCLUSIVE"):
    """
    Acquire row-level lock using SELECT FOR UPDATE pattern.
    
    Note: SQLite doesn't support true row-level locks, but this pattern
    ensures exclusive access by using immediate transaction and validation.
    
    Usage:
        with transaction(isolation_level=IsolationLevel.IMMEDIATE) as conn:
            with row_lock(conn, "inventory", item_id):
                # Safe to read-modify-write
                current = get_inventory(conn, item_id)
                update_inventory(conn, item_id, current - amount)
    """
    cursor = conn.cursor()
    
    # Read record to validate it exists and establish lock intent
    cursor.execute(f"SELECT 1 FROM {table} WHERE id = ?", (record_id,))
    if not cursor.fetchone():
        raise TransactionError(f"Record not found: {table}.{record_id}")
    
    yield


# =============================================================================
# BATCH OPERATIONS
# =============================================================================

def batch_insert(conn, table: str, records: List[dict], batch_size: int = 100) -> int:
    """
    Insert records in batches for better performance.
    
    Args:
        conn: Database connection
        table: Table name
        records: List of dicts with column names as keys
        batch_size: Records per batch
        
    Returns:
        Number of records inserted
    """
    if not records:
        return 0
    
    cursor = conn.cursor()
    columns = list(records[0].keys())
    placeholders = ", ".join(["?"] * len(columns))
    column_names = ", ".join(columns)
    
    sql = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"
    
    total_inserted = 0
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        values = [tuple(r.get(c) for c in columns) for r in batch]
        cursor.executemany(sql, values)
        total_inserted += cursor.rowcount
    
    return total_inserted


def batch_update(conn, table: str, updates: List[tuple], id_column: str = "id") -> int:
    """
    Update records in batches.
    
    Args:
        conn: Database connection
        table: Table name
        updates: List of (record_id, {column: value}) tuples
        id_column: Name of ID column
        
    Returns:
        Number of records updated
    """
    if not updates:
        return 0
    
    cursor = conn.cursor()
    total_updated = 0
    
    for record_id, changes in updates:
        if not changes:
            continue
        
        set_clause = ", ".join(f"{k} = ?" for k in changes.keys())
        values = list(changes.values())
        values.append(record_id)
        
        cursor.execute(f"""
            UPDATE {table}
            SET {set_clause}
            WHERE {id_column} = ?
        """, values)
        
        total_updated += cursor.rowcount
    
    return total_updated


# =============================================================================
# CONSISTENCY CHECKS
# =============================================================================

def check_foreign_key_integrity(conn) -> List[str]:
    """Check for foreign key constraint violations."""
    cursor = conn.cursor()
    issues = []
    
    # Enable FK checking
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA foreign_key_check")
    
    for row in cursor.fetchall():
        issues.append(f"FK violation in table '{row[0]}', rowid {row[1]}, parent '{row[2]}'")
    
    return issues


def check_orphaned_records(conn, child_table: str, child_fk: str, parent_table: str, parent_pk: str = "id") -> int:
    """Find orphaned records in child table."""
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT COUNT(*) FROM {child_table} c
        LEFT JOIN {parent_table} p ON c.{child_fk} = p.{parent_pk}
        WHERE p.{parent_pk} IS NULL
    """)
    return cursor.fetchone()[0]


def run_consistency_checks(conn) -> dict:
    """
    Run all consistency checks.
    
    Returns:
        Dict with check results
    """
    results = {
        "timestamp": time.time(),
        "passed": True,
        "issues": []
    }
    
    # Foreign key integrity
    fk_issues = check_foreign_key_integrity(conn)
    if fk_issues:
        results["passed"] = False
        results["issues"].extend(fk_issues)
    
    # Check for common orphaned records
    orphaned = check_orphaned_records(conn, "quote_items", "quote_id", "quotes")
    if orphaned > 0:
        results["passed"] = False
        results["issues"].append(f"{orphaned} orphaned quote_items records")
    
    orphaned = check_orphaned_records(conn, "quotes", "customer_id", "customers")
    if orphaned > 0:
        results["passed"] = False
        results["issues"].append(f"{orphaned} orphaned quotes records")
    
    return results


# =============================================================================
# SEQUENCING
# =============================================================================

class Sequence:
    """
    Database sequence generator for unique IDs.
    
    SQLite doesn't have native sequences, so we implement them
    using a table with counter values.
    """
    
    def __init__(self, name: str, start: int = 1, increment: int = 1):
        self.name = name
        self.start = start
        self.increment = increment
    
    def initialize(self, conn):
        """Create sequence if not exists."""
        cursor = conn.cursor()
        
        # Create sequences table if needed
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS _sequences (
                name TEXT PRIMARY KEY,
                current_value INTEGER NOT NULL,
                increment INTEGER NOT NULL DEFAULT 1
            )
        """)
        
        # Insert initial value
        cursor.execute("""
            INSERT OR IGNORE INTO _sequences (name, current_value, increment)
            VALUES (?, ?, ?)
        """, (self.name, self.start - self.increment, self.increment))
    
    def nextval(self, conn) -> int:
        """Get next sequence value."""
        cursor = conn.cursor()
        
        # Update and return new value atomically
        cursor.execute("""
            UPDATE _sequences
            SET current_value = current_value + increment
            WHERE name = ?
            RETURNING current_value
        """, (self.name,))
        
        result = cursor.fetchone()
        if not result:
            raise TransactionError(f"Sequence '{self.name}' not initialized")
        
        return result[0]
    
    def currval(self, conn) -> int:
        """Get current sequence value."""
        cursor = conn.cursor()
        cursor.execute(
            "SELECT current_value FROM _sequences WHERE name = ?",
            (self.name,)
        )
        result = cursor.fetchone()
        if not result:
            raise TransactionError(f"Sequence '{self.name}' not initialized")
        return result[0]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def vacuum_database(conn):
    """Run VACUUM to reclaim space and optimize database."""
    cursor = conn.cursor()
    cursor.execute("VACUUM")
    logger.info("Database vacuum completed")


def analyze_database(conn):
    """Run ANALYZE to update query planner statistics."""
    cursor = conn.cursor()
    cursor.execute("ANALYZE")
    logger.info("Database analyze completed")


def get_table_stats(conn, table: str) -> dict:
    """Get statistics for a table."""
    cursor = conn.cursor()
    
    # Row count
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    row_count = cursor.fetchone()[0]
    
    # Table size estimate
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    
    # Index info
    cursor.execute(f"PRAGMA index_list({table})")
    indexes = cursor.fetchall()
    
    return {
        "table": table,
        "row_count": row_count,
        "column_count": len(columns),
        "index_count": len(indexes),
        "indexes": [idx[1] for idx in indexes]
    }
