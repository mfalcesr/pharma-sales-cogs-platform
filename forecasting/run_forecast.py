from forecasting.fetch_actuals import fetch_monthly_revenue
from forecasting.model import generate_forecasts
from forecasting.write_forecast import upsert_forecasts


def main():
    print("Fetching actuals from gold layer...")
    actuals = fetch_monthly_revenue()
    if actuals.empty:
        print("No actuals found; skipping forecast.")
        return

    print(f"  {len(actuals)} monthly records across {actuals['product_line'].nunique()} product lines.")
    print("Running Holt-Winters forecast...")
    forecast_df = generate_forecasts(actuals)
    print(f"  Generated {len(forecast_df)} forecast rows.")
    upsert_forecasts(forecast_df)
    print("Forecast complete.")


if __name__ == "__main__":
    main()
