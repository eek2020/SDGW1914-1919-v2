#!/usr/bin/env python3
"""
Validate the migrated SQLite database against expected row counts
and data integrity constraints.

Usage:
    python src/scripts/validate_migration.py [--db-path PATH]
"""

import argparse
import logging
import sqlite3
import sys
import time
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


def setup_logging():
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)-5s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "validation.log"),
        ],
    )


EXPECTED_COUNTS = {
    "ranks": 547,
    "battalions_sd": 721,
    "battalions_od": 480,
    "regiment_battalion_sd": 1987,
    "regiment_battalion_od": 1662,
    "officers": 41846,
    "soldiers": 661960,
}


def check_row_counts(conn):
    """Verify row counts match expected values."""
    print("\n  ROW COUNTS")
    print("  " + "-" * 50)
    all_pass = True
    total = 0

    for table, expected in EXPECTED_COUNTS.items():
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
        actual = cursor.fetchone()[0]
        total += actual
        match = actual == expected
        status = "OK" if match else "FAIL"
        print(f"    {status}  {table:<28s} {actual:>10,} (expected {expected:,})")
        if not match:
            all_pass = False

    print(f"    {'':4s} {'TOTAL':<28s} {total:>10,}")
    return all_pass


def check_null_constraints(conn):
    """Check that required fields are not null."""
    print("\n  NULL CONSTRAINTS")
    print("  " + "-" * 50)
    all_pass = True

    checks = [
        ("officers", "surname", 0),
        ("officers", "battalion_id", 0),
        ("soldiers", "surname", 0),
        ("soldiers", "battalion_id", 0),
        ("ranks", "rank_group", 0),
        ("ranks", "rank_new", 0),
    ]

    for table, column, max_nulls in checks:
        cursor = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL"
        )
        null_count = cursor.fetchone()[0]
        ok = null_count <= max_nulls
        status = "OK" if ok else "FAIL"
        print(f"    {status}  {table}.{column}: {null_count} nulls (max allowed: {max_nulls})")
        if not ok:
            all_pass = False

    return all_pass


def check_date_parsing(conn):
    """Verify death dates were parsed correctly."""
    print("\n  DATE PARSING")
    print("  " + "-" * 50)
    all_pass = True

    for table in ("officers", "soldiers"):
        # Count records with raw date but no parsed date
        cursor = conn.execute(
            f"""SELECT COUNT(*) FROM {table}
                WHERE death_date_raw IS NOT NULL
                AND death_date_raw != ''
                AND death_date IS NULL"""
        )
        unparsed = cursor.fetchone()[0]

        cursor = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE death_date IS NOT NULL"
        )
        parsed = cursor.fetchone()[0]

        cursor = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE death_date_raw IS NOT NULL AND death_date_raw != ''"
        )
        with_raw = cursor.fetchone()[0]

        parse_rate = (parsed / with_raw * 100) if with_raw > 0 else 0
        status = "OK" if unparsed == 0 else "WARN"
        print(
            f"    {status}  {table}: {parsed:,} parsed / {with_raw:,} with raw date "
            f"({parse_rate:.1f}%), {unparsed} unparsed"
        )

        # Check date range is reasonable (1914-1921)
        cursor = conn.execute(
            f"""SELECT COUNT(*) FROM {table}
                WHERE death_date IS NOT NULL
                AND (death_date < '1914-01-01' OR death_date > '1921-12-31')"""
        )
        out_of_range = cursor.fetchone()[0]
        status2 = "OK" if out_of_range == 0 else "WARN"
        print(f"    {status2}  {table}: {out_of_range} dates outside 1914-1921 range")

        if unparsed > 0 or out_of_range > 0:
            all_pass = False

    return all_pass


