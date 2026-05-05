import pytest
import numpy as np
import pandas as pd
from datetime import date


def _make_test_actuals(n_months: int = 24, product_lines: list[str] = None) -> pd.DataFrame:
    if product_lines is None:
        product_lines = ["Primary Care", "Biologics"]
    from dateutil.relativedelta import relativedelta
    start = date(2023, 1, 1)
    rows = []
    for pl in product_lines:
        base = 1_000_000 if pl == "Biologics" else 500_000
        for i in range(n_months):
            month = start + relativedelta(months=i)
            # Add some seasonality noise
            revenue = base * (1 + 0.05 * np.sin(i * np.pi / 6)) + np.random.normal(0, 10_000)
            rows.append({"revenue_month": month, "product_line": pl, "revenue": max(revenue, 0)})
    return pd.DataFrame(rows)


def test_generate_forecasts_returns_correct_shape():
    from forecasting.model import generate_forecasts, FORECAST_MONTHS
    np.random.seed(42)
    actuals = _make_test_actuals(24)
    forecasts = generate_forecasts(actuals)
    n_lines = actuals["product_line"].nunique()
    assert len(forecasts) == n_lines * FORECAST_MONTHS


def test_forecast_rows_are_in_future():
    from forecasting.model import generate_forecasts
    np.random.seed(42)
    actuals = _make_test_actuals(24)
    forecasts = generate_forecasts(actuals)
    last_actual = pd.to_datetime(actuals["revenue_month"]).max()
    for _, row in forecasts.iterrows():
        assert pd.to_datetime(row["revenue_month"]) > last_actual


def test_forecast_revenue_non_negative():
    from forecasting.model import generate_forecasts
    np.random.seed(42)
    actuals = _make_test_actuals(24)
    forecasts = generate_forecasts(actuals)
    assert (forecasts["revenue"] >= 0).all(), "Forecast revenue must be non-negative"


def test_forecast_lower_bound_lte_upper_bound():
    from forecasting.model import generate_forecasts
    np.random.seed(42)
    actuals = _make_test_actuals(24)
    forecasts = generate_forecasts(actuals)
    assert (forecasts["forecast_lower_bound"] <= forecasts["forecast_upper_bound"]).all()


def test_forecast_handles_short_series():
    from forecasting.model import generate_forecasts, FORECAST_MONTHS
    actuals = _make_test_actuals(n_months=4, product_lines=["Generics"])
    forecasts = generate_forecasts(actuals)
    assert len(forecasts) == FORECAST_MONTHS
    assert (forecasts["revenue"] >= 0).all()


def test_is_forecast_flag():
    from forecasting.model import generate_forecasts
    np.random.seed(42)
    actuals = _make_test_actuals(12)
    forecasts = generate_forecasts(actuals)
    assert forecasts["is_forecast"].all(), "All rows from generate_forecasts must have is_forecast=True"
