import warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

FORECAST_MONTHS = 6
CONFIDENCE_LEVEL = 0.95


def _forecast_series(series: pd.Series, n_periods: int) -> dict:
    """
    Fit Holt-Winters and return forecast + confidence interval.
    Falls back to linear trend if series is too short.
    """
    series = series.dropna()
    if len(series) < 6:
        # Not enough data; project using simple linear trend
        x = np.arange(len(series))
        slope, intercept = np.polyfit(x, series.values, 1)
        future_x = np.arange(len(series), len(series) + n_periods)
        forecast_values = intercept + slope * future_x
        std = series.std() if len(series) > 1 else series.mean() * 0.1
        z = 1.96  # ~95% CI
        return {
            "forecast":    np.maximum(forecast_values, 0).tolist(),
            "lower_bound": np.maximum(forecast_values - z * std, 0).tolist(),
            "upper_bound": (forecast_values + z * std).tolist(),
        }

    seasonal_periods = min(12, len(series) // 2)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = ExponentialSmoothing(
            series,
            trend="add",
            seasonal="add" if len(series) >= 2 * seasonal_periods else None,
            seasonal_periods=seasonal_periods if len(series) >= 2 * seasonal_periods else None,
            damped_trend=True,
        ).fit(optimized=True)

    forecast_obj = model.forecast(n_periods)
    # Bootstrap confidence interval from in-sample residuals
    residuals = model.resid
    std = residuals.std()
    z = 1.96
    forecast_values = np.maximum(forecast_obj.values, 0)

    return {
        "forecast":    forecast_values.tolist(),
        "lower_bound": np.maximum(forecast_values - z * std, 0).tolist(),
        "upper_bound": (forecast_values + z * std).tolist(),
    }


def generate_forecasts(df: pd.DataFrame) -> pd.DataFrame:
    """
    df: columns [revenue_month, product_line, revenue]
    Returns forecast rows ready for insertion into gold.mart_forecast.
    """
    from dateutil.relativedelta import relativedelta

    df = df.copy()
    df["revenue_month"] = pd.to_datetime(df["revenue_month"])
    df = df.sort_values(["product_line", "revenue_month"])

    forecast_rows = []
    for product_line, group in df.groupby("product_line"):
        group = group.set_index("revenue_month").sort_index()
        series = group["revenue"].asfreq("MS")  # month-start frequency

        result = _forecast_series(series, FORECAST_MONTHS)

        last_month = series.index[-1]
        for i in range(FORECAST_MONTHS):
            forecast_month = last_month + relativedelta(months=i + 1)
            forecast_rows.append({
                "revenue_month":         forecast_month.date(),
                "product_line":          product_line,
                "therapeutic_area":      None,
                "revenue":               round(result["forecast"][i], 2),
                "units_sold":            None,
                "order_count":           None,
                "is_forecast":           True,
                "forecast_lower_bound":  round(result["lower_bound"][i], 2),
                "forecast_upper_bound":  round(result["upper_bound"][i], 2),
            })

    return pd.DataFrame(forecast_rows)
