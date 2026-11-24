"""
Controlled Tool/Function Layer for the AI Business Analyst.
All tools have strict input validation, execute on the real dataset, and return structured dictionaries.
"""
import time
from typing import Any, Literal
from retailpulse.analytics.sales import SalesAnalytics
from retailpulse.analytics.customers import CustomerAnalytics
from retailpulse.analytics.products import ProductAnalytics
from retailpulse.analytics.root_cause import RootCauseDiagnostic
from retailpulse.agent.sql_guard import SQLGuard
from retailpulse.models.schemas import ChartSpec, ToolExecutionTrace
from retailpulse.core.logger import get_logger

logger = get_logger("retailpulse.tools")

def get_kpi_summary() -> dict[str, Any]:
    """Retrieve executive KPI summary: Total Revenue, Total Orders, Average Order Value (AOV), and Customer counts."""
    kpi = SalesAnalytics.get_kpi_summary()
    return kpi.model_dump()

def get_sales_metrics(metric_type: Literal["monthly", "category"] = "monthly") -> dict[str, Any]:
    """Retrieve aggregated sales performance metrics over time (monthly) or by category."""
    if metric_type == "category":
        items = SalesAnalytics.get_revenue_by_category()
        return {"metric_type": "category", "data": [item.model_dump() for item in items]}
    else:
        items = SalesAnalytics.get_monthly_revenue()
        return {"metric_type": "monthly", "data": [item.model_dump() for item in items]}

def get_top_products(metric: Literal["revenue", "volume", "low_performing"] = "revenue", limit: int = 5) -> dict[str, Any]:
    """Retrieve ranked product analytics by gross revenue, volume of units sold, or low-performing inventory."""
    if metric == "volume":
        items = ProductAnalytics.get_top_products_by_volume(limit=limit)
    elif metric == "low_performing":
        items = ProductAnalytics.get_low_performing_products(limit=limit)
    else:
        items = ProductAnalytics.get_top_products_by_revenue(limit=limit)
    return {"metric": metric, "limit": limit, "products": [p.model_dump() for p in items]}

def get_customer_metrics(segment: Literal["summary", "inactive", "top_spenders"] = "summary", limit: int = 10) -> dict[str, Any]:
    """Retrieve customer analytics: overview cohorts, inactive/churned customers, or top customers by lifetime spend."""
    if segment == "inactive":
        customers = CustomerAnalytics.get_inactive_customers(days_inactive=90, limit=limit)
        return {"segment": "inactive", "days_threshold": 90, "customers": customers}
    else:
        summary = CustomerAnalytics.get_customer_summary(top_n=limit)
        return {"segment": "summary", "data": summary.model_dump()}

def diagnose_revenue_decline(target_month: str | None = None, baseline_month: str | None = None) -> dict[str, Any]:
    """
    Executes multi-step root cause analysis on revenue decline between baseline and target month.
    Investigates revenue delta, order volume vs AOV, category shifts, top dropped products, and customer cohorts.
    """
    result = RootCauseDiagnostic.diagnose_revenue_decline(target_month=target_month, baseline_month=baseline_month)
    return result.model_dump()

def generate_chart(metric: str, chart_type: str | None = None, title: str | None = None) -> dict[str, Any]:
    """
    Dynamically generates chart specifications (labels, datasets, styling) from actual database data.
    Supported metrics: 'monthly_revenue', 'category_revenue', 'top_products', 'customer_segments'
    """
    metric_normalized = metric.lower().strip()
    
    if "month" in metric_normalized or "trend" in metric_normalized:
        monthly = SalesAnalytics.get_monthly_revenue()
        labels = [m.month for m in monthly]
        data = [m.revenue for m in monthly]
        return ChartSpec(
            chart_id="chart_monthly_revenue",
            chart_type="line",
            title=title or "Monthly Revenue Trend (USD)",
            labels=labels,
            datasets=[{
                "label": "Gross Revenue ($)",
                "data": data,
                "borderColor": "#3b82f6",
                "backgroundColor": "rgba(59, 130, 246, 0.15)",
                "fill": True,
                "tension": 0.3
            }]
        ).model_dump()

    elif "category" in metric_normalized:
        categories = SalesAnalytics.get_revenue_by_category()
        labels = [c.category_name for c in categories]
        data = [c.revenue for c in categories]
        return ChartSpec(
            chart_id="chart_category_revenue",
            chart_type="bar",
            title=title or "Revenue by Product Category (USD)",
            labels=labels,
            datasets=[{
                "label": "Category Revenue ($)",
                "data": data,
                "backgroundColor": ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"]
            }]
        ).model_dump()

    elif "product" in metric_normalized:
        top_prods = ProductAnalytics.get_top_products_by_revenue(limit=5)
        labels = [p.product_name[:25] + "..." if len(p.product_name) > 25 else p.product_name for p in top_prods]
        data = [p.revenue for p in top_prods]
        return ChartSpec(
            chart_id="chart_top_products",
            chart_type="bar",
            title=title or "Top 5 Products by Revenue (USD)",
            labels=labels,
            datasets=[{
                "label": "Revenue ($)",
                "data": data,
                "backgroundColor": "#10b981"
            }]
        ).model_dump()

    elif "customer" in metric_normalized or "cohort" in metric_normalized:
        summary = CustomerAnalytics.get_customer_summary()
        labels = ["Active Customers", "Inactive Customers", "New Signups (90d)"]
        data = [summary.total_customers - summary.inactive_customers, summary.inactive_customers, summary.new_customers_last_90d]
        return ChartSpec(
            chart_id="chart_customer_segments",
            chart_type="doughnut",
            title=title or "Customer Segmentation & Activity",
            labels=labels,
            datasets=[{
                "label": "Customers",
                "data": data,
                "backgroundColor": ["#10b981", "#ef4444", "#3b82f6"]
            }]
        ).model_dump()

    else:
        # Fallback to monthly revenue
        return generate_chart(metric="monthly_revenue", title=title)

