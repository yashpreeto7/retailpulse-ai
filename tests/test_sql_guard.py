"""
Tests for Safe SQL Execution and Security Guardrails.
"""
import pytest
from retailpulse.agent.sql_guard import SQLGuard, SQLSecurityException

def test_safe_select_queries_pass():
    query1 = "SELECT count(*) FROM products"
    sanitized1 = SQLGuard.validate_and_sanitize(query1)
    assert sanitized1.startswith("SELECT")
    assert "LIMIT 50" in sanitized1

    query2 = "SELECT product_name, price FROM products LIMIT 5"
    sanitized2 = SQLGuard.validate_and_sanitize(query2)
    assert "LIMIT 5" in sanitized2

    rows = SQLGuard.execute_safe_query("SELECT count(*) as cnt FROM products")
    assert len(rows) == 1
    assert rows[0]["cnt"] > 0

def test_malicious_sql_rejections():
    # DROP statement
    with pytest.raises(SQLSecurityException):
        SQLGuard.validate_and_sanitize("DROP TABLE customers")

    # DELETE statement
    with pytest.raises(SQLSecurityException):
        SQLGuard.validate_and_sanitize("DELETE FROM orders WHERE id = 1")

    # INSERT statement
    with pytest.raises(SQLSecurityException):
        SQLGuard.validate_and_sanitize("INSERT INTO products (name) VALUES ('Hacked')")

    # UPDATE statement
    with pytest.raises(SQLSecurityException):
        SQLGuard.validate_and_sanitize("UPDATE customers SET email = 'bad'")

    # Multi-statement injection attempt
    with pytest.raises(SQLSecurityException):
        SQLGuard.validate_and_sanitize("SELECT * FROM products; DROP TABLE customers")

    # SQL comment injection
    with pytest.raises(SQLSecurityException):
        SQLGuard.validate_and_sanitize("SELECT * FROM products -- comment")
