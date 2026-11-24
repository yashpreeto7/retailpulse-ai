"""
Product Analytics Engine: Top-selling, highest-revenue, and low-performing inventory metrics.
"""
from typing import Any
from retailpulse.core.database import execute_raw_sql
from retailpulse.models.schemas import ProductMetricItem

class ProductAnalytics:
    @staticmethod
    def get_top_products_by_revenue(limit: int = 5) -> list[ProductMetricItem]:
        """Returns top products ranked by gross revenue."""
        sql = f"""
        SELECT 
            p.product_id,
            p.name as product_name,
            c.name as category_name,
            p.price,
            p.stock_quantity,
            p.is_active,
            COALESCE(SUM(oi.quantity), 0) as units_sold,
            ROUND(COALESCE(SUM(oi.subtotal), 0), 2) as revenue
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
        JOIN order_items oi ON p.product_id = oi.product_id
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.status = 'completed'
        GROUP BY p.product_id, p.name, c.name, p.price, p.stock_quantity, p.is_active
        ORDER BY revenue DESC
        LIMIT {limit}
        """
        rows = execute_raw_sql(sql)
        return [ProductMetricItem(**r) for r in rows]

    @staticmethod
    def get_top_products_by_volume(limit: int = 5) -> list[ProductMetricItem]:
        """Returns top products ranked by total volume of units sold."""
        sql = f"""
        SELECT 
            p.product_id,
            p.name as product_name,
            c.name as category_name,
            p.price,
            p.stock_quantity,
            p.is_active,
            COALESCE(SUM(oi.quantity), 0) as units_sold,
            ROUND(COALESCE(SUM(oi.subtotal), 0), 2) as revenue
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
        JOIN order_items oi ON p.product_id = oi.product_id
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.status = 'completed'
        GROUP BY p.product_id, p.name, c.name, p.price, p.stock_quantity, p.is_active
        ORDER BY units_sold DESC
        LIMIT {limit}
        """
        rows = execute_raw_sql(sql)
        return [ProductMetricItem(**r) for r in rows]

    @staticmethod
    def get_low_performing_products(limit: int = 5) -> list[ProductMetricItem]:
        """Identifies stagnant, low-velocity, or zero-sale products tying up inventory capital."""
        sql = f"""
        SELECT 
            p.product_id,
            p.name as product_name,
            c.name as category_name,
            p.price,
            p.stock_quantity,
            p.is_active,
            COALESCE(SUM(oi.quantity), 0) as units_sold,
            ROUND(COALESCE(SUM(oi.subtotal), 0), 2) as revenue
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN order_items oi ON p.product_id = oi.product_id
        LEFT JOIN orders o ON oi.order_id = o.order_id AND o.status = 'completed'
        GROUP BY p.product_id, p.name, c.name, p.price, p.stock_quantity, p.is_active
        ORDER BY units_sold ASC, revenue ASC
        LIMIT {limit}
        """
        rows = execute_raw_sql(sql)
        return [ProductMetricItem(**r) for r in rows]
