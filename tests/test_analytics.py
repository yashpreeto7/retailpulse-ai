"""
Tests for Core Business Analytics Calculations.
"""
import pytest
from retailpulse.analytics.sales import SalesAnalytics
from retailpulse.analytics.customers import CustomerAnalytics
from retailpulse.analytics.products import ProductAnalytics

def test_sales_kpi_summary():
    kpi = SalesAnalytics.get_kpi_summary()
    assert kpi.total_revenue > 0
    assert kpi.total_orders > 0
    assert kpi.completed_orders > 0
    assert kpi.completed_orders + kpi.cancelled_orders <= kpi.total_orders
    # AOV mathematical identity: total_revenue / completed_orders
    expected_aov = round(kpi.total_revenue / kpi.completed_orders, 2)
    assert abs(kpi.average_order_value - expected_aov) <= 0.05
    assert kpi.active_customers + kpi.inactive_customers == kpi.total_customers

def test_monthly_revenue_analytics():
    monthly = SalesAnalytics.get_monthly_revenue()
    assert len(monthly) >= 2
    # Check chronological ordering
    months = [m.month for m in monthly]
    assert months == sorted(months)
    for m in monthly:
        assert m.revenue > 0
        assert m.orders_count > 0

def test_category_revenue_shares():
    categories = SalesAnalytics.get_revenue_by_category()
    assert len(categories) > 0
    total_share = sum(c.pct_of_total for c in categories)
    assert 99.0 <= total_share <= 101.0
    # Sorted descending by revenue
    revenues = [c.revenue for c in categories]
    assert revenues == sorted(revenues, reverse=True)

def test_top_products_ranking():
    top_rev = ProductAnalytics.get_top_products_by_revenue(limit=5)
    assert len(top_rev) == 5
    revs = [p.revenue for p in top_rev]
    assert revs == sorted(revs, reverse=True)

    top_vol = ProductAnalytics.get_top_products_by_volume(limit=5)
    assert len(top_vol) == 5
    vols = [p.units_sold for p in top_vol]
    assert vols == sorted(vols, reverse=True)

def test_customer_segmentation():
    summary = CustomerAnalytics.get_customer_summary(top_n=5)
    assert summary.total_customers > 0
    assert 0 <= summary.repeat_customer_rate_pct <= 100
    assert 0 <= summary.inactive_customer_rate_pct <= 100
    assert len(summary.top_customers) <= 5

    inactive = CustomerAnalytics.get_inactive_customers(days_inactive=90, limit=10)
    for c in inactive:
        if c.get("days_since_last_order") is not None:
            assert c["days_since_last_order"] >= 90
