"""
Enterprise RAG (Retrieval-Augmented Generation) Pipeline for RetailPulse AI.
Integrates Alibaba Qwen 2.5 7B with live SQLite relational data, business metric schemas,
and strict anti-hallucination grounding.
"""
import json
import time
from typing import Any
import httpx
from retailpulse.core.database import execute_raw_sql
from retailpulse.core.logger import get_logger
from retailpulse.analytics.sales import SalesAnalytics
from retailpulse.analytics.customers import CustomerAnalytics
from retailpulse.analytics.products import ProductAnalytics
from retailpulse.analytics.root_cause import RootCauseDiagnostic
from retailpulse.analytics.forecasting import ForecastingEngine
from retailpulse.agent.tools import generate_chart
from retailpulse.models.schemas import ChartSpec

logger = get_logger("retailpulse.rag")

# Domain Knowledge Corpus for Schema & Metrics (Strictly conceptual — live numbers always come from SQLite)
KNOWLEDGE_CORPUS = [
    {
        "topic": "KPI Definitions",
        "keywords": ["revenue", "kpi", "sales", "aov", "orders"],
        "content": (
            "Total Gross Revenue is computed as SUM(orders.total_amount) where status='completed'. "
            "Average Order Value (AOV) is Total Gross Revenue / Completed Orders. "
            "All figures are in USD."
        )
    },
    {
        "topic": "Root Cause Framework",
        "keywords": ["decline", "last month", "drop", "why", "trend"],
        "content": (
            "Revenue decline diagnostics decompose Month-over-Month (MoM) variance into "
            "Order Volume Effect, Average Order Value (AOV) Effect, Category-Level Variance, "
            "Product SKU Stockouts, and Customer Cohort Retention."
        )
    },
    {
        "topic": "Customer Retention & Inactivity",
        "keywords": ["customer", "inactive", "churn", "dormant", "recent", "retention"],
        "content": (
            "Inactive Customers are defined as registered accounts with no completed order in the last 90 days. "
            "Repeat customers are accounts with 2 or more completed orders."
        )
    },
    {
        "topic": "Product & Category Taxonomy",
        "keywords": ["category", "product", "sku", "top", "best", "units"],
        "content": (
            "Product categories include Electronics, Home & Kitchen, Fitness & Outdoor, Apparel, "
            "and Beauty & Personal Care. Category revenue shares are computed from completed order_items."
        )
    }
]

