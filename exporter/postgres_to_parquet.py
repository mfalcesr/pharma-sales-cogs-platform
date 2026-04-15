import os
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
from pathlib import Path
from datetime import date
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))

GOLD_TABLES = [
    "mart_sales_performance",
    "mart_cogs_margin",
    "mart_customer_health",
    "mart_mrr_waterfall",
    "mart_time_intelligence",
    "mart_forecast",
]


def get_engine():
    user     = os.getenv("POSTGRES_USER", "pharma_user")
    password = os.getenv("POSTGRES_PASSWORD", "")
    host     = os.getenv("POSTGRES_HOST", "localhost")
    port     = os.getenv("POSTGRES_PORT", "5432")
    dbname   = os.getenv("POSTGRES_DB", "pharma_db")
    return create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}")


def export_table_to_parquet(
    engine,
    table_name: str,
    export_dir: Path,
) -> Path:
    with engine.connect() as conn:
        df = pd.read_sql(text(f"SELECT * FROM gold.{table_name}"), conn)

    # Convert object columns to string for Parquet compatibility
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).replace("None", pd.NA)

    table = pa.Table.from_pandas(df, preserve_index=False)
    out_path = export_dir / f"{table_name}.parquet"
    pq.write_table(
        table,
        out_path,
        compression="snappy",
        row_group_size=100_000,
    )
    print(f"  Exported {len(df):,} rows -> {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")
    return out_path


def export_all(export_date: date | None = None) -> list[Path]:
    if export_date is None:
        export_date = date.today()

    export_dir = DATA_DIR / "exports" / export_date.isoformat()
    export_dir.mkdir(parents=True, exist_ok=True)

    engine = get_engine()
    exported = []
    for table_name in GOLD_TABLES:
        try:
            path = export_table_to_parquet(engine, table_name, export_dir)
            exported.append(path)
        except Exception as e:
            print(f"  ERROR exporting {table_name}: {e}")
    return exported
