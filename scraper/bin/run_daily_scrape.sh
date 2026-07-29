#!/bin/bash
# Wrapper for the scheduled (launchd) daily incremental scrape.
#
# Handles the three things main.py itself doesn't: loading DATABASE_URL from
# backend/.env (launchd jobs start with a near-empty environment), refusing
# to start a second run while one is still in progress (a full walk can take
# hours, and unegui.mn should never see two of us at once), and capturing
# output to a log file since nothing else will.
#
# --pages is a generous ceiling, not a target: --stop-after-known-pages cuts
# the walk short once we run back into pages that are entirely already-known
# ads, which is the normal case for a daily run. The ceiling only matters on
# an unusually high-volume day.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRAPER_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$SCRAPER_DIR/.." && pwd)"
LOG_DIR="$SCRAPER_DIR/logs"
LOCK_DIR="$SCRAPER_DIR/.daily_scrape.lock"

mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/daily_scrape_$(date +%Y-%m-%d_%H%M%S).log"

# macOS has no flock(1); use mkdir's atomicity as the lock, with a PID file
# inside so a leftover lock from a killed/crashed run can be told apart from
# one that's genuinely still running.
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    old_pid="$(cat "$LOCK_DIR/pid" 2>/dev/null || true)"
    if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
        echo "$(date): previous run (pid $old_pid) still in progress, skipping this trigger" >> "$LOG_DIR/skipped_overlaps.log"
        exit 0
    fi
    echo "$(date): stale lock (pid $old_pid not running), reclaiming" >> "$LOG_DIR/skipped_overlaps.log"
    rm -rf "$LOCK_DIR"
    mkdir "$LOCK_DIR"
fi
echo $$ > "$LOCK_DIR/pid"
trap 'rm -rf "$LOCK_DIR"' EXIT

status=0
{
    echo "=== daily scrape start: $(date) ==="

    set -a
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/backend/.env"
    set +a

    cd "$SCRAPER_DIR"
    # shellcheck disable=SC1091
    source .venv/bin/activate

    python -m scraper.main \
        --pages 60 \
        --skip-recent-days 1 \
        --stop-after-known-pages 3 || status=$?

    echo "=== daily scrape end: $(date) (exit $status) ==="
} >> "$LOG_FILE" 2>&1

# Retention: don't let logs grow forever on an unattended machine.
find "$LOG_DIR" -name 'daily_scrape_*.log' -mtime +30 -delete

exit "$status"
