"""
Tests for Multi-Step Root Cause Diagnostic Analysis.
"""
import pytest
from retailpulse.analytics.root_cause import RootCauseDiagnostic

def test_multi_step_revenue_decline_diagnosis():
    result = RootCauseDiagnostic.diagnose_revenue_decline()
    
    assert result.target_month is not None
    assert result.baseline_month is not None
    assert result.revenue_target > 0
    assert result.revenue_baseline > 0
    
    # Mathematical identity verification: revenue_delta_dollars = revenue_target - revenue_baseline
    expected_delta = round(result.revenue_target - result.revenue_baseline, 2)
    assert abs(result.revenue_delta_dollars - expected_delta) < 0.05
    
    # Percentage identity
    expected_pct = round(((result.revenue_target - result.revenue_baseline) / result.revenue_baseline) * 100, 2)
    assert abs(result.revenue_delta_pct - expected_pct) < 0.05

    # Check that category breakdown identifies Electronics as top drop
    assert len(result.category_breakdown) > 0
    worst_category = result.category_breakdown[0]
    assert worst_category["delta_dollars"] < 0
    assert worst_category["category_name"] == "Electronics"

    # Check product breakdown
    assert len(result.product_breakdown) > 0
    assert result.product_breakdown[0]["delta_dollars"] < 0

    # Check cohort breakdown contains repeat buyer drop metrics
    cohort = result.customer_cohort_breakdown
    assert "repeat_orders_delta_pct" in cohort
    assert "customer_count_delta_pct" in cohort

    # Grounded takeaway
    assert len(result.primary_driver) > 20
    assert len(result.actionable_takeaway) > 20
