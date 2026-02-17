#!/usr/bin/env python3
"""
Validate exported CSV files against the source MDB database.

Usage:
    python src/scripts/validate_export.py [--db-path PATH] [--export-dir DIR]
"""

import argparse
import logging
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_access import DataExtractor


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


def main():
    parser = argparse.ArgumentParser(description="Validate SDGW CSV exports")
    parser.add_argument(
        "--db-path",
        default=str(project_root / "data" / "sd_2011.mdb"),
        help="Path to the MDB database file",
    )
    parser.add_argument(
        "--export-dir",
        default=str(project_root / "data" / "exports"),
        help="Directory containing CSV exports",
    )
    args = parser.parse_args()

    setup_logging()

    print("=" * 70)
    print("SDGW 1914-1919 EXPORT VALIDATION REPORT")
    print("=" * 70)

    try:
        extractor = DataExtractor(args.db_path)
    except (FileNotFoundError, EnvironmentError) as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

    report = extractor.validate_export(args.export_dir)

    print(f"\nDate: {report.timestamp}")
    print(f"Tables Checked: {report.tables_checked}")
    print(f"Total Rows: {report.total_rows_validated:,}")

    print("\n" + "-" * 70)
    print("DETAILED RESULTS")
    print("-" * 70)

    for tv in report.table_results:
        status = "PASS" if (tv.row_count_match and tv.spot_check_passed) else "FAIL"
        print(f"\n  {status}  {tv.table_name}")
        print(f"       Rows: {tv.actual_rows:,} (expected {tv.expected_rows:,})")
        print(f"       Columns: {tv.actual_columns}")
        print(f"       Row count match: {tv.row_count_match}")
        print(f"       Spot checks: {tv.spot_check_passed}")
        for detail in tv.spot_check_details:
            print(f"         - {detail}")

    if report.errors:
        print("\n" + "-" * 70)
        print("ERRORS")
        print("-" * 70)
        for err in report.errors:
            print(f"  - {err}")

    if report.warnings:
        print("\n" + "-" * 70)
        print("WARNINGS")
        print("-" * 70)
        for warn in report.warnings:
            print(f"  - {warn}")

    print("\n" + "=" * 70)
    overall = "PASSED" if report.all_pass else "FAILED"
    print(f"CONCLUSION: Validation {overall}")
    print("=" * 70)

    sys.exit(0 if report.all_pass else 1)


if __name__ == "__main__":
    main()
