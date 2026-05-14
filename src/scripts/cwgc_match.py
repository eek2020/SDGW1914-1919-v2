#!/usr/bin/env python3
"""
CWGC Matcher (cwgc_match target)

Populates the `cwgc_match` table with links between `cwgc_records` and
`soldiers` / `officers`. Uses a layered strategy with increasing
permissiveness; later layers can only add NEW pairs because the
`idx_cwgc_match_one_active` partial unique index rejects duplicates of
the same (cwgc_id, record_type, record_id) while is_active=1.

Layers (run in order):
  1. EXACT  — soldiers: surname + initials + service_number + death_date
                        all four normalized and non-empty
  2. HIGH   — soldiers: surname + initials + death_date (1:1 unambiguous)
  3. HIGH   — officers: surname + initials + death_date (1:1 unambiguous)
  4. MEDIUM — soldiers: surname + christian_names + death_date  (candidates)
  5. MEDIUM — officers: surname + christian_names + death_date  (candidates)

The "1:1 unambiguous" filter for HIGH means: a CWGC record only matches a
soldier at HIGH confidence if exactly one soldier and one CWGC record
share the join key. Anything ambiguous falls through to MEDIUM where the
operator reviews via `v_cwgc_match_candidates`.

DOES NOT modify `soldiers` or `officers` (CLAUDE.md §6.1).

Usage:
    python3 src/scripts/cwgc_match.py                       # default: data/sd_2011.db
    python3 src/scripts/cwgc_match.py --db /some/other.db
    python3 src/scripts/cwgc_match.py --reset               # wipe cwgc_match first
    python3 src/scripts/cwgc_match.py --layers exact high   # run a subset
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from pathlib import Path

DEFAULT_DB = Path("data/sd_2011.db")
ALL_LAYERS = ["exact", "high", "high-off", "medium", "medium-off"]


def log(msg: str) -> None:
    print(f"[cwgc_match] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Build normalised temp tables
# ---------------------------------------------------------------------------
def build_temp_tables(con: sqlite3.Connection) -> None:
    """Create normalised join keys in TEMP tables.

    Soldier and CWGC fields need different cleaning:
      surname        : UPPER, trim
      initials       : strip [. - space ' /], UPPER. SDGW: "WCA"; CWGC: "W C A"
      service_number : strip [. - space ' /], UPPER. CWGC also wraps in "'...'".
      christian_names: UPPER, trim, collapse whitespace
      death_date     : already ISO yyyy-mm-dd in both tables.
    """
    cur = con.cursor()
    log("  building _norm_soldiers ...")
    cur.execute("DROP TABLE IF EXISTS _norm_soldiers;")
    cur.execute("""
        CREATE TEMP TABLE _norm_soldiers AS
        SELECT
            soldier_id,
            UPPER(TRIM(surname)) AS s_surname,
            REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                UPPER(IFNULL(initials,'')),
                '.',''), ' ',''), '-',''), '''',''), '/','') AS s_initials,
            REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                UPPER(IFNULL(service_number,'')),
                '.',''), ' ',''), '-',''), '''',''), '/','') AS s_service_number,
            TRIM(UPPER(IFNULL(christian_names,''))) AS s_christian,
            death_date AS s_death_date
        FROM soldiers
        WHERE surname IS NOT NULL;
    """)
    cur.execute("CREATE INDEX _ns_s_dod ON _norm_soldiers(s_surname, s_death_date);")
    cur.execute("CREATE INDEX _ns_si_d  ON _norm_soldiers(s_surname, s_initials, s_death_date);")
    cur.execute("CREATE INDEX _ns_siss  ON _norm_soldiers(s_surname, s_initials, s_service_number, s_death_date);")

    log("  building _norm_officers ...")
    cur.execute("DROP TABLE IF EXISTS _norm_officers;")
    cur.execute("""
        CREATE TEMP TABLE _norm_officers AS
        SELECT
            officer_id,
            UPPER(TRIM(surname)) AS o_surname,
            REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                UPPER(IFNULL(initials,'')),
                '.',''), ' ',''), '-',''), '''',''), '/','') AS o_initials,
            TRIM(UPPER(IFNULL(christian_names,''))) AS o_christian,
            death_date AS o_death_date
        FROM officers
        WHERE surname IS NOT NULL;
    """)
    cur.execute("CREATE INDEX _no_s_dod ON _norm_officers(o_surname, o_death_date);")
    cur.execute("CREATE INDEX _no_si_d  ON _norm_officers(o_surname, o_initials, o_death_date);")

    log("  building _norm_cwgc ...")
    cur.execute("DROP TABLE IF EXISTS _norm_cwgc;")
    cur.execute("""
        CREATE TEMP TABLE _norm_cwgc AS
        SELECT
            cwgc_id,
            UPPER(TRIM(surname)) AS c_surname,
            REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                UPPER(IFNULL(initials,'')),
                '.',''), ' ',''), '-',''), '''',''), '/','') AS c_initials,
            REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                UPPER(IFNULL(service_number,'')),
                '.',''), ' ',''), '-',''), '''',''), '/','') AS c_service_number,
            TRIM(UPPER(IFNULL(forename,''))) AS c_forename,
            date_of_death AS c_death_date
        FROM cwgc_records
        WHERE surname IS NOT NULL;
    """)
    cur.execute("CREATE INDEX _nc_s_dod ON _norm_cwgc(c_surname, c_death_date);")
    cur.execute("CREATE INDEX _nc_si_d  ON _norm_cwgc(c_surname, c_initials, c_death_date);")
    cur.execute("CREATE INDEX _nc_siss  ON _norm_cwgc(c_surname, c_initials, c_service_number, c_death_date);")
    con.commit()


# ---------------------------------------------------------------------------
# Matching layers
# ---------------------------------------------------------------------------
def layer_exact(con: sqlite3.Connection) -> int:
    """Soldiers only. Surname + initials + service# + death_date all non-empty."""
    cur = con.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO cwgc_match
            (cwgc_id, record_type, record_id, confidence, match_reason)
        SELECT c.cwgc_id, 'soldier', s.soldier_id, 'exact',
               'surname+initials+service_number+death_date'
        FROM _norm_cwgc c
        JOIN _norm_soldiers s
          ON s.s_surname = c.c_surname
         AND s.s_initials = c.c_initials AND length(s.s_initials) > 0
         AND s.s_service_number = c.c_service_number AND length(s.s_service_number) > 0
         AND s.s_death_date = c.c_death_date AND s.s_death_date IS NOT NULL;
    """)
    n = cur.rowcount
    con.commit()
    return n


def layer_high_soldiers(con: sqlite3.Connection) -> int:
    """Soldiers. Surname + initials + death_date, 1:1 unambiguous.

    "1:1 unambiguous": the (surname, initials, death_date) tuple maps to
    exactly one soldier AND exactly one CWGC record. Anything else falls
    through to the MEDIUM layer.
    """
    cur = con.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO cwgc_match
            (cwgc_id, record_type, record_id, confidence, match_reason)
        WITH soldier_unique AS (
            SELECT s_surname, s_initials, s_death_date,
                   MIN(soldier_id) AS soldier_id, COUNT(*) AS n
            FROM _norm_soldiers
            WHERE length(s_initials) > 0 AND s_death_date IS NOT NULL
            GROUP BY s_surname, s_initials, s_death_date
            HAVING COUNT(*) = 1
        ),
        cwgc_unique AS (
            SELECT c_surname, c_initials, c_death_date,
                   MIN(cwgc_id) AS cwgc_id, COUNT(*) AS n
            FROM _norm_cwgc
            WHERE length(c_initials) > 0 AND c_death_date IS NOT NULL
            GROUP BY c_surname, c_initials, c_death_date
            HAVING COUNT(*) = 1
        )
        SELECT c.cwgc_id, 'soldier', s.soldier_id, 'high',
               'unique surname+initials+death_date'
        FROM cwgc_unique c
        JOIN soldier_unique s
          ON s.s_surname = c.c_surname
         AND s.s_initials = c.c_initials
         AND s.s_death_date = c.c_death_date;
    """)
    n = cur.rowcount
    con.commit()
    return n


def layer_high_officers(con: sqlite3.Connection) -> int:
    """Officers. Surname + initials + death_date, 1:1 unambiguous."""
    cur = con.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO cwgc_match
            (cwgc_id, record_type, record_id, confidence, match_reason)
        WITH officer_unique AS (
            SELECT o_surname, o_initials, o_death_date,
                   MIN(officer_id) AS officer_id, COUNT(*) AS n
            FROM _norm_officers
            WHERE length(o_initials) > 0 AND o_death_date IS NOT NULL
            GROUP BY o_surname, o_initials, o_death_date
            HAVING COUNT(*) = 1
        ),
        cwgc_unique AS (
            SELECT c_surname, c_initials, c_death_date,
                   MIN(cwgc_id) AS cwgc_id, COUNT(*) AS n
            FROM _norm_cwgc
            WHERE length(c_initials) > 0 AND c_death_date IS NOT NULL
            GROUP BY c_surname, c_initials, c_death_date
            HAVING COUNT(*) = 1
        )
        SELECT c.cwgc_id, 'officer', o.officer_id, 'high',
               'unique surname+initials+death_date'
        FROM cwgc_unique c
        JOIN officer_unique o
          ON o.o_surname = c.c_surname
         AND o.o_initials = c.c_initials
         AND o.o_death_date = c.c_death_date;
    """)
    n = cur.rowcount
    con.commit()
    return n


def layer_medium_soldiers(con: sqlite3.Connection) -> int:
    """Soldiers. Surname + christian_names + death_date. Candidates for review."""
    cur = con.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO cwgc_match
            (cwgc_id, record_type, record_id, confidence, match_reason)
        SELECT c.cwgc_id, 'soldier', s.soldier_id, 'medium',
               'surname+christian_names+death_date'
        FROM _norm_cwgc c
        JOIN _norm_soldiers s
          ON s.s_surname = c.c_surname
         AND length(s.s_christian) > 0 AND s.s_christian = c.c_forename
         AND s.s_death_date = c.c_death_date AND s.s_death_date IS NOT NULL;
    """)
    n = cur.rowcount
    con.commit()
    return n


def layer_medium_officers(con: sqlite3.Connection) -> int:
    """Officers. Surname + christian_names + death_date. Candidates for review."""
    cur = con.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO cwgc_match
            (cwgc_id, record_type, record_id, confidence, match_reason)
        SELECT c.cwgc_id, 'officer', o.officer_id, 'medium',
               'surname+christian_names+death_date'
        FROM _norm_cwgc c
        JOIN _norm_officers o
          ON o.o_surname = c.c_surname
         AND length(o.o_christian) > 0 AND o.o_christian = c.c_forename
         AND o.o_death_date = c.c_death_date AND o.o_death_date IS NOT NULL;
    """)
    n = cur.rowcount
    con.commit()
    return n


LAYER_FN = {
    "exact":      ("EXACT  (soldiers)", layer_exact),
    "high":       ("HIGH   (soldiers)", layer_high_soldiers),
    "high-off":   ("HIGH   (officers)", layer_high_officers),
    "medium":     ("MEDIUM (soldiers)", layer_medium_soldiers),
    "medium-off": ("MEDIUM (officers)", layer_medium_officers),
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="CWGC matcher: populates cwgc_match")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--reset", action="store_true",
                        help="Soft-delete auto-generated cwgc_match rows (sets is_active=0). "
                             "Rows with confidence='manual' are PRESERVED so operator "
                             "confirmations survive a re-match.")
    parser.add_argument("--hard-reset", action="store_true",
                        help="DELETE all rows from cwgc_match including manual confirmations. "
                             "Use only when there are no manual matches yet (testing / first runs).")
    parser.add_argument("--layers", nargs="+", choices=ALL_LAYERS, default=ALL_LAYERS,
                        help="Layers to run (default: all)")
    args = parser.parse_args()

    if not args.db.exists():
        log(f"ERROR: database not found: {args.db}")
        return 2

    con = sqlite3.connect(str(args.db))
    try:
        con.execute("PRAGMA journal_mode = WAL;")
        con.execute("PRAGMA synchronous = NORMAL;")
        con.execute("PRAGMA temp_store = MEMORY;")

        # Sanity: tables exist
        row = con.execute(
            "SELECT COUNT(*) FROM sqlite_master "
            "WHERE type='table' AND name IN ('cwgc_records','cwgc_match');"
        ).fetchone()
        if row[0] != 2:
            log("ERROR: cwgc_records or cwgc_match missing. "
                "Run src/scripts/cwgc_schema_migrate.py first.")
            return 2

        # Reset modes
        if args.hard_reset:
            log("hard-resetting cwgc_match (DELETE all rows)")
            con.execute("DELETE FROM cwgc_match;")
            con.commit()
        elif args.reset:
            log("soft-resetting cwgc_match (is_active=0 on auto-generated rows; manual matches preserved)")
            con.execute(
                "UPDATE cwgc_match SET is_active=0 "
                "WHERE is_active=1 AND confidence != 'manual';"
            )
            con.commit()

        log(f"DB: {args.db}")
        log(f"layers: {', '.join(args.layers)}")

        cwgc_n = con.execute("SELECT COUNT(*) FROM cwgc_records").fetchone()[0]
        log(f"cwgc_records      : {cwgc_n:,}")
        before = con.execute(
            "SELECT COUNT(*) FROM cwgc_match WHERE is_active=1"
        ).fetchone()[0]
        log(f"cwgc_match before : {before:,} active rows")

        t0 = time.time()
        build_temp_tables(con)
        log(f"  temp tables built in {time.time()-t0:.1f}s")

        per_layer: dict[str, int] = {}
        for layer in args.layers:
            label, fn = LAYER_FN[layer]
            t = time.time()
            n = fn(con)
            per_layer[layer] = n
            log(f"  layer {label}: +{n:,} new rows ({time.time()-t:.1f}s)")

        after = con.execute(
            "SELECT COUNT(*) FROM cwgc_match WHERE is_active=1"
        ).fetchone()[0]

        log("=== Match summary ===")
        log(f"  cwgc_records           : {cwgc_n:,}")
        log(f"  cwgc_match before      : {before:,}")
        log(f"  cwgc_match after       : {after:,}")
        log(f"  net new active rows    : {after - before:,}")
        for layer in args.layers:
            label, _ = LAYER_FN[layer]
            log(f"  {label:24s}: +{per_layer[layer]:,}")
        log(f"  total runtime          : {time.time()-t0:.1f}s")
        log("DONE")
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main())
