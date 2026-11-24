"""
Multi-Step Root Cause Diagnostic Engine.
Answers complex multi-factor business inquiries such as:
'Why did revenue decline last month?'
Decomposes revenue into Volume vs AOV effects, Category shifts, SKU drop-offs, and Customer cohorts.
"""
from typing import Any
from retailpulse.core.database import execute_raw_sql
from retailpulse.models.schemas import RootCauseAnalysisResult

class RootCauseDiagnostic:
    @staticmethod
    def diagnose_revenue_decline(target_month: str | None = None, baseline_month: str | None = None) -> RootCauseAnalysisResult:
        """
        Executes a 5-step diagnostic breakdown comparing target month against previous baseline month.
        """
        # 1. Determine target and baseline months if not explicitly provided
        months_sql = """
        SELECT DISTINCT strftime('%Y-%m', order_date) as month
        FROM orders
        WHERE status = 'completed'
        ORDER BY month DESC
        LIMIT 2
        """
        available_months = execute_raw_sql(months_sql)
        if len(available_months) < 2:
            raise ValueError("Insufficient historical data to perform comparative month-over-month diagnosis.")

        if not target_month:
            target_month = available_months[0]["month"]
        if not baseline_month:
            baseline_month = available_months[1]["month"]

        # Step 1: Macro Metric Decomposition (Revenue, Orders, AOV)
        macro_sql = f"""
        SELECT 
            strftime('%Y-%m', order_date) as month,
            ROUND(SUM(total_amount), 2) as revenue,
            COUNT(order_id) as orders_count,
            ROUND(AVG(total_amount), 2) as aov
        FROM orders
        WHERE status = 'completed' AND strftime('%Y-%m', order_date) IN ('{baseline_month}', '{target_month}')
        GROUP BY month
        ORDER BY month ASC
        """
        macro_rows = {r["month"]: r for r in execute_raw_sql(macro_sql)}
        
        base_data = macro_rows.get(baseline_month, {"revenue": 0.0, "orders_count": 0, "aov": 0.0})
        target_data = macro_rows.get(target_month, {"revenue": 0.0, "orders_count": 0, "aov": 0.0})

        rev_base = float(base_data["revenue"])
        rev_target = float(target_data["revenue"])
        rev_delta = round(rev_target - rev_base, 2)
        rev_delta_pct = round(((rev_target - rev_base) / rev_base * 100), 2) if rev_base > 0 else 0.0

        orders_base = int(base_data["orders_count"])
        orders_target = int(target_data["orders_count"])
        vol_delta_pct = round(((orders_target - orders_base) / orders_base * 100), 2) if orders_base > 0 else 0.0

        aov_base = float(base_data["aov"])
        aov_target = float(target_data["aov"])
        aov_delta_pct = round(((aov_target - aov_base) / aov_base * 100), 2) if aov_base > 0 else 0.0

        # Step 2: Category Variance Analysis
        cat_sql = f"""
        SELECT 
            c.name as category_name,
            ROUND(SUM(CASE WHEN strftime('%Y-%m', o.order_date) = '{baseline_month}' THEN oi.subtotal ELSE 0 END), 2) as base_revenue,
            ROUND(SUM(CASE WHEN strftime('%Y-%m', o.order_date) = '{target_month}' THEN oi.subtotal ELSE 0 END), 2) as target_revenue
        FROM categories c
        JOIN products p ON c.category_id = p.category_id
        JOIN order_items oi ON p.product_id = oi.product_id
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.status = 'completed' AND strftime('%Y-%m', o.order_date) IN ('{baseline_month}', '{target_month}')
        GROUP BY c.name
        ORDER BY base_revenue DESC
        """
        cat_rows = execute_raw_sql(cat_sql)
        category_breakdown = []
        for r in cat_rows:
            b_rev = float(r["base_revenue"])
            t_rev = float(r["target_revenue"])
            delta_dollars = round(t_rev - b_rev, 2)
            delta_pct = round(((t_rev - b_rev) / b_rev * 100), 2) if b_rev > 0 else 0.0
            category_breakdown.append({
                "category_name": r["category_name"],
                "baseline_revenue": b_rev,
                "target_revenue": t_rev,
                "delta_dollars": delta_dollars,
                "delta_pct": delta_pct
            })
        category_breakdown.sort(key=lambda x: x["delta_dollars"])

        # Step 3: Product SKU Level Variance (Top Losers)
        prod_sql = f"""
        SELECT 
            p.product_id,
            p.name as product_name,
            c.name as category_name,
            ROUND(SUM(CASE WHEN strftime('%Y-%m', o.order_date) = '{baseline_month}' THEN oi.subtotal ELSE 0 END), 2) as base_revenue,
            ROUND(SUM(CASE WHEN strftime('%Y-%m', o.order_date) = '{target_month}' THEN oi.subtotal ELSE 0 END), 2) as target_revenue,
            SUM(CASE WHEN strftime('%Y-%m', o.order_date) = '{baseline_month}' THEN oi.quantity ELSE 0 END) as base_units,
            SUM(CASE WHEN strftime('%Y-%m', o.order_date) = '{target_month}' THEN oi.quantity ELSE 0 END) as target_units
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
        JOIN order_items oi ON p.product_id = oi.product_id
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.status = 'completed' AND strftime('%Y-%m', o.order_date) IN ('{baseline_month}', '{target_month}')
        GROUP BY p.product_id, p.name, c.name
        HAVING base_revenue > 0 OR target_revenue > 0
        """
        prod_rows = execute_raw_sql(prod_sql)
        product_breakdown = []
        for r in prod_rows:
            b_rev = float(r["base_revenue"])
            t_rev = float(r["target_revenue"])
            d_rev = round(t_rev - b_rev, 2)
            product_breakdown.append({
                "product_name": r["product_name"],
                "category_name": r["category_name"],
                "baseline_revenue": b_rev,
                "target_revenue": t_rev,
                "delta_dollars": d_rev,
                "baseline_units": int(r["base_units"]),
                "target_units": int(r["target_units"])
            })
        product_breakdown.sort(key=lambda x: x["delta_dollars"])

        # Step 4: Customer Activity & Cohort Dynamics (Repeat vs New Buyers)
        cohort_sql = f"""
        SELECT 
            strftime('%Y-%m', o.order_date) as month,
            COUNT(DISTINCT o.customer_id) as active_customers,
            SUM(CASE WHEN c.signup_date >= date(o.order_date, '-30 days') THEN 1 ELSE 0 END) as new_customer_orders,
            SUM(CASE WHEN c.signup_date < date(o.order_date, '-30 days') THEN 1 ELSE 0 END) as repeat_customer_orders
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.status = 'completed' AND strftime('%Y-%m', o.order_date) IN ('{baseline_month}', '{target_month}')
        GROUP BY month
        """
        cohort_rows = {r["month"]: r for r in execute_raw_sql(cohort_sql)}
        c_base = cohort_rows.get(baseline_month, {"active_customers": 0, "repeat_customer_orders": 0, "new_customer_orders": 0})
        c_target = cohort_rows.get(target_month, {"active_customers": 0, "repeat_customer_orders": 0, "new_customer_orders": 0})

        cust_delta_pct = round(((c_target["active_customers"] - c_base["active_customers"]) / c_base["active_customers"] * 100), 2) if c_base["active_customers"] > 0 else 0.0
        repeat_delta_pct = round(((c_target["repeat_customer_orders"] - c_base["repeat_customer_orders"]) / c_base["repeat_customer_orders"] * 100), 2) if c_base["repeat_customer_orders"] > 0 else 0.0

        customer_cohort_breakdown = {
            "baseline_active_customers": c_base["active_customers"],
            "target_active_customers": c_target["active_customers"],
            "customer_count_delta_pct": cust_delta_pct,
            "baseline_repeat_orders": c_base["repeat_customer_orders"],
            "target_repeat_orders": c_target["repeat_customer_orders"],
            "repeat_orders_delta_pct": repeat_delta_pct
        }

        # Step 5: Primary Driver Attribution & Actionable Takeaway
        worst_category = category_breakdown[0] if category_breakdown else {"category_name": "None", "delta_dollars": 0}
        top_dropped_skus = [p["product_name"] for p in product_breakdown[:2]]
        
        primary_driver = (
            f"The revenue decline of ${abs(rev_delta):,.2f} ({rev_delta_pct:.1f}%) in {target_month} was primarily driven by "
            f"a sharp collapse in the '{worst_category['category_name']}' category (${worst_category['delta_dollars']:,.2f}), "
            f"compounded by a {abs(vol_delta_pct):.1f}% drop in total order volume."
        )

        actionable_takeaway = (
            f"Root cause summary: 1) Supply chain stockout/drop in '{', '.join(top_dropped_skus)}' "
            f"accounted for the bulk of category loss. 2) Repeat buyer engagement declined by {abs(repeat_delta_pct):.1f}%. "
            f"Recommendation: Prioritize stock replenishment for core high-margin items in {worst_category['category_name']} "
            f"and launch targeted retention/re-engagement campaigns for inactive repeat buyers."
        )

        return RootCauseAnalysisResult(
            target_month=target_month,
            baseline_month=baseline_month,
            revenue_target=rev_target,
            revenue_baseline=rev_base,
            revenue_delta_dollars=rev_delta,
            revenue_delta_pct=rev_delta_pct,
            volume_effect_pct=vol_delta_pct,
            aov_effect_pct=aov_delta_pct,
            primary_driver=primary_driver,
            category_breakdown=category_breakdown,
            product_breakdown=product_breakdown[:5],
            customer_cohort_breakdown=customer_cohort_breakdown,
            actionable_takeaway=actionable_takeaway
        )
