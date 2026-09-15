# Pharma Sales & COGS Intelligence Platform

A data engineering portfolio project that models a pharmaceutical company's end-to-end sales and cost-of-goods analytics pipeline. Synthetic data covers four years of transactional history across 20 drug products, 150 customer accounts, 30 sales reps, and 10 territories, loaded into PostgreSQL, transformed through a medallion architecture with dbt, forecast with Holt-Winters, and served to Power BI.

[![CI](https://github.com/mfalcesr/pharma-sales-cogs-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/mfalcesr/pharma-sales-cogs-platform/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## Tech Stack

| Layer | Tool / Library | Purpose |
|---|---|---|
| Data Generation | Python 3.11, Faker 24, NumPy 1.26 | Synthetic pharma data with realistic seasonality |
| Storage | PostgreSQL 15 (Docker) | Relational store for all pipeline layers |
| Transformation | dbt-postgres 1.8, dbt-utils 1.1 | Bronze → Silver → Gold medallion models |
| Forecasting | statsmodels 0.14, SciPy 1.13 | Holt-Winters ETS, 6-month horizon |
| Export | PyArrow 15, pandas 2.2 | Parquet backups for archival / BI hand-off |
| Orchestration | Bash + cron | Nightly pipeline scheduling |
| Containerization | Docker Compose | One-command Postgres spin-up |
| Visualization | Power BI Desktop | Direct Query to gold schema |

---

## Architecture

```
                     ┌─────────────────────────────────┐
                     │        Data Generator            │
                     │  (Python / Faker / NumPy)        │
                     │  Products, Customers, Reps,      │
                     │  Orders, Costs, Returns, MRR     │
                     └────────────────┬────────────────┘
                                      │ CSV files
                                      ▼
                          data/raw/static/   (reference)
                          data/raw/YYYY-MM-DD/ (daily)
                                      │
                     ┌────────────────▼────────────────┐
                     │          Loader Module           │
                     │   (psycopg2 / SQLAlchemy)        │
                     │   COPY CSV → raw schema          │
                     └────────────────┬────────────────┘
                                      │
                     ┌────────────────▼────────────────┐
                     │       PostgreSQL raw schema      │
                     │  territories, products,          │
                     │  customers, reps, orders,        │
                     │  costs, returns, mrr_events      │
                     └────────────────┬────────────────┘
                                      │ dbt run
                          ┌───────────▼───────────┐
                          │    bronze schema       │
                          │  Type-cast, dedupe,    │
                          │  _loaded_at watermark  │
                          └───────────┬───────────┘
                                      │ dbt run
                          ┌───────────▼───────────┐
                          │    silver schema       │
                          │  dim_product           │
                          │  dim_customer          │
                          │  dim_rep               │
                          │  dim_territory         │
                          │  dim_date              │
                          │  fct_orders            │
                          │  fct_costs             │
                          │  fct_returns           │
                          │  fct_mrr               │
                          └───────────┬───────────┘
                                      │ dbt run
                          ┌───────────▼───────────┐
                          │     gold schema        │
                          │  mart_sales_summary    │
                          │  mart_cogs_margin      │
                          │  mart_rep_performance  │
                          │  mart_mrr_waterfall    │
                          │  mart_territory_health │
                          └─────────┬──────┬──────┘
                                    │      │
               ┌────────────────────▼─┐  ┌─▼──────────────────┐
               │  Power BI Desktop    │  │  Parquet Export     │
               │  Direct Query        │  │  data/exports/      │
               │  gold schema         │  │  (PyArrow)          │
               └──────────────────────┘  └────────────────────┘
                                    │
               ┌────────────────────▼──────────────┐
               │  Forecasting Module                │
               │  Holt-Winters ETS (statsmodels)    │
               │  6-month horizon, 95% CI bands     │
               │  → gold.mart_forecast              │
               └───────────────────────────────────┘
```

---

## Design Choices

### PostgreSQL over an embedded database

Most production pharma analytics stacks run on Postgres, Redshift, or Snowflake - all server-based, transactional databases. Using Postgres here matches that operational reality. It exercises the full `dbt-postgres` adapter including incremental models with real `_loaded_at` watermarks, schema isolation enforced at the database level, and `COPY`-based bulk loading via psycopg2. An embedded database like DuckDB would have simplified the local setup but would not have demonstrated the loader and schema isolation patterns that matter in production environments. The trade-off is a running Docker container; the benefit is a pipeline that transfers directly to a real deployment without architectural changes.

### Strict layer isolation in the medallion architecture

Bronze, silver, and gold are separate PostgreSQL schemas, not naming conventions within a single schema. No model in silver queries raw directly, and no model in gold queries bronze. This hard boundary means a bug in a silver transformation never corrupts the raw copy, and you can always rebuild the entire downstream from bronze without touching the generator or loader. The `_loaded_at` watermark on every bronze table makes incremental dbt models idempotent: re-running on the same day only processes rows that arrived after the last run, not the full table.

### Holt-Winters ETS over ARIMA or a machine learning model

Pharmaceutical revenue has strong, predictable annual seasonality driven by budget cycles, Q1 prescribing patterns, and summer troughs. Holt-Winters additive ETS captures exactly that structure without requiring stationarity transformations (ARIMA) or a feature engineering pipeline (gradient boosting, neural networks). The model is interpretable: a product manager can reason about the trend component, the level, and the seasonal index for each month directly from the fitted parameters. `statsmodels` provides analytic 95% confidence intervals, which are more meaningful to stakeholders than bootstrapped prediction intervals from a tree model. The minimum viable input is 24 months of history; the model falls back to a linear trend for product lines with shorter series.

### Seeded RNG and explicit seasonality multipliers in the generator

Every random number generator in the generator module is seeded with a fixed integer so the full four-year dataset is byte-for-byte reproducible across machines and Python versions. Monthly seasonality multipliers are hard-coded constants in `config.py` rather than sampled from a distribution. A purely random generator would produce flat time series with no structure for the forecasting module to fit. Hard-coding the multipliers makes the seasonality intentional and documentable, not an accidental artefact of the seed.

### Bash + cron over Airflow

Airflow is the right orchestrator for a distributed, multi-team pipeline with complex dependency graphs and SLA monitoring. For a single-machine portfolio project it would add a Celery worker, Redis, Flower, and three extra Docker containers to schedule five sequential shell commands. Bash + cron achieves the same nightly scheduling with one script (`cron_runner.sh`) and one crontab file, keeping the project runnable on any machine with Docker and Python 3.11 installed. If this pipeline were handed to a production team, the `cron_runner.sh` steps map directly to Airflow tasks with no logic changes.

### DirectQuery mode in Power BI

The gold marts are connected via DirectQuery rather than imported and cached in Power BI's in-memory model. This ensures the report always reflects the latest dbt run without a manual refresh step, and it enforces a clear contract: the gold schema is the single source of truth, not a copy inside the BI tool. The practical constraint is that DirectQuery requires the PostgreSQL container to be running when the report is open. For a demo this is fine; a production deployment would use a scheduled import refresh against a cloud database instead.

---

## Quick Start

### Prerequisites

- Docker Desktop (for PostgreSQL)
- Python 3.11+
- Power BI Desktop (optional, for visualization)

### 1. Create your .env

```bash
cp .env.example .env
```

`docker-compose.yml` reads `POSTGRES_USER`, `POSTGRES_PASSWORD` and `POSTGRES_DB` with no
fallback values, so the container will not start without this file. Change the placeholder
password before running anything you care about.

### 2. Start PostgreSQL

```bash
docker compose up -d
```

Postgres will initialize with `init_schemas.sql` automatically on first run. Verify with:

```bash
docker exec -it pharma_postgres psql -U pharma_user -d pharma_db -c "\dn"
```

### 3. Install Python dependencies

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Run the full pipeline

```bash
bash cron_runner.sh full
```

This executes in sequence: generate → load → dbt deps → dbt run → dbt test → forecast → export.

### 5. Run only the data generator (standalone)

```bash
# Full historical backfill (2022-01-01 to 2025-12-31)
python -m generator.run_generator --mode=full

# Daily increment for today
python -m generator.run_generator --mode=daily

# Daily increment for a specific date
python -m generator.run_generator --mode=daily --date 2024-06-15
```

---

## What a Run Produces

`bash cron_runner.sh full` chains generate → load → dbt deps → dbt run → dbt test → forecast → export,
appending one timestamped line per step to `logs/YYYY-MM-DD.log` and stopping at the first
non-zero exit:

```
[YYYY-MM-DD HH:MM:SS] --- START: generator ---
[YYYY-MM-DD HH:MM:SS] --- OK: generator ---
[YYYY-MM-DD HH:MM:SS] --- START: loader ---
[YYYY-MM-DD HH:MM:SS] --- OK: loader ---
[YYYY-MM-DD HH:MM:SS] --- START: dbt-run ---
```

The generator and loader report row counts per table as they go. The static counts are fixed
constants in `generator/config.py`, so they are identical on every machine:

```
Generating static reference data...
  Wrote 10 rows → data/raw/static/territories.csv
  Wrote 20 rows → data/raw/static/products.csv
  Wrote 150 rows → data/raw/static/customers.csv
  Wrote 30 rows → data/raw/static/reps.csv

Generating daily orders: 2022-01-01 → 2025-12-31

=== Full load: static reference data ===
  Loaded 10 rows -> raw.territories
  Loaded 20 rows -> raw.products
  Loaded 150 rows -> raw.customers
  Loaded 30 rows -> raw.reps
```

A completed run leaves:

```
data/
├── raw/static/          # the four reference CSVs above
├── raw/YYYY-MM-DD/      # one directory per simulated day: orders, costs, returns, mrr_events
└── exports/YYYY-MM-DD/  # Parquet snapshot of the gold marts
logs/YYYY-MM-DD.log     # one line per pipeline step
```

Confirm the warehouse built by listing the gold marts:

```bash
docker exec -it pharma_postgres psql -U pharma_user -d pharma_db -c "\dt gold.*"
```

---

## Data Model

### Raw Schema (source of truth, loaded from CSV)

| Table | Rows (approx.) | Description |
|---|---|---|
| `raw.territories` | 10 | Sales territories with region and zone |
| `raw.products` | 20 | Drug products with therapeutic area and cost |
| `raw.customers` | 150 | Pharma customer accounts (hospitals, pharmacies, clinics) |
| `raw.reps` | 30 | Sales representatives with quotas |
| `raw.orders` | ~50,000/year | Daily transactional orders with pricing |
| `raw.costs` | ~240/year | Monthly standard vs. actual COGS per product |
| `raw.returns` | ~1,500/year | Return events linked to orders |
| `raw.mrr_events` | ~variable | Monthly recurring revenue events (new/churn/expansion) |

### Bronze Schema (dbt, incremental)

Mirrors raw tables with casting, null handling, and `_loaded_at` watermarking. No business logic.

### Silver Schema (dbt, dimensional model)

**Dimensions**

| Model | Grain | Key fields |
|---|---|---|
| `dim_product` | 1 row per product | therapeutic_area, product_line, formulation |
| `dim_customer` | 1 row per customer | segment, tier, region, territory |
| `dim_rep` | 1 row per rep | territory, manager, annual_quota |
| `dim_territory` | 1 row per territory | region, zone, country |
| `dim_date` | 1 row per calendar day | year, quarter, month, week, is_weekend |

**Facts**

| Model | Grain | Key metrics |
|---|---|---|
| `fct_orders` | 1 row per order line | gross_amount, net_amount, discount_pct, quantity |
| `fct_costs` | 1 row per product-month | standard_cost, actual_cost, variance_pct |
| `fct_returns` | 1 row per return | quantity_returned, return_reason |
| `fct_mrr` | 1 row per customer-product-month event | mrr_amount, event_type |

### Gold Schema (dbt, business-ready marts)

| Mart | Description |
|---|---|
| `mart_sales_summary` | Revenue by product, territory, period with YoY and MoM comparisons |
| `mart_cogs_margin` | Gross margin by product line and therapeutic area |
| `mart_rep_performance` | Attainment vs. quota, rank within region |
| `mart_mrr_waterfall` | MRR bridge: new + expansion − churn + reactivation |
| `mart_territory_health` | Territory scorecard: revenue, customers, rep count, avg discount |
| `mart_forecast` | 6-month revenue forecast with 95% confidence intervals |

---

## Forecasting

The forecasting module (`forecasting/run_forecast.py`) uses **Holt-Winters Exponential Smoothing** (additive trend, additive seasonality, period=12 months) via `statsmodels.tsa.holtwinters.ExponentialSmoothing`.

- **Input**: monthly net revenue from `gold.mart_sales_summary` (trailing 36 months minimum)
- **Horizon**: 6 months forward
- **Output**: point forecast + 95% confidence bands written to `gold.mart_forecast`
- **Granularity**: run at total company level and repeated per therapeutic area

---

## Power BI Connection

1. Open Power BI Desktop
2. **Get Data** → **PostgreSQL database**
3. Server: `localhost`, Database: `pharma_db`
4. Select **DirectQuery** mode
5. Navigate to the **gold** schema and import marts as separate tables
6. Build relationships on `product_id`, `customer_id`, `rep_id`, `territory_id`, `date_id`

Credentials: the `POSTGRES_USER` and `POSTGRES_PASSWORD` values from your `.env` — see
[`.env.example`](.env.example) for the full list of variables.

---

## Cron Schedule

| Time | Step | Command |
|---|---|---|
| 01:00 | Generate synthetic data | `cron_runner.sh generate` |
| 01:30 | Load CSVs to Postgres | `cron_runner.sh load` |
| 02:00 | dbt transformations | `cron_runner.sh transform` |
| 03:00 | Forecasting model | `cron_runner.sh forecast` |
| 03:30 | Parquet export | `cron_runner.sh export` |

Import the schedule:

```bash
crontab schedule.crontab
```

Set `NOTIFY_EMAIL` in your environment to receive failure alerts:

```bash
export NOTIFY_EMAIL=you@example.com
```

---

## dbt

### Run transformations

```bash
# Install dbt packages
dbt deps --project-dir dbt --profiles-dir dbt

# Run all models
dbt run --project-dir dbt --profiles-dir dbt

# Run only silver layer
dbt run --project-dir dbt --profiles-dir dbt --select silver.*

# Run only gold marts
dbt run --project-dir dbt --profiles-dir dbt --select gold.*
```

### Test data quality

```bash
dbt test --project-dir dbt --profiles-dir dbt
```

Tests cover: not-null, unique, accepted-values, referential integrity, and custom revenue sanity checks.

### Generate and serve docs

```bash
dbt docs generate --project-dir dbt --profiles-dir dbt
dbt docs serve --project-dir dbt --profiles-dir dbt
# Opens browser at http://localhost:8080
```

---

## Testing

```bash
pytest tests/ -v
```

Key test modules:

| Test file | Coverage |
|---|---|
| `tests/test_generators.py` | Row counts, schema completeness, value ranges |
| `tests/test_costs.py` | Cost variance bounds, MRR event type validity |
| `tests/test_orders.py` | Price calculations, discount bounds, return rate |
| `tests/test_loader.py` | Postgres connectivity, COPY idempotency |

---

## Project Structure

```
.
├── .env.example                # Environment template (copy to .env, which is gitignored)
├── docker-compose.yml          # PostgreSQL container
├── init_schemas.sql            # Schema + table DDL
├── requirements.txt            # Python dependencies
├── cron_runner.sh              # Bash orchestrator
├── schedule.crontab            # Cron schedule definition
├── generator/                  # Synthetic data generator
│   ├── __init__.py
│   ├── config.py               # All generation parameters
│   ├── generate_products.py
│   ├── generate_customers.py
│   ├── generate_reps.py
│   ├── generate_orders.py
│   ├── generate_costs.py
│   └── run_generator.py        # CLI entry point
├── loader/                     # CSV → Postgres loader
├── dbt/                        # dbt project (bronze/silver/gold)
├── forecasting/                # Holt-Winters forecasting module
├── exporter/                   # Parquet export module
├── tests/                      # pytest test suite
├── data/
│   ├── raw/                    # Generated CSVs (gitignored except .gitkeep)
│   └── exports/                # Parquet output (gitignored except .gitkeep)
└── logs/                       # Pipeline run logs (gitignored)
```

---

## License

MIT, see [LICENSE](LICENSE).
