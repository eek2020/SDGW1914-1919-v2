#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────────────────────
# cwgc_refresh.sh — snapshot refresh of the CWGC enrichment in data/sd_2011.db
#
# What it does (in order):
#   1. Re-applies the CWGC schema (idempotent, no backup by default)
#   2. UPSERTs every CSV under data/cwgc_batches and data/source into cwgc_records
#   3. Soft-resets auto-generated cwgc_match rows (preserves operator manual confirms)
#   4. Re-runs the layered matcher
#   5. Prints a fresh stats snapshot
#
# SAFE to run while src/scripts/cwgc_download.py is still scraping in the
# background — the import is read-only on the CSV files. Run it any time
# you want an up-to-date snapshot of the enrichment progress.
#
# Usage:
#   src/scripts/cwgc_refresh.sh                  # full refresh
#   src/scripts/cwgc_refresh.sh --no-match       # skip the matcher (import only)
#   src/scripts/cwgc_refresh.sh --hard-reset     # full DELETE of cwgc_match (no manual rows yet)
#   src/scripts/cwgc_refresh.sh --quiet          # suppress the trailing stats block
#   src/scripts/cwgc_refresh.sh -h | --help
# ────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# Locate the project root (parent of src/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

DB="data/sd_2011.db"
RUN_MATCH=1
MATCH_FLAG="--reset"     # default: preserve manual confirms
SHOW_STATS=1

while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-match)   RUN_MATCH=0; shift ;;
        --hard-reset) MATCH_FLAG="--hard-reset"; shift ;;
        --no-reset)   MATCH_FLAG=""; shift ;;
        --quiet)      SHOW_STATS=0; shift ;;
        -h|--help)
            sed -n '2,22p' "$0"
            exit 0 ;;
        *)
            echo "unknown option: $1" >&2
            echo "see: $0 --help" >&2
            exit 2 ;;
    esac
done

stamp() { date '+%Y-%m-%dT%H:%M:%S'; }
log()   { echo "[refresh $(stamp)] $*"; }

log "starting"
log "DB     : $DB"
log "match  : $([ "$RUN_MATCH" -eq 1 ] && echo "yes (${MATCH_FLAG:-no-reset})" || echo "skipped")"

if [[ ! -f "$DB" ]]; then
    log "ERROR: $DB not found. Run src/scripts/cwgc_schema_migrate.py manually first"
    log "       (it needs a DB to migrate; this refresh script doesn't create one)."
    exit 2
fi

# 1. Schema (idempotent)
log "applying schema (idempotent) ..."
python3 src/scripts/cwgc_schema_migrate.py --db "$DB" --no-backup 2>&1 \
    | sed 's/^/    /'

# 2. Import
log "importing CSVs ..."
python3 src/scripts/cwgc_import.py --db "$DB" 2>&1 \
    | sed 's/^/    /'

# 3. Match (optional)
if [[ "$RUN_MATCH" -eq 1 ]]; then
    log "running matcher ${MATCH_FLAG:-(no reset)} ..."
    if [[ -n "$MATCH_FLAG" ]]; then
        python3 src/scripts/cwgc_match.py --db "$DB" "$MATCH_FLAG" 2>&1 | sed 's/^/    /'
    else
        python3 src/scripts/cwgc_match.py --db "$DB" 2>&1 | sed 's/^/    /'
    fi
fi

# 4. Stats
if [[ "$SHOW_STATS" -eq 1 ]]; then
    echo
    echo "=================================================================="
    echo "  CWGC enrichment snapshot — $(stamp)"
    echo "=================================================================="
    sqlite3 "$DB" <<'SQL'
.headers on
.mode column
.width 28 14
SELECT 'cwgc_records (rows)'        AS metric, COUNT(*) AS value FROM cwgc_records
UNION ALL SELECT 'cwgc_match active rows',     COUNT(*) FROM cwgc_match WHERE is_active=1
UNION ALL SELECT '  └─ exact (soldier)',       COUNT(*) FROM cwgc_match WHERE is_active=1 AND confidence='exact'  AND record_type='soldier'
UNION ALL SELECT '  └─ high  (soldier)',       COUNT(*) FROM cwgc_match WHERE is_active=1 AND confidence='high'   AND record_type='soldier'
UNION ALL SELECT '  └─ high  (officer)',       COUNT(*) FROM cwgc_match WHERE is_active=1 AND confidence='high'   AND record_type='officer'
UNION ALL SELECT '  └─ medium (soldier)',      COUNT(*) FROM cwgc_match WHERE is_active=1 AND confidence='medium' AND record_type='soldier'
UNION ALL SELECT '  └─ medium (officer)',      COUNT(*) FROM cwgc_match WHERE is_active=1 AND confidence='medium' AND record_type='officer'
UNION ALL SELECT '  └─ manual confirms',       COUNT(*) FROM cwgc_match WHERE is_active=1 AND confidence='manual'
UNION ALL SELECT 'soldiers w/ CWGC link',      COUNT(DISTINCT record_id) FROM cwgc_match WHERE is_active=1 AND record_type='soldier' AND confidence IN ('exact','high','manual')
UNION ALL SELECT 'officers w/ CWGC link',      COUNT(DISTINCT record_id) FROM cwgc_match WHERE is_active=1 AND record_type='officer' AND confidence IN ('exact','high','manual')
UNION ALL SELECT 'unmatched CWGC casualties',  COUNT(*) FROM v_cwgc_unmatched
UNION ALL SELECT 'pending operator review',    COUNT(*) FROM v_cwgc_match_candidates
;
SQL
    echo
    echo "  scraper status:"
    if pgrep -f cwgc_download.py >/dev/null 2>&1; then
        pid=$(pgrep -f cwgc_download.py | head -1)
        echo "    running (PID $pid)"
        if [[ -f logs/cwgc_download.log ]]; then
            last_month=$(grep '] Month ' logs/cwgc_download.log | tail -1 || true)
            [[ -n "$last_month" ]] && echo "    $last_month"
        fi
    else
        echo "    (not running)"
    fi
    if [[ -d data/cwgc_batches ]]; then
        echo "    batches on disk: $(ls data/cwgc_batches | wc -l | tr -d ' ')"
    fi
    echo "=================================================================="
fi

log "done"
