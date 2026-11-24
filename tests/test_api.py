"""
Tests for FastAPI REST Endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from retailpulse.api.app import app

client = TestClient(app)

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "counts" in data
    assert data["counts"]["orders"] > 0

def test_api_kpis():
    res = client.get("/api/kpis")
    assert res.status_code == 200
    data = res.json()
    assert data["total_revenue"] > 0
    assert data["completed_orders"] > 0
    assert data["average_order_value"] > 0

def test_api_monthly_sales():
    res = client.get("/api/sales/monthly")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert "revenue" in data[0]

def test_api_top_products():
    res = client.get("/api/products/top?metric=revenue&limit=3")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 3
    assert data[0]["revenue"] >= data[1]["revenue"]

def test_api_charts():
    res = client.get("/api/charts/monthly-revenue")
    assert res.status_code == 200
    data = res.json()
    assert data["chart_type"] == "line"
    assert len(data["labels"]) > 0

def test_api_chat_endpoint():
    res = client.post("/api/chat", json={"question": "What were the top 5 products by revenue?"})
    assert res.status_code == 200
    data = res.json()
    assert data["grounded"] is True
    assert len(data["executed_tools"]) > 0
    assert "answer" in data

def test_api_sql_security():
    # Valid SELECT query
    res = client.post("/api/query/sql", json={"sql": "SELECT name, price FROM products LIMIT 2"})
    assert res.status_code == 200
    assert res.json()["row_count"] == 2

    # Malicious DROP query should be blocked with 403 Forbidden
    res_bad = client.post("/api/query/sql", json={"sql": "DROP TABLE customers"})
    assert res_bad.status_code == 403
    assert "Forbidden SQL" in res_bad.json()["detail"]

def test_api_data_quality():
    res = client.get("/api/data-quality")
    assert res.status_code == 200
    data = res.json()
    assert data["records_loaded"] > 0
    assert data["clean_pct"] >= 95.0
