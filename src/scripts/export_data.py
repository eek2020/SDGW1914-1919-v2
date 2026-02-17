#!/usr/bin/env python3
"""
Export all tables from the SDGW 1914-1919 MDB database to CSV files.

Usage:
    python src/scripts/export_data.py [--db-path PATH] [--output-dir DIR] [--skip-backup]
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
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
            logging.FileHandler(log_dir / "data_access.log"),
        ],
    )


def main():
    parser = argparse.ArgumentParser(description="Export SDGW database tables to CSV")
    parser.add_argument(
        "--db-path",
        default=str(project_root / "data" / "sd_2011.mdb"),
        help="Path to the MDB database file",
    )
    parser.add_argument(
        "--output-dir",
        default=str(project_root / "data" / "exports"),
        help="Directory for CSV output files",
    )
    parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="Skip creating a backup before export",
    )
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger("sdgw.export")

    print("=" * 70)
    print("SDGW 1914-1919 DATA EXPORT")
    print("=" * 70)

    try:
        extractor = DataExtractor(args.db_path)
    except (FileNotFoundError, EnvironmentError) as e:
        logger.error(str(e))
        print(f"\nERROR: {e}")
        sys.exit(1)

    # Backup
    if not args.skip_backup:
        print("\nStep 1: Creating backup...")
        backup_dir = str(project_root / "data" / "backups")
        backup = extractor.create_backup(backup_dir)
        if backup.success:
            print(f"  Backup created: {Path(backup.backup_path).name}")
            print(f"  Size: {backup.backup_size / (1024*1024):.1f} MB (match: {backup.size_match})")
        else:
            print(f"  WARNING: Backup failed: {backup.error}")
            logger.warning("Backup failed, continuing with export: %s", backup.error)
    else:
        print("\nStep 1: Backup skipped (--skip-backup)")

    # Export
    print(f"\nStep 2: Exporting tables to {args.output_dir}...")
    results = extractor.export_all(args.output_dir)

    # Summary
    print("\n" + "=" * 70)
    print("EXPORT SUMMARY")
    print("=" * 70)

    total_rows = 0
    total_time = 0.0
    success_count = 0

    for table, result in results.items():
        status = "OK" if result.success else "FAIL"
        print(
            f"  {status}  {table:<20s} {result.row_count:>10,} rows  "
            f"{result.column_count:>3} cols  {result.duration_seconds:>6.1f}s"
        )
        if result.success:
            success_count += 1
            total_rows += result.row_count
            total_time += result.duration_seconds
        else:
            print(f"       Error: {result.error}")

    print("-" * 70)
    print(f"  Total: {success_count}/{len(results)} tables, {total_rows:,} rows in {total_time:.1f}s")

    # Quick validation
    print(f"\nStep 3: Quick row count validation...")
    all_match = True
    for table, result in results.items():
        if not result.success:
            continue
        expected = DataExtractor.EXPECTED_COUNTS.get(table)
        if expected and result.row_count != expected:
            print(f"  MISMATCH {table}: expected {expected:,}, got {result.row_count:,}")
            all_match = False
        elif expected:
            print(f"  OK  {table}: {result.row_count:,} rows")

    if all_match and success_count == len(results):
        print(f"\nSTATUS: ALL EXPORTS SUCCESSFUL")
        sys.exit(0)
    else:
        print(f"\nSTATUS: SOME ISSUES DETECTED - run validate_export.py for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
