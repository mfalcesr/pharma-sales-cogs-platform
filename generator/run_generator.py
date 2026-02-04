"""
CLI entry point for the Pharma data generator.

Modes
-----
full
    Generates all static reference data (territories, products, customers, reps)
    plus every daily order/return file and every monthly cost/MRR file from
    START_DATE through END_DATE.  Expect ~5–10 minutes to run for a 4-year
    window on a modern laptop.

daily
    Generates (or re-generates) orders and returns for a single date (defaults
    to today).  If static reference CSVs are absent they are created first.

Usage
-----
    python -m generator.run_generator --mode full
    python -m generator.run_generator --mode daily
    python -m generator.run_generator --mode daily --date 2024-06-15
"""

import argparse
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from generator.config import END_DATE, START_DATE
from generator.generate_costs import (
    generate_costs_for_month,
    generate_mrr_events_for_month,
)
from generator.generate_customers import generate_customers
from generator.generate_orders import generate_orders_for_date
from generator.generate_products import generate_products
from generator.generate_reps import generate_reps, generate_territories

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
STATIC_DIR = DATA_DIR / "raw" / "static"


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


def write_csv(records: list[dict], path: Path) -> None:
    """Write *records* to a CSV file at *path*, creating parent dirs as needed."""
    if not records:
        print(f"  Skipping (0 rows) → {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records).to_csv(path, index=False)
    print(f"  Wrote {len(records):,} rows → {path}")


# ---------------------------------------------------------------------------
# Static reference data
# ---------------------------------------------------------------------------


def generate_static_data() -> tuple[list, list, list, list]:
    """Generate and persist all static reference data to STATIC_DIR.

    Returns
    -------
    tuple[list, list, list, list]
        (territories, products, customers, reps)
    """
    print("Generating static reference data...")

    territories = generate_territories()
    write_csv(territories, STATIC_DIR / "territories.csv")

    products = generate_products()
    write_csv(products, STATIC_DIR / "products.csv")

    customers = generate_customers(territories)
    write_csv(customers, STATIC_DIR / "customers.csv")

    reps = generate_reps(territories)
    write_csv(reps, STATIC_DIR / "reps.csv")

    return territories, products, customers, reps


def load_static_data() -> tuple[list, list, list, list]:
    """Load static reference CSVs from STATIC_DIR into lists of dicts.

    Raises
    ------
    FileNotFoundError
        If any expected static file is missing.
    """
    territories = pd.read_csv(STATIC_DIR / "territories.csv").to_dict("records")
    products    = pd.read_csv(STATIC_DIR / "products.csv").to_dict("records")
    customers   = pd.read_csv(STATIC_DIR / "customers.csv").to_dict("records")
    reps        = pd.read_csv(STATIC_DIR / "reps.csv").to_dict("records")
    return territories, products, customers, reps


# ---------------------------------------------------------------------------
# Daily generation
# ---------------------------------------------------------------------------


def generate_for_date(
    target_date: date,
    products: list[dict],
    customers: list[dict],
    reps: list[dict],
) -> None:
    """Generate and persist order and return CSVs for *target_date*."""
    daily_dir = DATA_DIR / "raw" / target_date.isoformat()
    print(f"  Generating orders for {target_date}...")

    orders, returns = generate_orders_for_date(target_date, products, customers, reps)
    write_csv(orders,  daily_dir / "orders.csv")
    write_csv(returns, daily_dir / "returns.csv")


# ---------------------------------------------------------------------------
# Monthly generation (costs + MRR)
# ---------------------------------------------------------------------------


def generate_monthly_data(
    products: list[dict],
    customers: list[dict],
    start: date,
    end: date,
) -> None:
    """Generate and persist cost and MRR event CSVs month by month.

    Carries MRR state (active / churned pairs) forward across months so that
    churn/expansion/reactivation events are realistic and consistent.

    Parameters
    ----------
    products, customers:
        Static reference data.
    start, end:
        Inclusive date range; month boundaries are inferred automatically.
    """
    try:
        from dateutil.relativedelta import relativedelta
        _advance = lambda d: d + relativedelta(months=1)  # noqa: E731
    except ImportError:
        # Fallback when python-dateutil is not installed
        def _advance(d: date) -> date:
            return (d + timedelta(days=32)).replace(day=1)

    current = start.replace(day=1)
    end_month = end.replace(day=1)
    previous_active: set[tuple] = set()
    previous_churned: set[tuple] = set()

    while current <= end_month:
        monthly_dir = DATA_DIR / "raw" / current.isoformat()
        print(f"  Generating costs/MRR for {current.strftime('%Y-%m')}...")

        costs = generate_costs_for_month(current, products)
        write_csv(costs, monthly_dir / "costs.csv")

        mrr_events, previous_active, previous_churned = generate_mrr_events_for_month(
            current, customers, products, previous_active, previous_churned
        )
        write_csv(mrr_events, monthly_dir / "mrr_events.csv")

        current = _advance(current)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pharma synthetic data generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--mode",
        choices=["full", "daily"],
        default="daily",
        help="'full' = entire history, 'daily' = single date (default: today)",
    )
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        default=date.today(),
        metavar="YYYY-MM-DD",
        help="Target date for daily mode (default: today)",
    )
    args = parser.parse_args()

    if args.mode == "full":
        territories, products, customers, reps = generate_static_data()

        print(f"\nGenerating daily orders: {START_DATE} → {END_DATE}")
        current = START_DATE
        while current <= END_DATE:
            generate_for_date(current, products, customers, reps)
            current += timedelta(days=1)

        print(f"\nGenerating monthly costs/MRR: {START_DATE} → {END_DATE}")
        generate_monthly_data(products, customers, START_DATE, END_DATE)

        print("\nFull generation complete.")

    else:  # daily
        try:
            _, products, customers, reps = load_static_data()
        except FileNotFoundError:
            print("Static data not found; generating it first...")
            _, products, customers, reps = generate_static_data()

        generate_for_date(args.date, products, customers, reps)
        print(f"\nDaily generation complete for {args.date}.")


if __name__ == "__main__":
    main()