class GroundedRAGPipeline:
    def __init__(self, ollama_url: str = "http://127.0.0.1:11434", model_name: str = "qwen2.5:7b"):
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.timeout = 25.0

    def retrieve_context(self, query: str) -> tuple[str, dict[str, Any], ChartSpec | None, str]:
        """
        Retrieves relevant domain knowledge AND executes deterministic analytical tools
        to assemble an authoritative grounded context packet.
        Returns: (grounded_context, data_packet, chart_obj, primary_tool_name)
        """
        q = query.lower()
        context_parts = []
        data_packet = {}
        chart_obj = None
        primary_tool = "get_kpi_summary"

        # 1. Retrieve Knowledge Corpus matches
        matched_topics = []
        for doc in KNOWLEDGE_CORPUS:
            if any(k in q for k in doc["keywords"]):
                matched_topics.append(f"[{doc['topic']}]: {doc['content']}")
        
        if matched_topics:
            context_parts.append("BUSINESS KNOWLEDGE BASE:\n" + "\n".join(matched_topics))

        # 2. Retrieve Live Database Data based on query intent
        if any(w in q for w in ["why", "decline", "drop", "fall", "decline last month"]):
            primary_tool = "diagnose_revenue_decline"
            diag = RootCauseDiagnostic.diagnose_revenue_decline()
            data_packet["root_cause"] = diag.model_dump()
            context_parts.append(
                f"LIVE ROOT CAUSE ANALYSIS (SQLite):\n"
                f"- Target Month: {diag.target_month} (Revenue: ${diag.revenue_target:,.2f})\n"
                f"- Baseline Month: {diag.baseline_month} (Revenue: ${diag.revenue_baseline:,.2f})\n"
                f"- Revenue Delta: ${diag.revenue_delta_dollars:,.2f} ({diag.revenue_delta_pct:.1f}%)\n"
                f"- Volume Delta (Orders): {diag.volume_effect_pct:.1f}%\n"
                f"- AOV Delta: {diag.aov_effect_pct:.1f}%\n"
                f"- Worst Category: {diag.category_breakdown[0]['category_name']} (Loss: ${diag.category_breakdown[0]['delta_dollars']:,.2f})\n"
                f"- Primary Driver: {diag.primary_driver}\n"
                f"- Actionable Takeaway: {diag.actionable_takeaway}"
            )
            chart_dict = generate_chart("monthly_revenue", title="Monthly Revenue Trend Leading to Recent Decline")
            chart_obj = ChartSpec(**chart_dict)

        elif any(w in q for w in ["top product", "top 5", "highest revenue", "best seller"]):
            primary_tool = "get_top_products"
            prods = ProductAnalytics.get_top_products_by_revenue(limit=5)
            prod_dumps = [p.model_dump() for p in prods]
            data_packet["top_products"] = prod_dumps
            data_packet["products"] = prod_dumps
            prod_summary = "\n".join([f"{i}. {p.product_name} ({p.category_name}): ${p.revenue:,.2f} ({p.units_sold} units sold)" for i, p in enumerate(prods, 1)])
            context_parts.append(f"LIVE TOP PRODUCTS RANKED (SQLite, Ranked 1 to 5 by Revenue):\n{prod_summary}")
            chart_dict = generate_chart("top_products", title="Top 5 Products by Revenue")
            chart_obj = ChartSpec(**chart_dict)

        elif any(w in q for w in ["category", "which category", "category share"]):
            primary_tool = "get_sales_metrics"
            cats = SalesAnalytics.get_revenue_by_category()
            data_packet["categories"] = [c.model_dump() for c in cats]
            cat_summary = "\n".join([f"- {c.category_name}: ${c.revenue:,.2f} ({c.pct_of_total:.1f}% share, {c.units_sold} units)" for c in cats])
            context_parts.append(f"LIVE CATEGORY REVENUE (SQLite):\n{cat_summary}")
            if any(w in q for w in ["total revenue", "overall revenue", "kpi", "gross revenue"]):
                kpi = SalesAnalytics.get_kpi_summary()
                data_packet["kpis"] = kpi.model_dump()
                context_parts.append(
                    f"LIVE KPI SUMMARY (SQLite):\n"
                    f"- Total Gross Revenue: ${kpi.total_revenue:,.2f}\n"
                    f"- Total Orders: {kpi.total_orders} ({kpi.completed_orders} completed, {kpi.cancelled_orders} cancelled)\n"
                    f"- Average Order Value: ${kpi.average_order_value:,.2f}"
                )
            chart_dict = generate_chart("category_revenue", title="Revenue by Product Category")
            chart_obj = ChartSpec(**chart_dict)

        elif any(w in q for w in ["month", "trend", "monthly revenue", "sales trend"]):
            primary_tool = "get_sales_metrics"
            monthly = SalesAnalytics.get_monthly_revenue()
            data_packet["monthly_revenue"] = [m.model_dump() for m in monthly]
            recent = "\n".join([f"- {m.month}: ${m.revenue:,.2f} ({m.orders_count} orders, AOV: ${m.aov:,.2f})" for m in monthly[-6:]])
            context_parts.append(f"LIVE MONTHLY SALES REVENUE (SQLite):\n{recent}")
            chart_dict = generate_chart("monthly_revenue", title="Monthly Revenue Trajectory")
            chart_obj = ChartSpec(**chart_dict)

        elif any(w in q for w in ["forecast", "predict", "projection"]):
            primary_tool = "forecast_sales"
            fc = ForecastingEngine.forecast_sales(horizon_months=3)
            data_packet["forecast"] = fc
            fc_summary = "\n".join([f"- {f['month']}: Projected ${f['projected_revenue']:,.2f} (95% CI: ${f['lower_bound_95']:,.2f} to ${f['upper_bound_95']:,.2f})" for f in fc["forecast"]])
            context_parts.append(f"LIVE REVENUE FORECAST (Weighted Regression):\nBaseline: ${fc['historical_baseline_revenue']:,.2f}\n{fc_summary}")
            chart_obj = ChartSpec(**fc["chart"])

        elif any(w in q for w in ["inactive", "dormant", "churn", "not purchased"]):
            primary_tool = "get_customer_metrics"
            inactive = CustomerAnalytics.get_inactive_customers(days_inactive=90, limit=8)
            data_packet["inactive_customers"] = inactive
            inact_summary = "\n".join([f"- {c['name']} ({c['email']}): {int(c['days_since_last_order'])} days inactive, past spend: ${c['historical_spend']:,.2f}" for c in inactive])
            context_parts.append(f"LIVE INACTIVE CUSTOMERS (No orders in >90 days):\n{inact_summary}")

        else:
            primary_tool = "get_kpi_summary"
            kpi = SalesAnalytics.get_kpi_summary()
            data_packet["kpis"] = kpi.model_dump()
            context_parts.append(
                f"LIVE KPI SUMMARY (SQLite):\n"
                f"- Gross Revenue: ${kpi.total_revenue:,.2f}\n"
                f"- Total Orders: {kpi.total_orders} ({kpi.completed_orders} completed, {kpi.cancelled_orders} cancelled)\n"
                f"- Average Order Value: ${kpi.average_order_value:,.2f}\n"
                f"- Active Customers: {kpi.active_customers} | Inactive: {kpi.inactive_customers}"
            )

        grounded_context = "\n\n".join(context_parts)
        return grounded_context, data_packet, chart_obj, primary_tool

    def generate_grounded_answer(self, query: str, context: str) -> str:
        """
        Sends grounded database context and query to local Alibaba Qwen 2.5 7B via Ollama.
        """
        system_prompt = (
            "You are RetailPulse AI, an elite enterprise AI Business Analyst powered by Alibaba's Qwen 2.5 7B model.\n"
            "You provide crisp, authoritative, professional business intelligence and data analysis grounded strictly in transactional data.\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. ONLY state numbers, percentages, dollar amounts, and facts provided in the GROUNDED CONTEXT below.\n"
            "2. NEVER hallucinate or invent numerical results.\n"
            "3. Format your response cleanly using Markdown (use bolding, bullet points, and tables where suitable).\n"
            "4. Provide actionable commercial takeaways based directly on the numbers."
        )

        user_prompt = (
            f"=== GROUNDED DATABASE CONTEXT ===\n"
            f"{context}\n\n"
            f"=== USER BUSINESS QUESTION ===\n"
            f"{query}\n\n"
            f"Provide an authoritative, grounded analysis answering the question:"
        )

        payload = {
            "model": self.model_name,
            "prompt": f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n",
            "stream": False,
            "options": {
                "temperature": 0.2,  # Low temperature for strict factual grounding
                "top_p": 0.9,
                "num_predict": 750
            }
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(f"{self.ollama_url}/api/generate", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    raw_text = data.get("response", "").strip()
                    # Strip any accidental thinking tags if present
                    if "</think>" in raw_text:
                        raw_text = raw_text.split("</think>")[-1].strip()
                    return raw_text
                else:
                    logger.warning(f"Ollama returned HTTP {res.status_code}: {res.text}")
                    return ""
        except Exception as e:
            logger.warning(f"Error querying Qwen 2.5 7B via Ollama: {e}")
            return ""
