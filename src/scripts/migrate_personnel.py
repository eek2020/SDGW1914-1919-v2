#!/usr/bin/env python3
"""
Migrate all CSV exports into the SQLite database.

Usage:
    python src/scripts/migrate_personnel.py [--export-dir DIR] [--db-path PATH] [--schema PATH]
"""

import argparse
import logging
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_migration import DataMigrator


def setup_logging():
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)-5s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "migration.log"),
        ],
    )


def main():
    parser = argparse.ArgumentParser(description="Migrate SDGW CSV data to SQLite")
    parser.add_argument(
        "--export-dir",
        default=str(project_root / "data" / "exports"),
        help="Directory containing CSV exports",
    )
    parser.add_argument(
        "--db-path",
        default=str(project_root / "data" / "sd_2011.db"),
        help="Path for the SQLite database",
    )
    parser.add_argument(
        "--schema",
        default=str(project_root / "src" / "schema.sql"),
        help="Path to the schema SQL file",
    )
    args = parser.parse_args()

    setup_logging()

    print("=" * 70)
    print("SDGW 1914-1919 DATA MIGRATION")
    print("=" * 70)

    # Remove existing database if present
    db_path = Path(args.db_path)
    if db_path.exists():
        print(f"\nRemoving existing database: {db_path.name}")
        db_path.unlink()

    try:
        migrator = DataMigrator(args.db_path, args.schema)
    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

    print(f"\nSource: {args.export_dir}")
    print(f"Target: {args.db_path}")
    print(f"Schema: {args.schema}")

    report = migrator.run_full_migration(args.export_dir)

    # Print results
    print("\n" + "=" * 70)
    print("MIGRATION SUMMARY")
    print("=" * 70)

    for table_name, result in report.results.items():
        status = "OK" if result.success else "FAIL"
        print(
            f"  {status}  {table_name:<25s} "
            f"{result.rows_loaded:>10,} loaded  "
            f"{result.rows_skipped:>5} skipped  "
            f"{result.duration_seconds:>6.1f}s"
        )
        if result.errors:
            for err in result.errors[:3]:
                print(f"       Error: {err}")
            if len(result.errors) > 3:
                print(f"       ... and {len(result.errors) - 3} more errors")

    print("-" * 70)
    print(
        f"  Total: {report.total_rows_loaded:,} rows loaded, "
        f"{report.total_rows_skipped} skipped, "
        f"{report.total_errors} errors "
        f"in {report.duration_seconds:.1f}s"
    )

    # Database file size
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"  Database size: {size_mb:.1f} MB")

    overall = "MIGRATION SUCCESSFUL" if report.all_success else "MIGRATION COMPLETED WITH ERRORS"
    print(f"\nSTATUS: {overall}")

    sys.exit(0 if report.all_success else 1)


if __name__ == "__main__":
    main()
