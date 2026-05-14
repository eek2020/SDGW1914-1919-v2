#!/usr/bin/env python3
"""
CWGC Schema Migration

Applies src/sql/cwgc_schema.sql to a target SQLite database. Creates a
timestamped backup first. Idempotent — every statement in the DDL is
IF NOT EXISTS, so running this repeatedly is safe.

Usage:
    python3 src/scripts/cwgc_schema_migrate.py                       # default: data/sd_2011.db
    python3 src/scripts/cwgc_schema_migrate.py --db /some/other.db
    python3 src/scripts/cwgc_schema_migrate.py --no-backup            # skip backup (CI/disposable DBs)
    python3 src/scripts/cwgc_schema_migrate.py --dry-run              # print what would happen

The migration does NOT modify the `soldiers` or `officers` tables. Per
CLAUDE.md §6.1 (Hard Constraints), the original historical records are
immutable. CWGC enrichment lives in new tables only:
    - cwgc_records      (new table)
    - cwgc_match        (new table)
    - soldiers_with_cwgc, officers_with_cwgc, v_cwgc_match_candidates,
      v_cwgc_unmatched  (new views)
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_DB = Path("data/sd_2011.db")
SCHEMA_FILE = Path("src/sql/cwgc_schema.sql")


def log(msg: str) -> None:
    print(f"[cwgc_schema_migrate] {msg}", flush=True)


def make_backup(db_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    backup = db_path.with_name(f"{db_path.name}.pre-cwgc-{stamp}.bak")
    log(f"backing up to {backup}")
    # Use sqlite3.Connection.backup for WAL safety
    src = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    dst = sqlite3.connect(str(backup))
    src.backup(dst)
    src.close()
    dst.close()
    log(f"backup complete ({backup.stat().st_size:,} bytes)")
    return backup


def apply_schema(db_path: Path, sql_text: str, dry_run: bool) -> None:
    log(f"opening {db_path}")
    con = sqlite3.connect(str(db_path))
    try:
        con.execute("PRAGMA foreign_keys = ON;")
        if dry_run:
            log("--- DRY RUN ---")
            log(sql_text)
            return
        log("applying schema (transactional)")
        with con:
            con.executescript(sql_text)
        log("schema applied")

        # Quick sanity checks
        cur = con.cursor()
        for tbl in ("cwgc_records", "cwgc_match"):
            row = cur.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
                (tbl,),
            ).fetchone()
            assert row[0] == 1, f"expected table {tbl} to exist"
            log(f"  table {tbl}: present")
        for view in ("soldiers_with_cwgc", "officers_with_cwgc",
                     "v_cwgc_match_candidates", "v_cwgc_unmatched"):
            row = cur.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='view' AND name=?",
                (view,),
            ).fetchone()
            assert row[0] == 1, f"expected view {view} to exist"
            log(f"  view {view}: present")

        # Confirm we haven't accidentally touched soldiers/officers
        cur.execute("SELECT COUNT(*) FROM soldiers;")
        soldiers = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM officers;")
        officers = cur.fetchone()[0]
        log(f"  soldiers row count: {soldiers:,}")
        log(f"  officers row count: {officers:,}")
    finally:
        con.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB,
                        help=f"Target SQLite database (default: {DEFAULT_DB})")
    parser.add_argument("--schema", type=Path, default=SCHEMA_FILE,
                        help=f"Schema SQL file (default: {SCHEMA_FILE})")
    parser.add_argument("--no-backup", action="store_true",
                        help="Skip the timestamped backup (use only for disposable DBs)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the SQL but don't apply it")
    args = parser.parse_args()

    if not args.db.exists():
        log(f"ERROR: database not found: {args.db}")
        return 2
    if not args.schema.exists():
        log(f"ERROR: schema file not found: {args.schema}")
        return 2

    sql_text = args.schema.read_text(encoding="utf-8")
    log(f"DB     : {args.db}")
    log(f"Schema : {args.schema} ({len(sql_text):,} chars)")

    if not args.no_backup and not args.dry_run:
        make_backup(args.db)

    apply_schema(args.db, sql_text, args.dry_run)
    log("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
