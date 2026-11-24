"""
FastAPI REST API Router for RetailPulse BI Agent.
"""
from typing import Any
from fastapi import APIRouter, HTTPException, Query, status
from retailpulse.models.schemas import (
    KPISummary, MonthlyRevenueItem, CategoryRevenueItem,
    ProductMetricItem, CustomerMetricSummary, RootCauseAnalysisResult,
    ChatRequest, ChatResponse, SafeSQLRequest, SafeSQLResponse,
    DataQualityReport, ChartSpec
)
from retailpulse.analytics.sales import SalesAnalytics
from retailpulse.analytics.customers import CustomerAnalytics
from retailpulse.analytics.products import ProductAnalytics
from retailpulse.analytics.root_cause import RootCauseDiagnostic
from retailpulse.analytics.forecasting import ForecastingEngine
from retailpulse.agent.orchestrator import AgentOrchestrator
from retailpulse.agent.tools import generate_chart
from retailpulse.agent.sql_guard import SQLGuard, SQLSecurityException
from retailpulse.data.ingestion import get_latest_quality_report, run_ingestion_pipeline
from retailpulse.core.database import execute_raw_sql

router = APIRouter(prefix="/api", tags=["Analytics & BI"])
orchestrator = AgentOrchestrator()

@router.get("/health", summary="Health and Database Status")
def health_check() -> dict[str, Any]:
    """Returns application health and operational database record counts."""
    try:
        counts = execute_raw_sql("""
            SELECT 
                (SELECT count(*) FROM customers) as customers,
                (SELECT count(*) FROM products) as products,
                (SELECT count(*) FROM orders) as orders,
                (SELECT count(*) FROM order_items) as order_items
        """)
        row = counts[0] if counts else {}
        return {
            "status": "healthy",
            "service": "RetailPulse AI Data Analyst",
            "database": "SQLite (Online)",
            "counts": row
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {str(e)}"
        )

@router.get("/kpis", response_model=KPISummary, summary="Executive KPI Summary")
def get_kpi_summary():
    """Retrieve high-level business metrics: Total Revenue, Orders, AOV, Customers."""
    return SalesAnalytics.get_kpi_summary()

@router.get("/sales/monthly", response_model=list[MonthlyRevenueItem], summary="Monthly Revenue Trend")
def get_monthly_revenue():
    """Returns monthly revenue breakdown, order volume, and Month-over-Month (MoM) growth."""
    return SalesAnalytics.get_monthly_revenue()

@router.get("/sales/categories", response_model=list[CategoryRevenueItem], summary="Revenue by Category")
def get_category_revenue():
    """Returns revenue, order volume, and sales shares across product categories."""
    return SalesAnalytics.get_revenue_by_category()

@router.get("/products/top", response_model=list[ProductMetricItem], summary="Top Products Ranking")
def get_top_products(
    metric: str = Query("revenue", pattern="^(revenue|volume|low_performing)$"),
    limit: int = Query(5, ge=1, le=50)
):
    """Retrieve ranked products by gross revenue, volume sold, or low-performing inventory."""
    if metric == "volume":
        return ProductAnalytics.get_top_products_by_volume(limit=limit)
    elif metric == "low_performing":
        return ProductAnalytics.get_low_performing_products(limit=limit)
    return ProductAnalytics.get_top_products_by_revenue(limit=limit)

@router.get("/customers/summary", response_model=CustomerMetricSummary, summary="Customer Cohort Summary")
def get_customer_summary(limit: int = Query(5, ge=1, le=20)):
    """Retrieve customer cohort breakdown (repeat rate, inactive rate, top spenders)."""
    return CustomerAnalytics.get_customer_summary(top_n=limit)

@router.get("/customers/inactive", summary="List Inactive Customers")
def get_inactive_customers(days: int = Query(90, ge=30, le=365), limit: int = Query(15, ge=1, le=100)):
    """Retrieve list of customers with no completed purchase within the specified days threshold."""
    return CustomerAnalytics.get_inactive_customers(days_inactive=days, limit=limit)

