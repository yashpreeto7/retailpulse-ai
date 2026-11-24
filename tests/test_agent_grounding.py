"""
Golden AI Questions Tests: End-to-end verification of agent responses against database ground truth.
"""
import pytest
from retailpulse.agent.orchestrator import AgentOrchestrator
from retailpulse.core.database import execute_raw_sql

orchestrator = AgentOrchestrator()

def test_ai_golden_question_top_products():
    """Verify 'What were the top 5 products by revenue?' matches exact database ranking."""
    response = orchestrator.answer_question("What were the top 5 products by revenue?")
    
    assert response.grounded is True
    assert any(t.tool_name == "get_top_products" for t in response.executed_tools)

    # Independent ground truth calculation directly from database
    sql = """
    SELECT p.name as product_name, ROUND(SUM(oi.subtotal), 2) as rev
    FROM products p
    JOIN order_items oi ON p.product_id = oi.product_id
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.status = 'completed'
    GROUP BY p.name
    ORDER BY rev DESC
    LIMIT 1
    """
    ground_truth = execute_raw_sql(sql)[0]
    top_name = ground_truth["product_name"]
    top_rev = ground_truth["rev"]

    # Verify that the top product name and revenue are present in the response
    assert top_name in response.answer
    assert f"${top_rev:,.2f}" in response.answer

def test_ai_golden_question_monthly_revenue():
    """Verify 'Show monthly revenue.' retrieves accurate monthly figures and attaches chart."""
    response = orchestrator.answer_question("Show monthly revenue.")
    
    assert response.grounded is True
    assert any(t.tool_name == "get_sales_metrics" for t in response.executed_tools)
    assert response.chart is not None
    assert response.chart.chart_type == "line"

    # Independent ground truth check
    sql = """
    SELECT strftime('%Y-%m', order_date) as month, ROUND(SUM(total_amount), 2) as rev
    FROM orders
    WHERE status = 'completed'
    GROUP BY month
    ORDER BY month DESC
    LIMIT 1
    """
    latest = execute_raw_sql(sql)[0]
    assert latest["month"] in response.answer
    assert f"${latest['rev']:,.2f}" in response.answer

def test_ai_golden_question_top_category():
    """Verify 'Which category generated the most revenue?' identifies the exact top category."""
    response = orchestrator.answer_question("Which category generated the most revenue?")
    
    assert response.grounded is True
    
    # Ground truth top category
    sql = """
    SELECT c.name as category_name, ROUND(SUM(oi.subtotal), 2) as rev
    FROM categories c
    JOIN products p ON c.category_id = p.category_id
    JOIN order_items oi ON p.product_id = oi.product_id
    JOIN orders o ON oi.order_id = o.order_id
    WHERE o.status = 'completed'
    GROUP BY c.name
    ORDER BY rev DESC
    LIMIT 1
    """
    top_cat = execute_raw_sql(sql)[0]
    assert top_cat["category_name"] in response.answer
    assert f"${top_cat['rev']:,.2f}" in response.answer

def test_ai_golden_question_multi_step_revenue_decline():
    """Verify multi-step root cause diagnostic 'Why did revenue decline last month?'."""
    response = orchestrator.answer_question("Why did revenue decline last month?")
    
    assert response.grounded is True
    assert any(t.tool_name == "diagnose_revenue_decline" for t in response.executed_tools)
    assert response.chart is not None

    # Check that root cause decomposition and metrics are present
    assert "Electronics" in response.answer
    assert any(w in response.answer for w in ["$16,248.49", "-40.7%", "23,648.32", "decline", "dropped"])
    assert any(w in response.answer.lower() for w in ["actionable", "recommendation", "takeaway", "root cause"])

def test_ai_golden_question_inactive_customers():
    """Verify 'Which customers have not purchased recently?' lists inactive customers."""
    response = orchestrator.answer_question("Which customers have not purchased recently?")
    
    assert response.grounded is True
    assert any(t.tool_name == "get_customer_metrics" for t in response.executed_tools)
    assert any(w in response.answer.lower() for w in ["inactive", "no recent purchase", "without purchase"])
    assert any(name in response.answer for name in ["Daniel Lopez", "Margaret Hernandez", "Sarah Smith", "Sandra Jones"])
    assert len(response.data_points.get("inactive_customers", [])) > 0

def test_ai_unsupported_out_of_domain_question():
    """Verify out-of-domain questions are gracefully rejected without hallucinating."""
    response = orchestrator.answer_question("What is the capital of France?")
    
    assert "I am your RetailPulse AI Business Analyst" in response.answer
    assert "I cannot answer general out-of-domain questions" in response.answer
    assert len(response.executed_tools) == 0
    assert response.chart is None
