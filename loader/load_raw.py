import os
import io
import csv
from pathlib import Path
from datetime import date
from loader.db import get_connection

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
RAW_DIR  = DATA_DIR / "raw"

STATIC_TABLES = ["territories", "products", "customers", "reps"]
DAILY_TABLES  = ["orders", "costs", "returns", "mrr_events"]

RAW_TABLE_COLUMNS = {
    "territories": [
        "territory_id", "territory_name", "region", "country", "zone",
    ],
    "products": [
        "product_id", "product_code", "product_name", "therapeutic_area",
        "product_line", "formulation", "launch_date", "unit_cost_standard",
    ],
    "customers": [
        "customer_id", "account_name", "segment", "tier", "region",
        "territory_id", "contract_start_date", "contract_end_date", "is_active",
    ],
    "reps": [
        "rep_id", "rep_name", "territory_id", "region",
        "manager_name", "hire_date", "annual_quota",
    ],
    "orders": [
        "order_id", "order_date", "product_id", "customer_id", "rep_id",
        "territory_id", "quantity", "list_price", "discount_pct",
        "net_price", "gross_amount", "net_amount",
    ],
    "costs": [
        "cost_id", "product_id", "cost_month", "standard_cost", "actual_cost",
    ],
    "returns": [
        "return_id", "order_id", "return_date", "quantity_returned", "reason",
    ],
    "mrr_events": [
        "event_id", "customer_id", "product_id", "event_month",
        "event_type", "mrr_amount",
    ],
}


def _copy_csv_to_table(conn, csv_path: Path, table: str) -> int:
    """
    Use PostgreSQL COPY for high-throughput CSV ingestion.

    Reads the CSV, re-orders columns to match RAW_TABLE_COLUMNS, and
    streams the result into Postgres via copy_expert.  Returns the number
    of data rows copied.
    """
    cols     = RAW_TABLE_COLUMNS[table]
    col_list = ", ".join(cols)

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        buf    = io.StringIO()
        writer = csv.writer(buf)
        count  = 0
        for row in reader:
            writer.writerow([row.get(c, "") for c in cols])
            count += 1
        buf.seek(0)

    with conn.cursor() as cur:
        copy_sql = (
            f"COPY raw.{table} ({col_list}) FROM STDIN WITH ("
            f"FORMAT CSV, NULL '', HEADER FALSE)"
        )
        cur.copy_expert(copy_sql, buf)

    return count


def load_static(mode: str = "daily") -> None:
    """
    Load static reference tables (territories, products, customers, reps).

    Parameters
    ----------
    mode : "full"
        Truncates all static tables (in reverse FK order) before loading.
    mode : "daily"
        Appends / no-op if rows already present (source CSVs are stable).
    """
    conn = get_connection()
    try:
        if mode == "full":
            with conn.cursor() as cur:
                # Reverse order respects FK constraints
                for tbl in reversed(STATIC_TABLES):
                    cur.execute(f"TRUNCATE raw.{tbl} CASCADE")
            conn.commit()
            print("Truncated static tables.")

        static_dir = RAW_DIR / "static"
        for table in STATIC_TABLES:
            csv_path = static_dir / f"{table}.csv"
            if not csv_path.exists():
                print(f"  SKIP: {csv_path} not found")
                continue
            count = _copy_csv_to_table(conn, csv_path, table)
            conn.commit()
            print(f"  Loaded {count:,} rows -> raw.{table}")

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_daily(target_date: date) -> None:
    """
    Load transactional CSVs for a single date partition.

    Files live under data/raw/YYYY-MM-DD/.  Missing files (e.g. no
    returns.csv on a quiet day) are silently skipped.
    """
    conn = get_connection()
    try:
        daily_dir = RAW_DIR / target_date.isoformat()
        for table in DAILY_TABLES:
            csv_path = daily_dir / f"{table}.csv"
            if not csv_path.exists():
                print(f"  SKIP: {csv_path} not found")
                continue
            count = _copy_csv_to_table(conn, csv_path, table)
            conn.commit()
            print(f"  Loaded {count:,} rows -> raw.{table}  [{target_date}]")

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_all_daily(mode: str = "full") -> None:
    """
    Iterate over every date directory under data/raw/ and call load_daily().

    In "full" mode the daily tables are truncated first (reverse FK order).
    """
    conn = get_connection()
    try:
        if mode == "full":
            with conn.cursor() as cur:
                for tbl in reversed(DAILY_TABLES):
                    cur.execute(f"TRUNCATE raw.{tbl} CASCADE")
            conn.commit()
            print("Truncated daily tables.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    if not RAW_DIR.exists():
        print(f"  WARN: RAW_DIR {RAW_DIR} does not exist; nothing to load.")
        return

    date_dirs = sorted([
        d for d in RAW_DIR.iterdir()
        if d.is_dir() and d.name != "static"
    ])

    if not date_dirs:
        print("  WARN: No date-partitioned directories found under data/raw/.")
        return

    for d in date_dirs:
        try:
            target_date = date.fromisoformat(d.name)
        except ValueError:
            print(f"  SKIP dir (not ISO date): {d.name}")
            continue
        load_daily(target_date)
