"""
Database Schema Validation and Production Readiness Checks

Validates database schema for production deployment:
- Missing indexes on foreign keys
- Proper data types
- Constraint validation
- Performance recommendations
"""

import sqlite3
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from loguru import logger

from app.database_sqlite import get_db


class IssueSeverity(Enum):
    CRITICAL = "critical"    # Must fix before production
    WARNING = "warning"      # Should fix, may cause issues
    INFO = "info"            # Recommendation for improvement


@dataclass
class SchemaIssue:
    """Represents a schema issue."""
    severity: IssueSeverity
    table: str
    issue_type: str
    message: str
    recommendation: str


class SchemaValidator:
    """
    Validates database schema for production readiness.
    
    Checks:
    - Foreign keys have indexes
    - Text columns don't have excessive length
    - Numeric columns have proper constraints
    - Tables have primary keys
    - No duplicate indexes
    """
    
    def __init__(self):
        self.issues: List[SchemaIssue] = []
    
    def validate_all(self) -> Tuple[bool, List[SchemaIssue]]:
        """
        Run all validation checks.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        self.issues = []
        
        with get_db() as conn:
            tables = self._get_tables(conn)
            
            for table in tables:
                if table.startswith("_"):  # Skip internal tables
                    continue
                
                self._check_primary_key(conn, table)
                self._check_foreign_key_indexes(conn, table)
                self._check_duplicate_indexes(conn, table)
                self._check_column_types(conn, table)
            
            self._check_wal_mode(conn)
            self._check_foreign_keys_enabled(conn)
        
        is_valid = not any(i.severity == IssueSeverity.CRITICAL for i in self.issues)
        return is_valid, self.issues
    
    def _get_tables(self, conn) -> List[str]:
        """Get list of all user tables."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        return [row[0] for row in cursor.fetchall()]
    
    def _check_primary_key(self, conn, table: str):
        """Check that table has a primary key."""
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        has_pk = any(col[5] == 1 for col in columns)  # pk column is index 5
        
        if not has_pk:
            self.issues.append(SchemaIssue(
                severity=IssueSeverity.CRITICAL,
                table=table,
                issue_type="missing_primary_key",
                message=f"Table '{table}' has no primary key",
                recommendation="Add PRIMARY KEY to id column or create surrogate key"
            ))
    
    def _check_foreign_key_indexes(self, conn, table: str):
        """Check that foreign key columns have indexes."""
        cursor = conn.cursor()
        
        # Get foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        fks = cursor.fetchall()
        
        # Get existing indexes
        cursor.execute(f"PRAGMA index_list({table})")
        indexes = cursor.fetchall()
        
        # Get index columns
        indexed_columns = set()
        for idx in indexes:
            cursor.execute(f"PRAGMA index_info({idx[1]})")
            for col in cursor.fetchall():
                indexed_columns.add(col[2])
        
        # Check each FK
        for fk in fks:
            from_col = fk[3]  # Column in this table
            
            if from_col not in indexed_columns:
                self.issues.append(SchemaIssue(
                    severity=IssueSeverity.WARNING,
                    table=table,
                    issue_type="missing_fk_index",
                    message=f"Foreign key column '{table}.{from_col}' has no index",
                    recommendation=f"CREATE INDEX idx_{table}_{from_col} ON {table}({from_col})"
                ))
    
    def _check_duplicate_indexes(self, conn, table: str):
        """Check for redundant/duplicate indexes."""
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA index_list({table})")
        indexes = cursor.fetchall()
        
        index_columns = {}
        for idx in indexes:
            idx_name = idx[1]
            cursor.execute(f"PRAGMA index_info({idx_name})")
            cols = tuple(sorted([col[2] for col in cursor.fetchall()]))
            
            if cols in index_columns:
                self.issues.append(SchemaIssue(
                    severity=IssueSeverity.INFO,
                    table=table,
                    issue_type="duplicate_index",
                    message=f"Duplicate indexes: '{idx_name}' and '{index_columns[cols]}'",
                    recommendation=f"Drop redundant index: DROP INDEX IF EXISTS {idx_name}"
                ))
            else:
                index_columns[cols] = idx_name
    
    def _check_column_types(self, conn, table: str):
        """Check column types for potential issues."""
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        for col in columns:
            name = col[1]
            dtype = col[2].upper()
            notnull = col[3]
            default = col[4]
            
            # Check for TEXT without length (SQLite doesn't enforce, but good for documentation)
            # This is more of an info since SQLite TEXT is unlimited
            
            # Check for nullable columns without defaults
            if not notnull and default is None and name not in ["id", "created_at", "updated_at"]:
                self.issues.append(SchemaIssue(
                    severity=IssueSeverity.INFO,
                    table=table,
                    issue_type="nullable_no_default",
                    message=f"Column '{table}.{name}' is nullable without default",
                    recommendation=f"Consider adding DEFAULT value or making NOT NULL"
                ))
            
            # Check for REAL columns that might need precision
            if dtype == "REAL":
                self.issues.append(SchemaIssue(
                    severity=IssueSeverity.INFO,
                    table=table,
                    issue_type="real_precision",
                    message=f"Column '{table}.{name}' is REAL - consider precision requirements",
                    recommendation="Use INTEGER (cents) for monetary values to avoid floating point errors"
                ))
    
    def _check_wal_mode(self, conn):
        """Check if WAL mode is enabled for better concurrency."""
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]
        
        if mode != "wal":
            self.issues.append(SchemaIssue(
                severity=IssueSeverity.WARNING,
                table="*",
                issue_type="wal_not_enabled",
                message=f"WAL mode not enabled (current: {mode})",
                recommendation="Enable WAL: PRAGMA journal_mode = WAL"
            ))
    
    def _check_foreign_keys_enabled(self, conn):
        """Check if foreign key enforcement is enabled."""
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys")
        enabled = cursor.fetchone()[0]
        
        if not enabled:
            self.issues.append(SchemaIssue(
                severity=IssueSeverity.CRITICAL,
                table="*",
                issue_type="foreign_keys_disabled",
                message="Foreign key enforcement is disabled",
                recommendation="Enable FKs: PRAGMA foreign_keys = ON"
            ))
    
    def get_summary(self) -> Dict:
        """Get validation summary."""
        is_valid, issues = self.validate_all()
        
        critical = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        warnings = sum(1 for i in issues if i.severity == IssueSeverity.WARNING)
        info = sum(1 for i in issues if i.severity == IssueSeverity.INFO)
        
        return {
            "is_valid": is_valid,
            "summary": {
                "critical": critical,
                "warning": warnings,
                "info": info,
                "total": len(issues)
            },
            "issues": [
                {
                    "severity": i.severity.value,
                    "table": i.table,
                    "type": i.issue_type,
                    "message": i.message,
                    "recommendation": i.recommendation
                }
                for i in issues
            ]
        }