@router.get("/charts/{chart_name}", response_model=ChartSpec, summary="Dynamic Chart Specification")
def get_chart_spec(chart_name: str):
    """Returns dynamic chart visual payload (monthly-revenue, category-revenue, top-products, customer-segments)."""
    normalized = chart_name.replace("-", "_")
    chart_dict = generate_chart(metric=normalized)
    return ChartSpec(**chart_dict)

@router.post("/chat", response_model=ChatResponse, summary="Natural Language BI Question Answering")
def chat_with_analyst(payload: ChatRequest):
    """
    Main natural language AI analyst endpoint.
    Supports multi-turn conversational memory, controlled tool execution, and dynamic chart generation.
    """
    try:
        return orchestrator.answer_question(payload.question, session_id=payload.session_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing AI query: {str(e)}"
        )

@router.post("/diagnostics/revenue-decline", response_model=RootCauseAnalysisResult, summary="Multi-Step Root Cause Diagnosis")
def run_revenue_decline_diagnosis(
    target_month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
    baseline_month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$")
):
    """
    Executes 5-step root-cause analysis investigating revenue, orders, AOV, category performance, and customer cohorts.
    """
    try:
        return RootCauseDiagnostic.diagnose_revenue_decline(
            target_month=target_month,
            baseline_month=baseline_month
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/query/sql", response_model=SafeSQLResponse, summary="Safe Read-Only SQL Query")
def execute_safe_sql_query(payload: SafeSQLRequest):
    """
    Executes a sanitized, read-only SELECT SQL query with strict SQL injection prevention.
    """
    import time
    start = time.time()
    try:
        rows = SQLGuard.execute_safe_query(payload.sql)
        duration_ms = round((time.time() - start) * 1000, 2)
        columns = list(rows[0].keys()) if rows else []
        return SafeSQLResponse(
            query=payload.sql,
            row_count=len(rows),
            columns=columns,
            rows=rows,
            execution_time_ms=duration_ms
        )
    except SQLSecurityException as se:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Security rejection: {str(se)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Query syntax error: {str(e)}")

@router.get("/data-quality", response_model=DataQualityReport, summary="ETL Data Quality Audit Report")
def get_data_quality():
    """Returns the latest data quality audit report (duplicates removed, missing values handled, clean pct)."""
    report = get_latest_quality_report()
    if not report:
        report = run_ingestion_pipeline()
    return report

@router.post("/etl/re-ingest", response_model=DataQualityReport, summary="Trigger Ingestion & Cleaning Pipeline")
def trigger_etl():
    """Triggers complete data cleaning, validation, and database re-population."""
    return run_ingestion_pipeline(force_regenerate=True)

@router.get("/forecast", summary="Predictive Sales Forecast")
def get_sales_forecast(horizon: int = Query(3, ge=1, le=12)):
    """Generates predictive revenue forecast with 95% confidence bounds."""
    return ForecastingEngine.forecast_sales(horizon_months=horizon)

@router.get("/export/sales", summary="Export Monthly Sales CSV")
def export_sales_csv():
    """Exports monthly sales performance as a downloadable CSV."""
    from fastapi.responses import Response
    monthly = SalesAnalytics.get_monthly_revenue()
    import io, csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Month", "Revenue_USD", "Completed_Orders", "AOV_USD", "MoM_Growth_Pct"])
    for m in monthly:
        writer.writerow([m.month, m.revenue, m.orders_count, m.aov, m.mom_growth_pct if m.mom_growth_pct is not None else ""])
    return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=monthly_sales.csv"})

@router.get("/export/products", summary="Export Top Products CSV")
def export_products_csv():
    """Exports top products ranked by revenue as a downloadable CSV."""
    from fastapi.responses import Response
    prods = ProductAnalytics.get_top_products_by_revenue(limit=50)
    import io, csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Product_ID", "Name", "Category", "Price_USD", "Units_Sold", "Revenue_USD", "Stock_Quantity"])
    for p in prods:
        writer.writerow([p.product_id, p.product_name, p.category_name, p.price, p.units_sold, p.revenue, p.stock_quantity])
    return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=products_performance.csv"})
