import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()


def get_engine():
    user     = os.getenv("POSTGRES_USER", "pharma_user")
    password = os.getenv("POSTGRES_PASSWORD", "")
    host     = os.getenv("POSTGRES_HOST", "localhost")
    port     = os.getenv("POSTGRES_PORT", "5432")
    dbname   = os.getenv("POSTGRES_DB", "pharma_db")
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}")


def fetch_monthly_revenue() -> pd.DataFrame:
    """Returns monthly revenue by product_line from gold.mart_forecast (actuals only)."""
    engine = get_engine()
    query = text("""
        SELECT
            revenue_month,
            product_line,
            SUM(revenue) AS revenue
        FROM gold.mart_forecast
        WHERE is_forecast = FALSE
          AND revenue_month IS NOT NULL
        GROUP BY revenue_month, product_line
        ORDER BY product_line, revenue_month
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, parse_dates=["revenue_month"])
    return df
