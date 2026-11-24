"""
Pydantic schemas for data validation, API requests/responses, and tool execution.
"""
from typing import Any, Literal
from datetime import date, datetime, timezone
from pydantic import BaseModel, Field, EmailStr

# --- Ingestion & Data Quality Schemas ---
class CustomerRaw(BaseModel):
    customer_id: str
    name: str
    email: str | None = None
    city: str | None = None
    state: str | None = None
    signup_date: str | date

class ProductRaw(BaseModel):
    product_id: str
    category_id: str
    name: str
    sku: str
    price: float
    cost: float
    stock_quantity: int = 0

class OrderRaw(BaseModel):
    order_id: str
    customer_id: str
    order_date: str | date
    status: str = "completed"
    total_amount: float
    shipping_amount: float = 0.0
    discount_amount: float = 0.0

class OrderItemRaw(BaseModel):
    order_item_id: str
    order_id: str
    product_id: str
    quantity: int
    unit_price: float
    subtotal: float | None = None

class DataQualityReport(BaseModel):
    total_raw_records: int
    duplicates_removed: int
    missing_values_handled: int
    records_loaded: int
    clean_pct: float
    issues_detected: list[str] = []
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# --- Analytics Response Schemas ---
class KPISummary(BaseModel):
    total_revenue: float
    total_orders: int
    total_customers: int
    average_order_value: float
    completed_orders: int
    cancelled_orders: int
    active_customers: int
    inactive_customers: int
    currency: str = "USD"

class MonthlyRevenueItem(BaseModel):
    month: str  # YYYY-MM
    revenue: float
    orders_count: int
    aov: float
    mom_growth_pct: float | None = None

class CategoryRevenueItem(BaseModel):
    category_id: str
    category_name: str
    revenue: float
    orders_count: int
    units_sold: int
    pct_of_total: float

class ProductMetricItem(BaseModel):
    product_id: str
    product_name: str
    category_name: str
    price: float
    units_sold: int
    revenue: float
    stock_quantity: int
    is_active: bool

class CustomerMetricSummary(BaseModel):
    total_customers: int
    new_customers_last_90d: int
    repeat_customers: int
    repeat_customer_rate_pct: float
    inactive_customers: int
    inactive_customer_rate_pct: float
    top_customers: list[dict[str, Any]]

# --- Multi-step Root Cause Analysis Schemas ---
class RootCauseDimension(BaseModel):
    factor_name: str
    impact_description: str
    metric_delta_pct: float
    numerical_evidence: dict[str, Any]

class RootCauseAnalysisResult(BaseModel):
    target_month: str
    baseline_month: str
    revenue_target: float
    revenue_baseline: float
    revenue_delta_dollars: float
    revenue_delta_pct: float
    volume_effect_pct: float  # delta orders
    aov_effect_pct: float      # delta aov
    primary_driver: str
    category_breakdown: list[dict[str, Any]]
    product_breakdown: list[dict[str, Any]]
    customer_cohort_breakdown: dict[str, Any]
    actionable_takeaway: str

# --- Dynamic Chart Spec Schema ---
class ChartSpec(BaseModel):
    chart_id: str
    chart_type: Literal["bar", "line", "pie", "doughnut"]
    title: str
    labels: list[str]
    datasets: list[dict[str, Any]]
    options: dict[str, Any] = {}

# --- Chat & Agent Schemas ---
class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000)
    session_id: str | None = None

class ToolExecutionTrace(BaseModel):
    tool_name: str
    input_args: dict[str, Any]
    output_summary: str
    execution_time_ms: float

class ChatResponse(BaseModel):
    answer: str
    grounded: bool = True
    executed_tools: list[ToolExecutionTrace] = []
    data_points: dict[str, Any] = {}
    chart: ChartSpec | None = None
    suggested_followups: list[str] = []
    model_provider: str = "RetailPulse Grounded Engine"
    latency_ms: float = 0.0

class SafeSQLRequest(BaseModel):
    sql: str = Field(..., min_length=5, max_length=2000)

class SafeSQLResponse(BaseModel):
    query: str
    row_count: int
    columns: list[str]
    rows: list[dict[str, Any]]
    execution_time_ms: float
