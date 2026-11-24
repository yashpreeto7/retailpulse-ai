"""
Tests for Elevated System Capabilities:
1. Predictive Sales Forecasting with Confidence Bounds
2. Multi-Turn Conversational Memory & Context Resolution
3. CSV Data Export Endpoints
4. Live HTTP Server Verification
"""
import pytest
import httpx
from retailpulse.analytics.forecasting import ForecastingEngine
from retailpulse.agent.orchestrator import AgentOrchestrator

def test_predictive_sales_forecasting():
    res = ForecastingEngine.forecast_sales(horizon_months=3)
    assert res["horizon_months"] == 3
    assert len(res["forecast"]) == 3
    assert "chart" in res
    assert res["chart"]["chart_type"] == "line"

    for item in res["forecast"]:
        assert item["projected_revenue"] > 0
        assert item["lower_bound_95"] <= item["projected_revenue"]
        assert item["upper_bound_95"] >= item["projected_revenue"]
        assert item["lower_bound_95"] < item["upper_bound_95"]

def test_multi_turn_conversational_memory():
    orch = AgentOrchestrator()
    session_id = "test_turn_session_1"

    # Turn 1: Ask top products
    r1 = orch.answer_question("What were the top 5 products by revenue?", session_id=session_id)
    assert r1.grounded is True
    assert "products" in r1.data_points
    assert len(r1.data_points["products"]) == 5

    # Turn 2: Contextual follow-up ("Which of those belongs to Electronics?")
    r2 = orch.answer_question("Which of those belongs to Electronics?", session_id=session_id)
    assert r2.grounded is True
    assert "Electronics" in r2.answer
    assert "previous analysis" in r2.answer

    # Turn 3: Contextual follow-up ("Who is the top one?")
    r3 = orch.answer_question("Who is the top one?", session_id=session_id)
    assert r3.grounded is True
    top_sku_name = r1.data_points["products"][0]["product_name"]
    assert top_sku_name in r3.answer

def test_live_server_endpoints():
    client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=60.0)

    # 1. Health check
    h = client.get("/api/health")
    assert h.status_code == 200
    assert h.json()["status"] == "healthy"

    # 2. Predictive forecast endpoint
    fc = client.get("/api/forecast?horizon=3")
    assert fc.status_code == 200
    assert len(fc.json()["forecast"]) == 3

    # 3. Export Sales CSV
    exp_sales = client.get("/api/export/sales")
    assert exp_sales.status_code == 200
    assert exp_sales.headers["content-type"].startswith("text/csv")
    assert "Month,Revenue_USD" in exp_sales.text

    # 4. Export Products CSV
    exp_prod = client.get("/api/export/products")
    assert exp_prod.status_code == 200
    assert exp_prod.headers["content-type"].startswith("text/csv")
    assert "Product_ID,Name" in exp_prod.text

    # 5. Natural Language Forecasting Query over HTTP
    chat_resp = client.post("/api/chat", json={"question": "Forecast revenue for the next 3 months."})
    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert any(w in data["answer"] for w in ["Predictive Revenue Forecast", "Forecast Revenue", "Forecast", "forecast"])
    assert data["chart"] is not None
    assert data["chart"]["chart_type"] == "line"
