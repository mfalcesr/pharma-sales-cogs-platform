import pandas as pd
from sqlalchemy import text
from forecasting.fetch_actuals import get_engine


def upsert_forecasts(forecast_df: pd.DataFrame) -> int:
    """
    Delete existing forecast rows for the forecast months/product_lines,
    then insert the new forecast rows. Returns row count inserted.
    """
    if forecast_df.empty:
        print("No forecast rows to write.")
        return 0

    engine = get_engine()
    with engine.begin() as conn:
        # Delete stale forecast rows for these months
        months = forecast_df["revenue_month"].unique().tolist()
        product_lines = forecast_df["product_line"].unique().tolist()
        conn.execute(text("""
            DELETE FROM gold.mart_forecast
            WHERE is_forecast = TRUE
              AND revenue_month = ANY(:months)
              AND product_line = ANY(:plines)
        """), {"months": months, "plines": product_lines})

        # Insert new forecast rows
        forecast_df.to_sql(
            "mart_forecast",
            conn,
            schema="gold",
            if_exists="append",
            index=False,
            method="multi",
        )

    n = len(forecast_df)
    print(f"Upserted {n} forecast rows into gold.mart_forecast.")
    return n
