#!/usr/bin/env python3
"""
Data Migration module for SDGW 1914-1919 Personnel Database.

Loads CSV exports into a SQLite database with type conversions,
validation, and error handling.
"""

import csv
import logging
import re
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("sdgw.migration")


@dataclass
class MigrationResult:
    table_name: str
    rows_loaded: int
    rows_skipped: int
    duration_seconds: float
    success: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class MigrationReport:
    timestamp: str
    db_path: str
    tables_migrated: int
    total_rows_loaded: int
    total_rows_skipped: int
    total_errors: int
    duration_seconds: float
    results: Dict[str, MigrationResult] = field(default_factory=dict)
    all_success: bool = True


def parse_death_date(raw_date: str, true_date: str) -> Optional[str]:
    """Parse death date fields into ISO 8601 format (YYYY-MM-DD).

    The MDB stores dates in two columns:
    - DEATH_DATE: text like "05/09/15" (DD/MM/YY)
    - D_TRUEDATE: datetime like "09/05/15 00:00:00" (MM/DD/YY HH:MM:SS)

    We prefer D_TRUEDATE as it's more reliable.
    """
    # Try D_TRUEDATE first (MM/DD/YY HH:MM:SS format from mdb-export)
    if true_date and true_date.strip():
        true_date = true_date.strip()
        # mdb-export outputs dates as MM/DD/YY HH:MM:SS
        match = re.match(r"(\d{2})/(\d{2})/(\d{2})\s", true_date)
        if match:
            month, day, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            # All dates are 1914-1919 era, so year < 50 means 19xx
            full_year = 1900 + year if year < 50 else 1800 + year
            try:
                return f"{full_year:04d}-{month:02d}-{day:02d}"
            except ValueError:
                pass

    # Fallback to DEATH_DATE (DD/MM/YY format)
    if raw_date and raw_date.strip():
        raw_date = raw_date.strip()
        match = re.match(r"(\d{2})/(\d{2})/(\d{2})", raw_date)
        if match:
            day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            full_year = 1900 + year if year < 50 else 1800 + year
            try:
                return f"{full_year:04d}-{month:02d}-{day:02d}"
            except ValueError:
                pass

    return None


def safe_int(value: str) -> Optional[int]:
    """Safely parse a string to int, handling floats and empty strings."""
    if not value or not value.strip():
        return None
    try:
        return int(float(value.strip()))
    except (ValueError, TypeError):
        return None


def safe_float(value: str) -> Optional[float]:
    """Safely parse a string to float."""
    if not value or not value.strip():
        return None
    try:
        return float(value.strip())
    except (ValueError, TypeError):
        return None


def clean_text(value: str) -> Optional[str]:
    """Clean text value: strip whitespace, convert empty to None."""
    if not value or not value.strip():
        return None
    return value.strip()


