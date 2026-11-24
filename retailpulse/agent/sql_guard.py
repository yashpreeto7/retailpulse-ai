"""
SQL Safety Guard: Enforces strict read-only execution, prevents SQL injection and DDL/DML.
"""
import re
from typing import Any
from retailpulse.core.database import execute_raw_sql
from retailpulse.core.logger import get_logger

logger = get_logger("retailpulse.sql_guard")

FORBIDDEN_KEYWORDS = [
    r"\bDROP\b", r"\bDELETE\b", r"\bUPDATE\b", r"\bINSERT\b",
    r"\bALTER\b", r"\bTRUNCATE\b", r"\bCREATE\b", r"\bATTACH\b",
    r"\bDETACH\b", r"\bPRAGMA\b", r"\bGRANT\b", r"\bREVOKE\b",
    r"\bREPLACE\b", r"\bUPSERT\b", r"\bEXEC\b", r"\bEXECUTE\b",
    r"--", r";.*"
]

class SQLSecurityException(Exception):
    """Raised when an unsafe or malicious SQL query is detected."""
    pass

class SQLGuard:
    @classmethod
    def validate_and_sanitize(cls, sql: str) -> str:
        """
        Validates that SQL is purely a safe SELECT statement:
        1. Must start with SELECT or WITH
        2. Must not contain DDL/DML mutations or comments
        3. Appends LIMIT if missing to prevent unbounded queries
        """
        cleaned_sql = sql.strip()
        
        # Strip trailing semicolon
        if cleaned_sql.endswith(";"):
            cleaned_sql = cleaned_sql[:-1].strip()

        # Check for multiple statements
        if ";" in cleaned_sql:
            raise SQLSecurityException("Multi-statement SQL queries are strictly forbidden.")

        # Check for forbidden keywords (case-insensitive)
        for pattern in FORBIDDEN_KEYWORDS:
            if re.search(pattern, cleaned_sql, re.IGNORECASE):
                raise SQLSecurityException(f"Forbidden SQL operation detected matching: {pattern}")

        # Ensure query begins with SELECT or WITH
        normalized = cleaned_sql.lstrip().upper()
        if not (normalized.startswith("SELECT") or normalized.startswith("WITH")):
            raise SQLSecurityException("Only read-only SELECT or WITH statements are allowed.")

        # Ensure reasonable LIMIT clause
        if not re.search(r"\bLIMIT\s+\d+", cleaned_sql, re.IGNORECASE):
            cleaned_sql = f"{cleaned_sql} LIMIT 50"

        return cleaned_sql

    @classmethod
    def execute_safe_query(cls, sql: str) -> list[dict[str, Any]]:
        """Validates and executes a read-only SQL query."""
        safe_sql = cls.validate_and_sanitize(sql)
        logger.info(f"Executing sanitized safe SQL: {safe_sql}")
        return execute_raw_sql(safe_sql)
