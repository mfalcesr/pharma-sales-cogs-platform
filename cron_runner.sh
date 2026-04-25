#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"
DATE=$(date +%Y-%m-%d)
LOG_FILE="${LOG_DIR}/${DATE}.log"
VENV="${SCRIPT_DIR}/.venv/bin/activate"
NOTIFY_EMAIL="${NOTIFY_EMAIL:-}"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

fail() {
    log "ERROR: $*"
    if [[ -n "$NOTIFY_EMAIL" ]]; then
        echo "Pipeline step '$1' failed on $DATE. Check $LOG_FILE for details." \
            | mail -s "[PHARMA PIPELINE] FAILURE: $1" "$NOTIFY_EMAIL" 2>/dev/null || true
    fi
    exit 1
}

run_step() {
    local step="$1"
    shift
    log "--- START: $step ---"
    if "$@" >> "$LOG_FILE" 2>&1; then
        log "--- OK: $step ---"
    else
        fail "$step"
    fi
}

source "$VENV" 2>/dev/null || { log "virtualenv not found at $VENV, using system Python"; }

cd "$SCRIPT_DIR"

case "${1:-}" in
    generate)
        run_step "generator" python -m generator.run_generator --mode=daily
        ;;
    load)
        run_step "loader" python -m loader.run_loader --mode=daily
        ;;
    transform)
        run_step "dbt-deps" dbt deps --project-dir dbt --profiles-dir dbt
        run_step "dbt-run"  dbt run  --project-dir dbt --profiles-dir dbt
        run_step "dbt-test" dbt test --project-dir dbt --profiles-dir dbt
        ;;
    forecast)
        run_step "forecasting" python -m forecasting.run_forecast
        ;;
    export)
        run_step "exporter" python -m exporter.run_export
        ;;
    full)
        run_step "generator"  python -m generator.run_generator --mode=full
        run_step "loader"     python -m loader.run_loader --mode=full
        run_step "dbt-deps"   dbt deps --project-dir dbt --profiles-dir dbt
        run_step "dbt-run"    dbt run  --project-dir dbt --profiles-dir dbt
        run_step "dbt-test"   dbt test --project-dir dbt --profiles-dir dbt
        run_step "forecasting" python -m forecasting.run_forecast
        run_step "exporter"   python -m exporter.run_export
        ;;
    *)
        echo "Usage: $0 {generate|load|transform|forecast|export|full}"
        exit 1
        ;;
esac
