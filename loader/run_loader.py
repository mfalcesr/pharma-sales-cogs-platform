"""
Entry point for the raw CSV loader.

Usage
-----
# Full reload (truncate + reload everything):
python -m loader.run_loader --mode full

# Incremental daily load for today:
python -m loader.run_loader --mode daily

# Incremental daily load for a specific date:
python -m loader.run_loader --mode daily --date 2024-03-15
"""
import argparse
from datetime import date

from loader.load_raw import load_static, load_daily, load_all_daily


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load raw CSVs into Postgres raw schema."
    )
    parser.add_argument(
        "--mode",
        choices=["full", "daily"],
        default="daily",
        help="'full' truncates and reloads everything; 'daily' is idempotent/incremental.",
    )
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        default=date.today(),
        metavar="YYYY-MM-DD",
        help="Target date for daily mode (defaults to today).",
    )
    args = parser.parse_args()

    if args.mode == "full":
        print("=== Full load: static reference data ===")
        load_static(mode="full")
        print("\n=== Full load: all daily transactional data ===")
        load_all_daily(mode="full")
        print("\nFull load complete.")
    else:
        print("=== Daily load: static reference data (incremental) ===")
        load_static(mode="daily")
        print(f"\n=== Daily load: transactional data for {args.date} ===")
        load_daily(args.date)
        print("\nDaily load complete.")


if __name__ == "__main__":
    main()
