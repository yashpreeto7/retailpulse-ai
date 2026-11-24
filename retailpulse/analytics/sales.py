"""
Sales Analytics Engine: Revenue, Orders, AOV, Monthly Breakdown, Category Performance.
"""
from datetime import date
from typing import Any
import pandas as pd
from retailpulse.core.database import execute_raw_sql
from retailpulse.models.schemas import KPISummary, MonthlyRevenueItem, CategoryRevenueItem

class SalesAnalytics:
    @staticmethod
    def get_kpi_summary() -> KPISummary:
        """Computes executive high-level business KPIs."""
        sql = """
        SELECT 
            COUNT(DISTINCT o.order_id) as total_orders,
            SUM(CASE WHEN o.status = 'completed' THEN 1 ELSE 0 END) as completed_orders,
            SUM(CASE WHEN o.status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_orders,
            COALESCE(SUM(CASE WHEN o.status = 'completed' THEN o.total_amount ELSE 0 END), 0) as total_revenue,
            COUNT(DISTINCT c.customer_id) as total_customers
        FROM customers c
        LEFT JOIN orders o ON c.customer_id = o.customer_id
        """
        rows = execute_raw_sql(sql)
        row = rows[0] if rows else {}
        
        total_orders = row.get("total_orders", 0) or 0
        completed_orders = row.get("completed_orders", 0) or 0
        cancelled_orders = row.get("cancelled_orders", 0) or 0
        total_revenue = round(float(row.get("total_revenue", 0.0) or 0.0), 2)
        total_customers = row.get("total_customers", 0) or 0
        
        aov = round(total_revenue / completed_orders, 2) if completed_orders > 0 else 0.0
        
        # Calculate active vs inactive customers (orders in last 90 days of max date)
        max_date_sql = "SELECT MAX(order_date) as max_date FROM orders WHERE status = 'completed'"
        max_date_res = execute_raw_sql(max_date_sql)
        max_date_str = max_date_res[0]["max_date"] if max_date_res and max_date_res[0]["max_date"] else date.today().isoformat()
        
        inactive_sql = f"""
        SELECT COUNT(DISTINCT customer_id) as inactive_cnt
        FROM customers
        WHERE customer_id NOT IN (
            SELECT DISTINCT customer_id
            FROM orders
            WHERE status = 'completed'
              AND order_date >= date('{max_date_str}', '-90 days')
        )
        """
        inactive_res = execute_raw_sql(inactive_sql)
        inactive_cnt = inactive_res[0]["inactive_cnt"] if inactive_res else 0
        active_cnt = max(0, total_customers - inactive_cnt)

        return KPISummary(
            total_revenue=total_revenue,
            total_orders=total_orders,
            total_customers=total_customers,
            average_order_value=aov,
            completed_orders=completed_orders,
            cancelled_orders=cancelled_orders,
            active_customers=active_cnt,
            inactive_customers=inactive_cnt
        )

    @staticmethod
    def get_monthly_revenue() -> list[MonthlyRevenueItem]:
        """Calculates monthly revenue, orders, AOV, and Month-over-Month (MoM) growth."""
        sql = """
        SELECT 
            strftime('%Y-%m', order_date) as month,
            ROUND(SUM(total_amount), 2) as revenue,
            COUNT(order_id) as orders_count,
            ROUND(AVG(total_amount), 2) as aov
        FROM orders
        WHERE status = 'completed'
        GROUP BY strftime('%Y-%m', order_date)
        ORDER BY month ASC
        """
        rows = execute_raw_sql(sql)
        results: list[MonthlyRevenueItem] = []
        prev_rev = None

        for r in rows:
            rev = float(r["revenue"])
            mom_pct = None
            if prev_rev and prev_rev > 0:
                mom_pct = round(((rev - prev_rev) / prev_rev) * 100, 2)
            
            results.append(MonthlyRevenueItem(
                month=r["month"],
                revenue=rev,
                orders_count=int(r["orders_count"]),
                aov=float(r["aov"]),
                mom_growth_pct=mom_pct
            ))
            prev_rev = rev

        return results

    @staticmethod
    def get_revenue_by_category() -> list[CategoryRevenueItem]:
        """Calculates revenue and units sold broken down by product category."""
        sql = """
        SELECT 
            c.category_id,
            c.name as category_name,
            ROUND(SUM(oi.subtotal), 2) as revenue,
            COUNT(DISTINCT o.order_id) as orders_count,
            SUM(oi.quantity) as units_sold
        FROM categories c
        JOIN products p ON c.category_id = p.category_id
        JOIN order_items oi ON p.product_id = oi.product_id
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.status = 'completed'
        GROUP BY c.category_id, c.name
        ORDER BY revenue DESC
        """
        rows = execute_raw_sql(sql)
        total_rev = sum(float(r["revenue"]) for r in rows) or 1.0

        results = []
        for r in rows:
            rev = float(r["revenue"])
            pct = round((rev / total_rev) * 100, 2)
            results.append(CategoryRevenueItem(
                category_id=r["category_id"],
                category_name=r["category_name"],
                revenue=rev,
                orders_count=int(r["orders_count"]),
                units_sold=int(r["units_sold"]),
                pct_of_total=pct
            ))
        return results
