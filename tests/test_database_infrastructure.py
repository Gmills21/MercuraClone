#!/usr/bin/env python3
"""
Database Production Infrastructure Tests

Tests migrations, transactions, schema validation, and race condition handling.
"""

import asyncio
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.migrations import MigrationManager, Migration
from app.utils.transactions import (
    transaction, atomic, TransactionOptions, IsolationLevel,
    OptimisticLock, ConcurrentUpdateError,
    batch_insert, batch_update,
    run_consistency_checks, Sequence
)
from app.utils.schema_validator import SchemaValidator, IssueSeverity

results = []


def test_section(name):
    print(f"\n{'=' * 70}")
    print(f"  {name}")
    print(f"{'=' * 70}")


def test_pass(name):
    results.append(("PASS", name))
    print(f"  [PASS] {name}")


def test_fail(name, error):
    results.append(("FAIL", name, str(error)))
    print(f"  [FAIL] {name}: {error}")


# =============================================================================
# TEST 1: Migration System
# =============================================================================

def test_migrations():
    """Test migration system."""
    test_section("TEST 1: Migration System")
    
    # Test 1a: Migration manager initialization
    try:
        manager = MigrationManager(migrations_dir="test_migrations")
        version = manager.get_current_version()
        assert isinstance(version, int)
        test_pass("Migration manager initialization")
    except Exception as e:
        test_fail("Migration manager initialization", e)
        return  # Can't continue without migrations
    
    # Test 1b: Create migration
    try:
        version = manager.create_migration(
            name="test_migration",
            description="Test migration",
            up_sql="CREATE TABLE IF NOT EXISTS test_table (id TEXT PRIMARY KEY)",
            down_sql="DROP TABLE IF EXISTS test_table"
        )
        assert version > 0
        test_pass("Create migration file")
    except Exception as e:
        test_fail("Create migration file", e)
    
    # Test 1c: Load migrations
    try:
        migrations = manager.load_migrations()
        assert len(migrations) > 0
        assert migrations[0].version == version
        test_pass("Load migrations from disk")
    except Exception as e:
        test_fail("Load migrations from disk", e)
    
    # Test 1d: Apply migration
    try:
        success = manager.migrate()
        assert success
        new_version = manager.get_current_version()
        assert new_version >= version
        test_pass("Apply migrations")
    except Exception as e:
        test_fail("Apply migrations", e)
    
    # Test 1e: Migration history
    try:
        history = manager.get_migration_history()
        assert len(history) > 0
        assert history[0]["version"] == version
        test_pass("Migration history tracking")
    except Exception as e:
        test_fail("Migration history tracking", e)
    
    # Cleanup
    import shutil
    shutil.rmtree("test_migrations", ignore_errors=True)


# =============================================================================
# TEST 2: Transactions
# =============================================================================

def test_transactions():
    """Test transaction handling."""
    test_section("TEST 2: Transactions")
    
    # Test 2a: Basic transaction commit
    try:
        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS tx_test (id TEXT PRIMARY KEY, value INTEGER)")
            cursor.execute("INSERT OR REPLACE INTO tx_test VALUES ('test1', 100)")
        
        # Verify data persisted
        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM tx_test WHERE id = 'test1'")
            result = cursor.fetchone()
            assert result[0] == 100
        
        test_pass("Transaction commit persists data")
    except Exception as e:
        test_fail("Transaction commit", e)
    
    # Test 2b: Transaction rollback on error
    try:
        try:
            with transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO tx_test VALUES ('test2', 200)")
                raise ValueError("Intentional error")
        except ValueError:
            pass  # Expected
        
        # Verify data was NOT persisted
        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM tx_test WHERE id = 'test2'")
            result = cursor.fetchone()
            assert result is None, "Data should have been rolled back"
        
        test_pass("Transaction rollback on error")
    except Exception as e:
        test_fail("Transaction rollback", e)
    
    # Test 2c: Atomic helper
    try:
        with atomic() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO tx_test VALUES ('test3', 300)")
        
        with atomic() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM tx_test WHERE id = 'test3'")
            assert cursor.fetchone()[0] == 300
        
        test_pass("Atomic context manager")
    except Exception as e:
        test_fail("Atomic context manager", e)
    
    # Cleanup
    try:
        with transaction() as conn:
            conn.cursor().execute("DROP TABLE IF EXISTS tx_test")
    except:
        pass


# =============================================================================
# TEST 3: Optimistic Locking
# =============================================================================

