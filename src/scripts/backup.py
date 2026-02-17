#!/usr/bin/env python3
"""
Create a timestamped backup of the SDGW source database.

Usage:
    python src/scripts/backup.py [--db-path PATH] [--backup-dir DIR] [--max-backups N]
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
            logging.FileHandler(log_dir / "backup.log"),
        ],
    )


def main():
    parser = argparse.ArgumentParser(description="Backup SDGW source database")
    parser.add_argument(
        "--db-path",
        default=str(project_root / "data" / "sd_2011.mdb"),
        help="Path to the MDB database file",
    )
    parser.add_argument(
        "--backup-dir",
        default=str(project_root / "data" / "backups"),
        help="Directory for backup files",
    )
    parser.add_argument(
        "--max-backups",
        type=int,
        default=5,
        help="Maximum number of backups to keep (default: 5)",
    )
    args = parser.parse_args()

    setup_logging()

    print("=" * 70)
    print("SDGW 1914-1919 DATABASE BACKUP")
    print("=" * 70)

    try:
        extractor = DataExtractor(args.db_path)
    except (FileNotFoundError, EnvironmentError) as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

    result = extractor.create_backup(args.backup_dir, max_backups=args.max_backups)

    if result.success:
        print(f"\nBackup created: {Path(result.backup_path).name}")
        print(f"Source size:  {result.source_size / (1024*1024):.1f} MB")
        print(f"Backup size:  {result.backup_size / (1024*1024):.1f} MB")
        print(f"Size match:   {result.size_match}")
        print(f"\nSTATUS: BACKUP SUCCESSFUL")

        # List existing backups
        backup_dir = Path(args.backup_dir)
        backups = sorted(backup_dir.glob("sd_2011.mdb.backup.*"))
        print(f"\nExisting backups ({len(backups)}):")
        for b in backups:
            size_mb = b.stat().st_size / (1024 * 1024)
            print(f"  - {b.name} ({size_mb:.1f} MB)")

        sys.exit(0)
    else:
        print(f"\nERROR: {result.error}")
        print("STATUS: BACKUP FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