class DataMigrator:
    """Migrates CSV data into a SQLite database."""

    def __init__(self, db_path: str, schema_path: str):
        self.db_path = Path(db_path)
        self.schema_path = Path(schema_path)

        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

    def create_database(self):
        """Create the database and apply the schema."""
        logger.info("Creating database: %s", self.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.db_path))
        try:
            schema_sql = self.schema_path.read_text(encoding="utf-8")
            conn.executescript(schema_sql)
            conn.commit()
            logger.info("Schema applied successfully")
        finally:
            conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys=OFF")  # Defer FK checks to validation
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def load_ranks(self, csv_path: str) -> MigrationResult:
        """Load SD_RANKS.csv into ranks table."""
        start = time.time()
        table = "ranks"
        loaded = 0
        skipped = 0
        errors = []

        logger.info("Loading %s from %s", table, csv_path)

        conn = self._get_connection()
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, 1):
                    try:
                        rank_id = safe_int(row["RANK_ID"])
                        if rank_id is None:
                            rank_id = safe_int(row["ID"])

                        conn.execute(
                            """INSERT OR IGNORE INTO ranks
                               (rank_id, new_rank_id, rank_group, rank_new, rank_original, my_rank_id)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (
                                safe_int(row["ID"]),
                                safe_int(row["NEW_RANK_ID"]),
                                clean_text(row["Rank Group"]) or "Unknown",
                                clean_text(row["Rank New"]) or "Unknown",
                                clean_text(row["Rank Original"]) or "Unknown",
                                safe_int(row["MYRANKID"]),
                            ),
                        )
                        loaded += 1
                    except Exception as e:
                        skipped += 1
                        errors.append(f"Row {row_num}: {e}")
                        if len(errors) <= 10:
                            logger.warning("Ranks row %d error: %s", row_num, e)

            conn.commit()
        finally:
            conn.close()

        duration = time.time() - start
        logger.info("Loaded %d ranks in %.1fs (%d skipped)", loaded, duration, skipped)
        return MigrationResult(
            table_name=table, rows_loaded=loaded, rows_skipped=skipped,
            duration_seconds=duration, success=len(errors) == 0, errors=errors,
        )

    def load_battalions_sd(self, csv_path: str) -> MigrationResult:
        """Load SD_Battalions.csv into battalions_sd table."""
        return self._load_battalions(csv_path, "battalions_sd")

    def load_battalions_od(self, csv_path: str) -> MigrationResult:
        """Load OD_Battalions.csv into battalions_od table."""
        return self._load_battalions(csv_path, "battalions_od")

    def _load_battalions(self, csv_path: str, table: str) -> MigrationResult:
        start = time.time()
        loaded = 0
        skipped = 0
        errors = []

        logger.info("Loading %s from %s", table, csv_path)

        conn = self._get_connection()
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, 1):
                    try:
                        conn.execute(
                            f"INSERT OR IGNORE INTO {table} (battalion_id, name) VALUES (?, ?)",
                            (safe_int(row["ID"]), clean_text(row["Name"]) or f"Unknown-{row_num}"),
                        )
                        loaded += 1
                    except Exception as e:
                        skipped += 1
                        errors.append(f"Row {row_num}: {e}")
            conn.commit()
        finally:
            conn.close()

        duration = time.time() - start
        logger.info("Loaded %d %s in %.1fs", loaded, table, duration)
        return MigrationResult(
            table_name=table, rows_loaded=loaded, rows_skipped=skipped,
            duration_seconds=duration, success=len(errors) == 0, errors=errors,
        )

    def load_regiment_battalions(self, csv_path: str, table: str) -> MigrationResult:
        """Load REGBATS or OD_REGBATS CSV into regiment_battalion_sd/od table."""
        start = time.time()
        loaded = 0
        skipped = 0
        errors = []

        logger.info("Loading %s from %s", table, csv_path)

        conn = self._get_connection()
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row_num, row in enumerate(reader, 1):
                    try:
                        conn.execute(
                            f"INSERT OR IGNORE INTO {table} (regiment_id, battalion_id, sort_order) VALUES (?, ?, ?)",
                            (
                                safe_int(row["REG_ID"]),
                                safe_int(row["BAT_ID"]),
                                safe_float(row["SORTORDER"]),
                            ),
                        )
                        loaded += 1
                    except Exception as e:
                        skipped += 1
                        errors.append(f"Row {row_num}: {e}")
            conn.commit()
        finally:
            conn.close()

        duration = time.time() - start
        logger.info("Loaded %d %s in %.1fs", loaded, table, duration)
        return MigrationResult(
            table_name=table, rows_loaded=loaded, rows_skipped=skipped,
            duration_seconds=duration, success=len(errors) == 0, errors=errors,
        )

    def load_officers(self, csv_path: str) -> MigrationResult:
        """Load OFFICERS.csv into officers table."""
        start = time.time()
        table = "officers"
        loaded = 0
        skipped = 0
        errors = []

        logger.info("Loading %s from %s", table, csv_path)

        conn = self._get_connection()
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                batch = []
                for row_num, row in enumerate(reader, 1):
                    try:
                        death_date = parse_death_date(
                            row.get("DEATH_DATE", ""),
                            row.get("D_TRUEDATE", ""),
                        )
                        batch.append((
                            safe_int(row["O_ID"]),
                            safe_float(row["REGSORT"]),
                            safe_float(row["REG_ID"]),
                            safe_int(row["BAT_ID"]),
                            clean_text(row["SURNAME"]) or "UNKNOWN",
                            clean_text(row["CHRST_NAME"]),
                            clean_text(row["INITIALS"]),
                            clean_text(row["DECORATION"]),
                            clean_text(row["RANK"]),
                            safe_int(row["RANK_ID"]),
                            safe_float(row["DC_ID"]),
                            clean_text(row["DEATH_DATE"]),
                            death_date,
                            clean_text(row["ADDNL_TEXT"]),
                            safe_int(row["RNK_ID"]),
                        ))
                        loaded += 1

                        if len(batch) >= 5000:
                            conn.executemany(
                                """INSERT OR IGNORE INTO officers
                                   (officer_id, reg_sort, regiment_id, battalion_id,
                                    surname, christian_names, initials, decoration,
                                    rank_text, rank_id, dc_id, death_date_raw,
                                    death_date, additional_text, rnk_id)
                                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                                batch,
                            )
                            batch = []

                    except Exception as e:
                        skipped += 1
                        errors.append(f"Row {row_num}: {e}")
                        if len(errors) <= 10:
                            logger.warning("Officers row %d error: %s", row_num, e)

                # Final batch
                if batch:
                    conn.executemany(
                        """INSERT OR IGNORE INTO officers
                           (officer_id, reg_sort, regiment_id, battalion_id,
                            surname, christian_names, initials, decoration,
                            rank_text, rank_id, dc_id, death_date_raw,
                            death_date, additional_text, rnk_id)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        batch,
                    )

            conn.commit()
        finally:
            conn.close()

        duration = time.time() - start
        logger.info("Loaded %d officers in %.1fs (%d skipped)", loaded, duration, skipped)
        return MigrationResult(
            table_name=table, rows_loaded=loaded, rows_skipped=skipped,
            duration_seconds=duration, success=len(errors) == 0, errors=errors,
        )

    def load_soldiers(self, csv_path: str, chunk_size: int = 5000) -> MigrationResult:
        """Load SOLDIERS.csv into soldiers table with chunked inserts."""
        start = time.time()
        table = "soldiers"
        loaded = 0
        skipped = 0
        errors = []

        logger.info("Loading %s from %s (chunk_size=%d)", table, csv_path, chunk_size)

        conn = self._get_connection()
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                batch = []

                for row_num, row in enumerate(reader, 1):
                    try:
                        death_date = parse_death_date(
                            row.get("DEATH_DATE", ""),
                            row.get("D_TRUEDATE", ""),
                        )
                        batch.append((
                            safe_int(row["S_ID"]),
                            safe_float(row["REGSORT"]),
                            safe_float(row["REG_ID"]),
                            safe_int(row["BAT_ID"]),
                            clean_text(row["SURNAME"]) or "UNKNOWN",
                            clean_text(row["CHRST_NAME"]),
                            clean_text(row["INITIALS"]),
                            clean_text(row["BORN_TOWN"]),
                            clean_text(row["ENLST_LOC"]),
                            clean_text(row["ENLST_PLC"]),
                            clean_text(row["NUMPREF"]),
                            clean_text(row["NUMBER"]),
                            clean_text(row["RANK"]),
                            safe_float(row["DC_ID"]),
                            clean_text(row["DEATH_DATE"]),
                            death_date,
                            clean_text(row["ADDNL_TEXT"]),
                            safe_int(row["NUMSORT"]),
                            safe_float(row["D_LOC_ID"]),
                            clean_text(row["DEATH_LOC"]),
                            safe_float(row["TOW_ID"]),
                            safe_int(row["RANK_ID"]),
                            safe_float(row["RNK_OLD"]),
                            safe_int(row["RNK_ID"]),
                        ))
                        loaded += 1

                        if len(batch) >= chunk_size:
                            conn.executemany(
                                """INSERT OR IGNORE INTO soldiers
                                   (soldier_id, reg_sort, regiment_id, battalion_id,
                                    surname, christian_names, initials, birth_town,
                                    enlistment_loc, enlistment_place, number_prefix,
                                    service_number, rank_text, dc_id, death_date_raw,
                                    death_date, additional_text, number_sort,
                                    death_loc_id, death_location, town_id,
                                    rank_id, rnk_old, rnk_id)
                                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                                batch,
                            )
                            batch = []
                            if loaded % 50000 == 0:
                                logger.info("  ...loaded %d soldiers so far", loaded)

                    except Exception as e:
                        skipped += 1
                        errors.append(f"Row {row_num}: {e}")
                        if len(errors) <= 10:
                            logger.warning("Soldiers row %d error: %s", row_num, e)

                # Final batch
                if batch:
                    conn.executemany(
                        """INSERT OR IGNORE INTO soldiers
                           (soldier_id, reg_sort, regiment_id, battalion_id,
                            surname, christian_names, initials, birth_town,
                            enlistment_loc, enlistment_place, number_prefix,
                            service_number, rank_text, dc_id, death_date_raw,
                            death_date, additional_text, number_sort,
                            death_loc_id, death_location, town_id,
                            rank_id, rnk_old, rnk_id)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        batch,
                    )

            conn.commit()
        finally:
            conn.close()

        duration = time.time() - start
        logger.info("Loaded %d soldiers in %.1fs (%d skipped)", loaded, duration, skipped)
        return MigrationResult(
            table_name=table, rows_loaded=loaded, rows_skipped=skipped,
            duration_seconds=duration, success=len(errors) == 0, errors=errors,
        )

    def run_full_migration(self, export_dir: str) -> MigrationReport:
        """Run the complete migration pipeline."""
        start = time.time()
        export_path = Path(export_dir)
        results = {}

        logger.info("Starting full migration from %s", export_dir)

        # 1. Create schema
        self.create_database()

        # 2. Load reference tables first (order matters for FK)
        results["ranks"] = self.load_ranks(str(export_path / "SD_RANKS.csv"))
        results["battalions_sd"] = self.load_battalions_sd(str(export_path / "SD_Battalions.csv"))
        results["battalions_od"] = self.load_battalions_od(str(export_path / "OD_Battalions.csv"))
        results["regiment_battalion_sd"] = self.load_regiment_battalions(
            str(export_path / "REGBATS.csv"), "regiment_battalion_sd"
        )
        results["regiment_battalion_od"] = self.load_regiment_battalions(
            str(export_path / "OD_REGBATS.csv"), "regiment_battalion_od"
        )

        # 3. Load personnel tables
        results["officers"] = self.load_officers(str(export_path / "OFFICERS.csv"))
        results["soldiers"] = self.load_soldiers(str(export_path / "SOLDIERS.csv"))

        total_duration = time.time() - start
        total_loaded = sum(r.rows_loaded for r in results.values())
        total_skipped = sum(r.rows_skipped for r in results.values())
        total_errors = sum(len(r.errors) for r in results.values())
        all_success = all(r.success for r in results.values())

        logger.info(
            "Migration complete: %d rows loaded, %d skipped, %d errors in %.1fs",
            total_loaded, total_skipped, total_errors, total_duration,
        )

        return MigrationReport(
            timestamp=datetime.now().isoformat(),
            db_path=str(self.db_path),
            tables_migrated=len(results),
            total_rows_loaded=total_loaded,
            total_rows_skipped=total_skipped,
            total_errors=total_errors,
            duration_seconds=total_duration,
            results=results,
            all_success=all_success,
        )
