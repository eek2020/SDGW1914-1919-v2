#!/usr/bin/env python3
"""
CWGC CSV Importer (cwgc_records target)

Imports one or more CWGC casualty CSVs into the `cwgc_records` table.
The CSVs are produced by `src/scripts/cwgc_download.py` and use the
native CWGC export column order:

    Id, Surname, Forename, Initials, AgeAtDeath, Honours,
    DateOfDeath, DateOfDeath2, Rank, Regiment, SecondaryRegiment,
    Unit, SecondaryUnit, CountryOfService, ServiceNumber,
    Burial, Cemetery, GraveRef, AdditionalInfo

Behaviour:
  * Idempotent — uses INSERT OR REPLACE keyed on cwgc_id. Re-running
    against the same files updates rows without duplicates.
  * Date format: DD/MM/YYYY -> YYYY-MM-DD (ISO). Empty/invalid -> NULL.
  * Constructs `cwgc_url` from the cwgc_id automatically.
  * Assumes the schema has been migrated already (see
    `src/scripts/cwgc_schema_migrate.py`). Fails fast if the table is
    missing.

Usage:
    python3 src/scripts/cwgc_import.py
    python3 src/scripts/cwgc_import.py --db data/sd_2011.db --input data/cwgc_batches
    python3 src/scripts/cwgc_import.py --input data/cwgc_batches data/source
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_DB = Path("data/sd_2011.db")
DEFAULT_INPUTS = [Path("data/cwgc_batches"), Path("data/source")]
CWGC_URL_TEMPLATE = "https://www.cwgc.org/find-records/find-war-dead/casualty/{cwgc_id}/"

EXPECTED_HEADER = [
    "Id", "Surname", "Forename", "Initials", "AgeAtDeath", "Honours",
    "DateOfDeath", "DateOfDeath2", "Rank", "Regiment", "SecondaryRegiment",
    "Unit", "SecondaryUnit", "CountryOfService", "ServiceNumber",
    "Burial", "Cemetery", "GraveRef", "AdditionalInfo",
]

# INSERT OR REPLACE is intentional: re-running with newer CSVs refreshes
# existing rows in place. cwgc_records is logically immutable per-import,
# but we want easy updates when CWGC re-publishes corrections.
UPSERT_SQL = """
INSERT OR REPLACE INTO cwgc_records (
    cwgc_id, surname, forename, initials, age_at_death, honours,
    date_of_death, date_of_death2, rank, regiment, secondary_regiment,
    unit, secondary_unit, country_of_service, service_number,
    burial, cemetery, grave_ref, additional_info, cwgc_url, imported_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
"""


def log(msg: str) -> None:
    print(f"[cwgc_import] {msg}", flush=True)


def parse_date(value: str) -> str | None:
    """DD/MM/YYYY -> YYYY-MM-DD. Returns None for empty/invalid input."""
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_int(value: str) -> int | None:
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def clean(value: str) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def strip_quoted_number(value: str | None) -> str | None:
    """CWGC writes service numbers with surrounding single quotes (e.g. "'620'")
    to defeat Excel's number coercion. Strip those off for storage."""
    if value is None:
        return None
    if len(value) >= 2 and value[0] == "'" and value[-1] == "'":
        value = value[1:-1]
    return value or None


def iter_csv_rows(path: Path):
    """Yield row tuples ready for UPSERT_SQL."""
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        if not header:
            return
        if header[: len(EXPECTED_HEADER)] != EXPECTED_HEADER:
            log(f"WARNING header mismatch in {path.name}; trying anyway")
        for row in reader:
            if len(row) < len(EXPECTED_HEADER):
                row = row + [""] * (len(EXPECTED_HEADER) - len(row))
            elif len(row) > len(EXPECTED_HEADER):
                row = row[: len(EXPECTED_HEADER)]
            (_id, surname, forename, initials, age, honours,
             dod, dod2, rank, regiment, sec_regiment,
             unit, sec_unit, country, service_no,
             burial, cemetery, grave_ref, additional) = row
            cwgc_id = parse_int(_id)
            if cwgc_id is None:
                continue
            yield (
                cwgc_id,
                clean(surname),
                clean(forename),
                clean(initials),
                parse_int(age),
                clean(honours),
                parse_date(dod),
                parse_date(dod2),
                clean(rank),
                clean(regiment),
                clean(sec_regiment),
                clean(unit),
                clean(sec_unit),
                clean(country),
                strip_quoted_number(clean(service_no)),
                clean(burial),
                clean(cemetery),
                clean(grave_ref),
                clean(additional),
                CWGC_URL_TEMPLATE.format(cwgc_id=cwgc_id),
            )


def discover_csvs(inputs: list[Path]) -> list[Path]:
    found: list[Path] = []
    for entry in inputs:
        if not entry.exists():
            continue
        if entry.is_file() and entry.suffix.lower() == ".csv":
            found.append(entry)
        elif entry.is_dir():
            found.extend(sorted(entry.rglob("*.csv")))
    # dedupe preserving order
    seen: set[Path] = set()
    unique: list[Path] = []
    for p in found:
        rp = p.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        unique.append(p)
    return unique


def assert_schema(con: sqlite3.Connection) -> None:
    cur = con.cursor()
    row = cur.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='cwgc_records'"
    ).fetchone()
    if not row or row[0] != 1:
        raise SystemExit(
            "ERROR: cwgc_records table not found. "
            "Run: python3 src/scripts/cwgc_schema_migrate.py first."
        )


