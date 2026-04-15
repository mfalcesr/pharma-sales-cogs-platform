import argparse
from datetime import date
from exporter.postgres_to_parquet import export_all


def main():
    parser = argparse.ArgumentParser(description="Export gold tables to Parquet")
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()

    print(f"Exporting gold layer to Parquet for {args.date}...")
    paths = export_all(args.date)
    print(f"Export complete: {len(paths)} files written.")


if __name__ == "__main__":
    main()