def query_database(sql: str) -> dict[str, Any]:
    """Execute a safe, read-only SQL SELECT query against the e-commerce database."""
    rows = SQLGuard.execute_safe_query(sql)
    columns = list(rows[0].keys()) if rows else []
    return {"query": sql, "row_count": len(rows), "columns": columns, "rows": rows}

# Tool Registry for agent routing
AVAILABLE_TOOLS = {
    "get_kpi_summary": get_kpi_summary,
    "get_sales_metrics": get_sales_metrics,
    "get_top_products": get_top_products,
    "get_customer_metrics": get_customer_metrics,
    "diagnose_revenue_decline": diagnose_revenue_decline,
    "generate_chart": generate_chart,
    "query_database": query_database,
}

TOOL_DEFINITIONS = [
    {
        "name": "get_kpi_summary",
        "description": "Get high-level business KPIs: Total Revenue, Total Orders, Average Order Value (AOV), and customer counts.",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "get_sales_metrics",
        "description": "Get sales metrics either aggregated monthly or broken down by product category.",
        "parameters": {
            "type": "object",
            "properties": {
                "metric_type": {"type": "string", "enum": ["monthly", "category"], "description": "Type of sales breakdown"}
            }
        }
    },
    {
        "name": "get_top_products",
        "description": "Get ranked products by revenue, units sold (volume), or low-performing/stagnant inventory.",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {"type": "string", "enum": ["revenue", "volume", "low_performing"], "description": "Metric to rank by"},
                "limit": {"type": "integer", "description": "Number of products to return (default 5)"}
            }
        }
    },
    {
        "name": "get_customer_metrics",
        "description": "Get customer cohort summary, list of inactive customers (no orders in 90 days), or top customers by lifetime spend.",
        "parameters": {
            "type": "object",
            "properties": {
                "segment": {"type": "string", "enum": ["summary", "inactive", "top_spenders"], "description": "Customer segment to retrieve"},
                "limit": {"type": "integer", "description": "Max records to return"}
            }
        }
    },
    {
        "name": "diagnose_revenue_decline",
        "description": "Perform multi-step root cause analysis on why revenue declined in the latest month. Evaluates orders, AOV, category shifts, lost SKUs, and customer cohorts.",
        "parameters": {
            "type": "object",
            "properties": {
                "target_month": {"type": "string", "description": "Target decline month (YYYY-MM), defaults to latest month"},
                "baseline_month": {"type": "string", "description": "Baseline month for comparison (YYYY-MM)"}
            }
        }
    },
    {
        "name": "generate_chart",
        "description": "Generate a visual chart specification from actual data (e.g. monthly revenue, category breakdown, top products).",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {"type": "string", "description": "Metric to visualize: 'monthly_revenue', 'category_revenue', 'top_products', 'customer_segments'"},
                "chart_type": {"type": "string", "description": "Chart type: 'bar', 'line', 'doughnut'"},
                "title": {"type": "string", "description": "Optional title for the chart"}
            },
            "required": ["metric"]
        }
    },
    {
        "name": "query_database",
        "description": "Execute a custom safe read-only SQL query against the e-commerce database for specific ad-hoc questions.",
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "Read-only SELECT SQL query"}
            },
            "required": ["sql"]
        }
    }
]