def import_csvs(db_path: Path, csv_paths: list[Path], batch_size: int) -> dict:
    con = sqlite3.connect(str(db_path))
    try:
        # Performance pragmas — safe to set per-connection
        con.execute("PRAGMA journal_mode = WAL;")
        con.execute("PRAGMA synchronous = NORMAL;")
        con.execute("PRAGMA temp_store = MEMORY;")
        assert_schema(con)

        before = con.execute("SELECT COUNT(*) FROM cwgc_records").fetchone()[0]
        log(f"rows in cwgc_records BEFORE: {before:,}")

        cur = con.cursor()
        total_in = 0
        total_buffered = 0
        buf: list[tuple] = []

        for csv_path in csv_paths:
            file_in = 0
            for row in iter_csv_rows(csv_path):
                buf.append(row)
                file_in += 1
                total_in += 1
                if len(buf) >= batch_size:
                    cur.executemany(UPSERT_SQL, buf)
                    total_buffered += len(buf)
                    buf.clear()
            log(f"  {csv_path.name}: {file_in:,} rows queued")

        if buf:
            cur.executemany(UPSERT_SQL, buf)
            total_buffered += len(buf)
            buf.clear()

        con.commit()
        after = con.execute("SELECT COUNT(*) FROM cwgc_records").fetchone()[0]

        return {
            "files": len(csv_paths),
            "rows_read": total_in,
            "rows_upserted": total_buffered,
            "rows_before": before,
            "rows_after": after,
            "rows_added": after - before,
        }
    finally:
        con.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Import CWGC casualty CSVs into cwgc_records")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB,
                        help=f"Target SQLite database (default: {DEFAULT_DB})")
    parser.add_argument("--input", nargs="+", type=Path, default=DEFAULT_INPUTS,
                        help="CSV files or directories (default: data/cwgc_batches data/source)")
    parser.add_argument("--batch-size", type=int, default=5000,
                        help="UPSERT batch size (default: 5000)")
    args = parser.parse_args()

    if not args.db.exists():
        log(f"ERROR: database not found: {args.db}")
        return 2

    csv_paths = discover_csvs(args.input)
    if not csv_paths:
        log(f"ERROR: no CSV files found under: {args.input}")
        return 2

    log(f"DB    : {args.db}")
    log(f"CSVs  : {len(csv_paths):,} files")

    stats = import_csvs(args.db, csv_paths, args.batch_size)

    log("=== Import summary ===")
    log(f"  files imported       : {stats['files']:,}")
    log(f"  CSV rows read        : {stats['rows_read']:,}")
    log(f"  rows UPSERTed        : {stats['rows_upserted']:,}")
    log(f"  cwgc_records before  : {stats['rows_before']:,}")
    log(f"  cwgc_records after   : {stats['rows_after']:,}")
    log(f"  rows added (new IDs) : {stats['rows_added']:,}")
    log("DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
