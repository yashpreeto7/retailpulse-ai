"""
Customer Analytics Engine: Segmentation, Lifetime Value, Repeat Rates, Churn Analysis.
"""
from typing import Any
from retailpulse.core.database import execute_raw_sql
from retailpulse.models.schemas import CustomerMetricSummary

class CustomerAnalytics:
    @staticmethod
    def get_customer_summary(top_n: int = 5) -> CustomerMetricSummary:
        """Computes comprehensive customer cohort and RFM-style segmentation metrics."""
        # Reference max order date in system
        max_date_res = execute_raw_sql("SELECT MAX(order_date) as max_date FROM orders WHERE status = 'completed'")
        max_date = max_date_res[0]["max_date"] if max_date_res and max_date_res[0]["max_date"] else "2024-10-31"

        # 1. Total customers
        total_cust_res = execute_raw_sql("SELECT COUNT(*) as cnt FROM customers")
        total_customers = total_cust_res[0]["cnt"] if total_cust_res else 0

        # 2. New customers (signed up in last 90 days relative to max_date)
        new_cust_sql = f"""
        SELECT COUNT(*) as cnt 
        FROM customers 
        WHERE signup_date >= date('{max_date}', '-90 days')
        """
        new_cust_res = execute_raw_sql(new_cust_sql)
        new_customers = new_cust_res[0]["cnt"] if new_cust_res else 0

        # 3. Repeat customers (completed > 1 order)
        repeat_sql = """
        SELECT COUNT(*) as cnt FROM (
            SELECT customer_id, COUNT(order_id) as ord_cnt
            FROM orders
            WHERE status = 'completed'
            GROUP BY customer_id
            HAVING ord_cnt > 1
        )
        """
        repeat_res = execute_raw_sql(repeat_sql)
        repeat_customers = repeat_res[0]["cnt"] if repeat_res else 0
        repeat_rate = round((repeat_customers / total_customers * 100), 2) if total_customers > 0 else 0.0

        # 4. Inactive customers (no completed order in last 90 days)
        inactive_sql = f"""
        SELECT COUNT(DISTINCT c.customer_id) as cnt
        FROM customers c
        WHERE c.customer_id NOT IN (
            SELECT DISTINCT customer_id
            FROM orders
            WHERE status = 'completed'
              AND order_date >= date('{max_date}', '-90 days')
        )
        """
        inactive_res = execute_raw_sql(inactive_sql)
        inactive_customers = inactive_res[0]["cnt"] if inactive_res else 0
        inactive_rate = round((inactive_customers / total_customers * 100), 2) if total_customers > 0 else 0.0

        # 5. Top customers by spend
        top_cust_sql = f"""
        SELECT 
            c.customer_id,
            c.name,
            c.email,
            c.city,
            c.state,
            COUNT(o.order_id) as total_orders,
            ROUND(SUM(o.total_amount), 2) as lifetime_spend,
            ROUND(AVG(o.total_amount), 2) as average_order_value,
            MAX(o.order_date) as last_order_date
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        WHERE o.status = 'completed'
        GROUP BY c.customer_id, c.name, c.email, c.city, c.state
        ORDER BY lifetime_spend DESC
        LIMIT {top_n}
        """
        top_customers = execute_raw_sql(top_cust_sql)

        return CustomerMetricSummary(
            total_customers=total_customers,
            new_customers_last_90d=new_customers,
            repeat_customers=repeat_customers,
            repeat_customer_rate_pct=repeat_rate,
            inactive_customers=inactive_customers,
            inactive_customer_rate_pct=inactive_rate,
            top_customers=top_customers
        )

    @staticmethod
    def get_inactive_customers(days_inactive: int = 90, limit: int = 15) -> list[dict[str, Any]]:
        """Retrieves specific customers who have not made a purchase within `days_inactive`."""
        max_date_res = execute_raw_sql("SELECT MAX(order_date) as max_date FROM orders WHERE status = 'completed'")
        max_date = max_date_res[0]["max_date"] if max_date_res and max_date_res[0]["max_date"] else "2024-10-31"

        sql = f"""
        SELECT 
            c.customer_id,
            c.name,
            c.email,
            c.city,
            c.state,
            MAX(o.order_date) as last_order_date,
            ROUND(julianday('{max_date}') - julianday(MAX(o.order_date)), 0) as days_since_last_order,
            COUNT(o.order_id) as past_orders,
            ROUND(COALESCE(SUM(o.total_amount), 0), 2) as historical_spend
        FROM customers c
        LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.status = 'completed'
        GROUP BY c.customer_id, c.name, c.email, c.city, c.state
        HAVING last_order_date IS NULL OR last_order_date < date('{max_date}', '-{days_inactive} days')
        ORDER BY days_since_last_order DESC
        LIMIT {limit}
        """
        return execute_raw_sql(sql)