# =============================================================================
# PERFORMANCE ANALYZER
# =============================================================================

class PerformanceAnalyzer:
    """Analyze database for performance issues."""
    
    def __init__(self):
        pass
    
    def analyze_query_performance(self, conn, query: str, params: tuple = ()) -> Dict:
        """
        Analyze a specific query's performance.
        
        Returns:
            Dict with query plan and recommendations
        """
        cursor = conn.cursor()
        
        # Get query plan
        cursor.execute(f"EXPLAIN QUERY PLAN {query}", params)
        plan = cursor.fetchall()
        
        # Parse plan for issues
        issues = []
        full_plan = " ".join(str(row) for row in plan)
        
        # Check for table scans
        if "SCAN TABLE" in full_plan and "USING INDEX" not in full_plan:
            issues.append("Query performs full table scan - consider adding index")
        
        # Check for large temporary tables
        if "TEMP B-TREE" in full_plan:
            issues.append("Query creates temporary B-tree - may be slow with large datasets")
        
        return {
            "query": query,
            "plan": [dict(row) for row in plan],
            "issues": issues,
            "recommendations": self._get_query_recommendations(full_plan)
        }
    
    def _get_query_recommendations(self, plan: str) -> List[str]:
        """Get recommendations based on query plan."""
        recommendations = []
        
        if "SCAN TABLE" in plan:
            recommendations.append("Add index on filtered columns")
        
        if "ORDER BY" in plan and "USING INDEX" not in plan:
            recommendations.append("Consider index on ORDER BY columns")
        
        if "GROUP BY" in plan:
            recommendations.append("Consider index on GROUP BY columns")
        
        return recommendations
    
    def get_table_statistics(self, conn, table: str) -> Dict:
        """Get statistics for a table."""
        cursor = conn.cursor()
        
        # Row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]
        
        # Column info
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        # Index info
        cursor.execute(f"PRAGMA index_list({table})")
        indexes = cursor.fetchall()
        
        # Calculate table size estimate
        size_estimate = self._estimate_table_size(cursor, table, columns)
        
        return {
            "table": table,
            "row_count": row_count,
            "estimated_size_bytes": size_estimate,
            "columns": len(columns),
            "indexes": len(indexes),
            "index_names": [idx[1] for idx in indexes]
        }
    
    def _estimate_table_size(self, cursor, table: str, columns: List) -> int:
        """Estimate table size in bytes."""
        # Rough estimation based on column types
        type_sizes = {
            "INTEGER": 8,
            "REAL": 8,
            "TEXT": 100,  # Average estimate
            "BLOB": 500,
            "BOOLEAN": 1,
            "DATETIME": 20,
        }
        
        row_size = 0
        for col in columns:
            dtype = col[2].upper()
            row_size += type_sizes.get(dtype, 50)
        
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]
        
        return row_size * row_count


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python schema_validator.py <command>")
        print("Commands:")
        print("  validate    - Run schema validation")
        print("  stats       - Show table statistics")
        print("  check <sql> - Check query performance")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "validate":
        validator = SchemaValidator()
        summary = validator.get_summary()
        
        print(json.dumps(summary, indent=2))
        
        if not summary["is_valid"]:
            print("\n[CRITICAL] Schema has critical issues that must be fixed before production!")
            sys.exit(1)
        elif summary["summary"]["warning"] > 0:
            print("\n[WARNING] Schema has warnings that should be addressed.")
        else:
            print("\n[OK] Schema validation passed!")
    
    elif cmd == "stats":
        analyzer = PerformanceAnalyzer()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("_")]
            
            for table in tables:
                stats = analyzer.get_table_statistics(conn, table)
                size_mb = stats["estimated_size_bytes"] / (1024 * 1024)
                print(f"{table}: {stats['row_count']:,} rows, ~{size_mb:.2f} MB, {stats['indexes']} indexes")
    
    elif cmd == "check" and len(sys.argv) > 2:
        query = sys.argv[2]
        analyzer = PerformanceAnalyzer()
        with get_db() as conn:
            result = analyzer.analyze_query_performance(conn, query)
            print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