def test_optimistic_locking():
    """Test optimistic locking for race condition prevention."""
    test_section("TEST 3: Optimistic Locking")
    
    # Setup
    try:
        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lock_test (
                    id TEXT PRIMARY KEY,
                    data TEXT,
                    version INTEGER DEFAULT 0
                )
            """)
            cursor.execute("INSERT OR REPLACE INTO lock_test VALUES ('record1', 'initial', 0)")
        
        # Test 3a: Get with version
        lock = OptimisticLock("lock_test")
        
        with transaction() as conn:
            record = lock.get_with_version(conn, "record1")
            assert record["data"] == "initial"
            assert record["_lock_version"] == 0
        
        test_pass("Get record with version")
    except Exception as e:
        test_fail("Get record with version", e)
        return
    
    # Test 3b: Update with version
    try:
        with transaction() as conn:
            record = lock.get_with_version(conn, "record1")
            success = lock.update_with_version(
                conn, "record1", record["_lock_version"],
                data="updated"
            )
            assert success
        
        # Verify update
        with transaction() as conn:
            record = lock.get_with_version(conn, "record1")
            assert record["data"] == "updated"
            assert record["_lock_version"] == 1
        
        test_pass("Update with version check")
    except Exception as e:
        test_fail("Update with version check", e)
    
    # Test 3c: Version conflict
    try:
        # Try to update with stale version
        with transaction() as conn:
            success = lock.update_with_version(conn, "record1", 0, data="should_fail")
            assert not success, "Update should have failed due to version mismatch"
        
        test_pass("Version conflict detected")
    except Exception as e:
        test_fail("Version conflict detection", e)
    
    # Cleanup
    try:
        with transaction() as conn:
            conn.cursor().execute("DROP TABLE IF EXISTS lock_test")
    except:
        pass


# =============================================================================
# TEST 4: Batch Operations
# =============================================================================

def test_batch_operations():
    """Test batch insert and update."""
    test_section("TEST 4: Batch Operations")
    
    # Setup
    try:
        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS batch_test (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    value INTEGER
                )
            """)
        
        # Test 4a: Batch insert
        records = [
            {"id": f"batch_{i}", "name": f"Item {i}", "value": i * 10}
            for i in range(100)
        ]
        
        with transaction() as conn:
            count = batch_insert(conn, "batch_test", records, batch_size=25)
            assert count == 100
        
        # Verify
        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM batch_test")
            assert cursor.fetchone()[0] == 100
        
        test_pass("Batch insert 100 records")
    except Exception as e:
        test_fail("Batch insert", e)
        return
    
    # Test 4b: Batch update
    try:
        updates = [
            (f"batch_{i}", {"value": i * 100})
            for i in range(50)
        ]
        
        with transaction() as conn:
            count = batch_update(conn, "batch_test", updates)
            assert count == 50
        
        # Verify
        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM batch_test WHERE id = 'batch_10'")
            assert cursor.fetchone()[0] == 1000  # 10 * 100
        
        test_pass("Batch update 50 records")
    except Exception as e:
        test_fail("Batch update", e)
    
    # Cleanup
    try:
        with transaction() as conn:
            conn.cursor().execute("DROP TABLE IF EXISTS batch_test")
    except:
        pass


# =============================================================================
# TEST 5: Consistency Checks
# =============================================================================

def test_consistency_checks():
    """Test database consistency validation."""
    test_section("TEST 5: Consistency Checks")
    
    try:
        with transaction() as conn:
            results = run_consistency_checks(conn)
        
        assert "timestamp" in results
        assert "passed" in results
        assert "issues" in results
        
        test_pass("Consistency checks run successfully")
    except Exception as e:
        test_fail("Consistency checks", e)


# =============================================================================
# TEST 6: Schema Validation
# =============================================================================

def test_schema_validation():
    """Test schema validation."""
    test_section("TEST 6: Schema Validation")
    
    try:
        validator = SchemaValidator()
        is_valid, issues = validator.validate_all()
        
        # Just verify it runs without errors
        assert isinstance(is_valid, bool)
        assert isinstance(issues, list)
        
        test_pass("Schema validation runs")
    except Exception as e:
        test_fail("Schema validation", e)
    
    # Test summary generation
    try:
        validator = SchemaValidator()
        summary = validator.get_summary()
        
        assert "is_valid" in summary
        assert "summary" in summary
        assert "issues" in summary
        assert "critical" in summary["summary"]
        
        test_pass("Schema validation summary")
    except Exception as e:
        test_fail("Schema validation summary", e)


# =============================================================================
# TEST 7: Sequences
# =============================================================================

def test_sequences():
    """Test sequence generator."""
    test_section("TEST 7: Sequences")
    
    # Test 7a: Initialize sequence
    try:
        seq = Sequence("test_seq", start=1)
        
        with transaction() as conn:
            seq.initialize(conn)
        
        test_pass("Initialize sequence")
    except Exception as e:
        test_fail("Initialize sequence", e)
        return
    
    # Test 7b: Get next values
    try:
        with transaction() as conn:
            val1 = seq.nextval(conn)
            val2 = seq.nextval(conn)
            val3 = seq.nextval(conn)
        
        assert val2 == val1 + 1
        assert val3 == val2 + 1
        
        test_pass("Sequence increment")
    except Exception as e:
        test_fail("Sequence increment", e)
    
    # Test 7c: Current value
    try:
        with transaction() as conn:
            current = seq.currval(conn)
        
        assert current == val3
        
        test_pass("Get current sequence value")
    except Exception as e:
        test_fail("Get current sequence value", e)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("\n" + "=" * 70)
    print("  DATABASE PRODUCTION INFRASTRUCTURE TESTS")
    print("  Testing migrations, transactions, locking, and schema validation")
    print("=" * 70)
    
    test_migrations()
    test_transactions()
    test_optimistic_locking()
    test_batch_operations()
    test_consistency_checks()
    test_schema_validation()
    test_sequences()
    
    # Summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for r in results if r[0] == "PASS")
    failed = sum(1 for r in results if r[0] == "FAIL")
    
    print(f"\n  Total: {len(results)} tests")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    
    if failed > 0:
        print("\n  Failed tests:")
        for r in results:
            if r[0] == "FAIL":
                print(f"    - {r[1]}: {r[2]}")
    
    print("\n" + "=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