def check_search_performance(conn):
    """Benchmark multi-parameter search queries."""
    print("\n  SEARCH PERFORMANCE")
    print("  " + "-" * 50)
    all_pass = True

    queries = [
        ("Surname lookup (SMITH)", "SELECT COUNT(*) FROM soldiers WHERE surname = 'SMITH'"),
        ("Surname prefix (SMI%)", "SELECT COUNT(*) FROM soldiers WHERE surname LIKE 'SMI%'"),
        ("Battalion filter", "SELECT COUNT(*) FROM soldiers WHERE battalion_id = 1"),
        ("Rank filter", "SELECT COUNT(*) FROM soldiers WHERE rank_id = 1"),
        ("Birth town search", "SELECT COUNT(*) FROM soldiers WHERE birth_town = 'LONDON'"),
        ("Death location filter", "SELECT COUNT(*) FROM soldiers WHERE death_location = 'France & Flanders'"),
        ("Date range query", "SELECT COUNT(*) FROM soldiers WHERE death_date BETWEEN '1916-07-01' AND '1916-07-31'"),
        (
            "Multi-param: surname+battalion",
            "SELECT COUNT(*) FROM soldiers WHERE surname = 'SMITH' AND battalion_id = 1",
        ),
        (
            "Multi-param: surname+rank+date",
            "SELECT COUNT(*) FROM soldiers WHERE surname LIKE 'SM%' AND rank_id = 1 AND death_date > '1916-01-01'",
        ),
        (
            "Join: soldiers+ranks",
            "SELECT COUNT(*) FROM soldiers s JOIN ranks r ON s.rank_id = r.rank_id WHERE r.rank_group = 'Privates'",
        ),
        (
            "Join: officers+battalions",
            "SELECT COUNT(*) FROM officers o JOIN battalions_sd b ON o.battalion_id = b.battalion_id WHERE o.surname = 'SMITH'",
        ),
    ]

    for label, sql in queries:
        start = time.time()
        cursor = conn.execute(sql)
        result = cursor.fetchone()[0]
        elapsed_ms = (time.time() - start) * 1000
        ok = elapsed_ms < 1000  # Under 1 second
        status = "OK" if ok else "SLOW"
        print(f"    {status}  {label:<40s} {result:>10,} results  {elapsed_ms:>7.1f}ms")
        if not ok:
            all_pass = False

    return all_pass


def check_data_samples(conn):
    """Spot-check a few known records."""
    print("\n  SPOT CHECKS")
    print("  " + "-" * 50)
    all_pass = True

    # Check first officer record (ADAMSON from our sample data)
    cursor = conn.execute("SELECT surname, rank_text, death_date FROM officers WHERE officer_id = 1")
    row = cursor.fetchone()
    if row:
        ok = row[0] == "ADAMSON"
        status = "OK" if ok else "FAIL"
        print(f"    {status}  Officer #1: {row[0]}, {row[1]}, death={row[2]}")
        if not ok:
            all_pass = False
    else:
        print("    FAIL  Officer #1: not found")
        all_pass = False

    # Check first soldier record (AINSLIE)
    cursor = conn.execute(
        "SELECT surname, service_number, birth_town, death_location FROM soldiers WHERE soldier_id = 1"
    )
    row = cursor.fetchone()
    if row:
        ok = row[0] == "AINSLIE"
        status = "OK" if ok else "FAIL"
        print(f"    {status}  Soldier #1: {row[0]}, svc#{row[1]}, born={row[2]}, died={row[3]}")
        if not ok:
            all_pass = False
    else:
        print("    FAIL  Soldier #1: not found")
        all_pass = False

    # Check rank reference integrity
    cursor = conn.execute(
        "SELECT COUNT(*) FROM soldiers WHERE rank_id IS NOT NULL AND rank_id NOT IN (SELECT rank_id FROM ranks)"
    )
    orphaned_ranks = cursor.fetchone()[0]
    status = "OK" if orphaned_ranks == 0 else "WARN"
    print(f"    {status}  Orphaned soldier rank references: {orphaned_ranks}")

    cursor = conn.execute(
        "SELECT COUNT(*) FROM officers WHERE rank_id IS NOT NULL AND rank_id NOT IN (SELECT rank_id FROM ranks)"
    )
    orphaned_officer_ranks = cursor.fetchone()[0]
    status = "OK" if orphaned_officer_ranks == 0 else "WARN"
    print(f"    {status}  Orphaned officer rank references: {orphaned_officer_ranks}")

    return all_pass


def main():
    parser = argparse.ArgumentParser(description="Validate SDGW migration")
    parser.add_argument(
        "--db-path",
        default=str(project_root / "data" / "sd_2011.db"),
        help="Path to the SQLite database",
    )
    args = parser.parse_args()

    setup_logging()

    print("=" * 70)
    print("SDGW 1914-1919 MIGRATION VALIDATION REPORT")
    print("=" * 70)

    db_path = Path(args.db_path)
    if not db_path.exists():
        print(f"\nERROR: Database not found: {db_path}")
        sys.exit(1)

    size_mb = db_path.stat().st_size / (1024 * 1024)
    print(f"\nDatabase: {db_path}")
    print(f"Size: {size_mb:.1f} MB")

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys=ON")

    results = {}
    results["row_counts"] = check_row_counts(conn)
    results["null_constraints"] = check_null_constraints(conn)
    results["date_parsing"] = check_date_parsing(conn)
    results["search_performance"] = check_search_performance(conn)
    results["spot_checks"] = check_data_samples(conn)

    conn.close()

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    all_pass = True
    for check_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {status}  {check_name}")
        if not passed:
            all_pass = False

    overall = "ALL CHECKS PASSED" if all_pass else "SOME CHECKS FAILED"
    print(f"\nCONCLUSION: {overall}")
    print("=" * 70)

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
