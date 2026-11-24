"""
Predictive Revenue Forecasting Engine.
Uses weighted trend regression and confidence intervals on historical monthly data
to forecast future sales horizons (descriptive -> predictive BI elevation).
"""
import numpy as np
from typing import Any
from retailpulse.analytics.sales import SalesAnalytics
from retailpulse.models.schemas import ChartSpec

class ForecastingEngine:
    @staticmethod
    def forecast_sales(horizon_months: int = 3) -> dict[str, Any]:
        """
        Forecasts revenue for the next `horizon_months` based on historical trend
        with upper and lower 95% confidence bounds.
        """
        historical = SalesAnalytics.get_monthly_revenue()
        if len(historical) < 3:
            raise ValueError("At least 3 months of historical data required for forecasting.")

        revs = [m.revenue for m in historical]
        months = [m.month for m in historical]
        n = len(revs)

        # Time indices
        x = np.arange(n)
        y = np.array(revs)

        # Weighted linear regression (giving higher weight to recent 6 months)
        weights = np.linspace(0.5, 1.0, n)
        poly = np.polyfit(x, y, deg=1, w=weights)
        slope, intercept = poly[0], poly[1]

        # Calculate residual standard error
        fitted = slope * x + intercept
        residuals = y - fitted
        std_err = np.std(residuals)

        # Generate forecast future months
        last_year, last_month = map(int, months[-1].split("-"))
        forecast_items = []
        forecast_labels = []
        forecast_values = []
        lower_bounds = []
        upper_bounds = []

        cur_year, cur_month = last_year, last_month
        for step in range(1, horizon_months + 1):
            cur_month += 1
            if cur_month > 12:
                cur_month = 1
                cur_year += 1
            
            f_month_str = f"{cur_year:04d}-{cur_month:02d}"
            f_x = n - 1 + step
            pred_val = round(max(0.0, float(slope * f_x + intercept)), 2)
            
            # 95% Confidence interval (1.96 * std_err * sqrt(1 + 1/n + ...))
            margin = round(float(1.96 * std_err * np.sqrt(1 + 1/n + (step**2)/np.sum((x - np.mean(x))**2))), 2)
            low_val = round(max(0.0, pred_val - margin), 2)
            high_val = round(pred_val + margin, 2)

            forecast_labels.append(f_month_str)
            forecast_values.append(pred_val)
            lower_bounds.append(low_val)
            upper_bounds.append(high_val)

            forecast_items.append({
                "month": f_month_str,
                "projected_revenue": pred_val,
                "lower_bound_95": low_val,
                "upper_bound_95": high_val,
                "confidence": "95%"
            })

        # Chart representation combining historical + projected
        all_labels = months + forecast_labels
        hist_series = [r for r in revs] + [None] * horizon_months
        proj_series = [None] * (n - 1) + [revs[-1]] + forecast_values

        chart = ChartSpec(
            chart_id="chart_revenue_forecast",
            chart_type="line",
            title=f"Sales Forecast: Next {horizon_months} Months (with 95% Confidence Bounds)",
            labels=all_labels,
            datasets=[
                {
                    "label": "Historical Revenue ($)",
                    "data": hist_series,
                    "borderColor": "#3b82f6",
                    "backgroundColor": "rgba(59, 130, 246, 0.15)",
                    "fill": False,
                    "tension": 0.3
                },
                {
                    "label": "Projected Revenue ($)",
                    "data": proj_series,
                    "borderColor": "#10b981",
                    "borderDash": [5, 5],
                    "backgroundColor": "rgba(16, 185, 129, 0.1)",
                    "fill": False,
                    "tension": 0.3
                }
            ]
        )

        growth_rate = round(((forecast_values[-1] - revs[-1]) / revs[-1]) * 100, 2) if revs[-1] > 0 else 0.0

        return {
            "historical_baseline_month": months[-1],
            "historical_baseline_revenue": revs[-1],
            "horizon_months": horizon_months,
            "projected_growth_pct": growth_rate,
            "forecast": forecast_items,
            "chart": chart.model_dump()
        }
