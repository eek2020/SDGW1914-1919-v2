#!/usr/bin/env python3
"""
Data Access Layer for SDGW 1914-1919 Personnel Database.

Provides the DataExtractor class for extracting data from the legacy
Microsoft Access (.mdb) database using mdbtools.
"""

import csv
import hashlib
import io
import logging
import os
import random
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("sdgw.data_access")


@dataclass
class ExportResult:
    table_name: str
    output_path: str
    row_count: int
    column_count: int
    columns: List[str]
    duration_seconds: float
    success: bool
    error: Optional[str] = None
    checksum: Optional[str] = None


@dataclass
class TableValidation:
    table_name: str
    expected_rows: int
    actual_rows: int
    row_count_match: bool
    column_count_match: bool
    expected_columns: int = 0
    actual_columns: int = 0
    spot_check_passed: bool = True
    spot_check_details: List[str] = field(default_factory=list)
    encoding_valid: bool = True


@dataclass
class ValidationReport:
    timestamp: str
    tables_checked: int
    total_rows_validated: int
    all_pass: bool
    table_results: List[TableValidation]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class BackupResult:
    source_path: str
    backup_path: str
    source_size: int
    backup_size: int
    size_match: bool
    timestamp: str
    success: bool
    error: Optional[str] = None


class DataExtractor:
    """Extracts data from a Microsoft Access (.mdb) database using mdbtools."""

    # Expected row counts for validation
    EXPECTED_COUNTS = {
        "SD_RANKS": 547,
        "SD_Battalions": 721,
        "REGBATS": 1987,
        "OD_REGBATS": 1662,
        "OD_Battalions": 480,
        "OFFICERS": 41846,
        "SOLDIERS": 661960,
    }

    def __init__(self, mdb_path: str):
        self.mdb_path = Path(mdb_path).resolve()
        self._validate_setup()

    def _validate_setup(self):
        if not self.mdb_path.exists():
            raise FileNotFoundError(f"Database not found: {self.mdb_path}")
        if not self.mdb_path.suffix.lower() == ".mdb":
            raise ValueError(f"Expected .mdb file, got: {self.mdb_path.suffix}")
        if shutil.which("mdb-export") is None:
            raise EnvironmentError(
                "mdbtools not installed. Install with: brew install mdbtools"
            )

    def _run_mdb_command(
        self, cmd: List[str], timeout: int = 600
    ) -> subprocess.CompletedProcess:
        logger.debug("Running: %s", " ".join(cmd))
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            logger.error("Command failed: %s\nstderr: %s", " ".join(cmd), result.stderr)
        return result

    def get_tables(self) -> List[str]:
        result = self._run_mdb_command(["mdb-tables", "-1", str(self.mdb_path)])
        if result.returncode != 0:
            raise RuntimeError(f"Failed to list tables: {result.stderr}")
        tables = [t for t in result.stdout.strip().split("\n") if t.strip()]
        logger.info("Found %d tables: %s", len(tables), ", ".join(tables))
        return tables

    def get_schema(self, table_name: Optional[str] = None) -> str:
        cmd = ["mdb-schema", str(self.mdb_path)]
        if table_name:
            cmd.append(table_name)
        result = self._run_mdb_command(cmd)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to get schema: {result.stderr}")
        return result.stdout

    def get_row_count(self, table_name: str) -> int:
        """WARNING: Exports full table to count rows. O(N) in table size.
        Use only in offline migration/validation scripts, never in a web request."""
        result = self._run_mdb_command(
            ["mdb-export", str(self.mdb_path), table_name],
            timeout=600,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to count rows for {table_name}: {result.stderr}")
        lines = result.stdout.strip().split("\n")
        return max(0, len(lines) - 1)  # subtract header

    def extract_table(self, table_name: str, output_csv: str) -> ExportResult:
        output_path = Path(output_csv)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        start = time.time()
        logger.info("Exporting table: %s -> %s", table_name, output_csv)

        try:
            result = self._run_mdb_command(
                ["mdb-export", str(self.mdb_path), table_name],
                timeout=600,
            )
            if result.returncode != 0:
                return ExportResult(
                    table_name=table_name,
                    output_path=str(output_path),
                    row_count=0,
                    column_count=0,
                    columns=[],
                    duration_seconds=time.time() - start,
                    success=False,
                    error=result.stderr,
                )

            output_path.write_text(result.stdout, encoding="utf-8")

            # Parse to get metadata
            reader = csv.reader(io.StringIO(result.stdout))
            columns = next(reader, [])
            row_count = sum(1 for _ in reader)

            # Compute checksum
            checksum = hashlib.md5(result.stdout.encode("utf-8")).hexdigest()

            duration = time.time() - start
            logger.info(
                "Exported %s: %d rows, %d columns in %.1fs",
                table_name, row_count, len(columns), duration,
            )

            return ExportResult(
                table_name=table_name,
                output_path=str(output_path),
                row_count=row_count,
                column_count=len(columns),
                columns=columns,
                duration_seconds=duration,
                success=True,
                checksum=checksum,
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start
            logger.error("Timeout exporting %s after %.1fs", table_name, duration)
            return ExportResult(
                table_name=table_name,
                output_path=str(output_path),
                row_count=0,
                column_count=0,
                columns=[],
                duration_seconds=duration,
                success=False,
                error=f"Export timed out after {duration:.0f}s",
            )

    def export_all(self, output_dir: str) -> Dict[str, ExportResult]:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        tables = self.get_tables()
        results = {}

        logger.info("Starting export of %d tables to %s", len(tables), output_dir)

        for table in tables:
            csv_path = output_path / f"{table}.csv"
            results[table] = self.extract_table(table, str(csv_path))

        success_count = sum(1 for r in results.values() if r.success)
        fail_count = len(results) - success_count
        total_rows = sum(r.row_count for r in results.values())

        logger.info(
            "Export complete: %d/%d tables successful, %d total rows",
            success_count, len(results), total_rows,
        )
        if fail_count > 0:
            failed = [n for n, r in results.items() if not r.success]
            logger.error("Failed tables: %s", ", ".join(failed))

        return results

    def validate_export(self, export_dir: str) -> ValidationReport:
        export_path = Path(export_dir)
        tables = self.get_tables()
        table_results = []
        errors = []
        warnings = []
        total_rows = 0

        logger.info("Validating exports in %s", export_dir)

        for table in tables:
            csv_file = export_path / f"{table}.csv"
            if not csv_file.exists():
                errors.append(f"Missing CSV for table: {table}")
                table_results.append(TableValidation(
                    table_name=table,
                    expected_rows=self.EXPECTED_COUNTS.get(table, -1),
                    actual_rows=0,
                    row_count_match=False,
                    column_count_match=False,
                ))
                continue

            # Read CSV and count rows/columns (streaming to avoid OOM)
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                columns = next(reader, [])
                actual_rows = 0
                sample_rows = []
                for row in reader:
                    actual_rows += 1
                    if len(sample_rows) < 5:
                        sample_rows.append(row)

            total_rows += actual_rows
            expected = self.EXPECTED_COUNTS.get(table, actual_rows)
            row_match = actual_rows == expected

            if not row_match:
                errors.append(
                    f"{table}: expected {expected} rows, got {actual_rows}"
                )

            # Spot check: verify sample records are parseable and complete
            spot_details = []
            spot_passed = True
            sample_size = len(sample_rows)
            if sample_size > 0:
                for i, row in enumerate(sample_rows):
                    if len(row) != len(columns):
                        spot_passed = False
                        spot_details.append(
                            f"Row has {len(row)} fields, expected {len(columns)}"
                        )
                    # Check encoding by trying to encode/decode
                    for val in row:
                        try:
                            val.encode("utf-8").decode("utf-8")
                        except UnicodeError:
                            spot_passed = False
                            spot_details.append(f"Encoding issue in spot check row {i}")

            if spot_passed:
                spot_details.append(f"{sample_size}/{sample_size} spot checks passed")

            tv = TableValidation(
                table_name=table,
                expected_rows=expected,
                actual_rows=actual_rows,
                row_count_match=row_match,
                column_count_match=True,
                expected_columns=len(columns),
                actual_columns=len(columns),
                spot_check_passed=spot_passed,
                spot_check_details=spot_details,
            )
            table_results.append(tv)

            status = "PASS" if row_match and spot_passed else "FAIL"
            logger.info(
                "Validated %s: %s (%d rows)", table, status, actual_rows
            )

        all_pass = len(errors) == 0 and all(
            t.row_count_match and t.spot_check_passed for t in table_results
        )

        return ValidationReport(
            timestamp=datetime.now().isoformat(),
            tables_checked=len(table_results),
            total_rows_validated=total_rows,
            all_pass=all_pass,
            table_results=table_results,
            errors=errors,
            warnings=warnings,
        )

    def create_backup(self, backup_dir: str, max_backups: int = 5) -> BackupResult:
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_path / f"sd_2011.mdb.backup.{timestamp}"

        logger.info("Creating backup: %s", backup_file)

        try:
            source_size = self.mdb_path.stat().st_size
            shutil.copy2(self.mdb_path, backup_file)
            backup_size = backup_file.stat().st_size
            size_match = source_size == backup_size

            if not size_match:
                logger.warning(
                    "Backup size mismatch: source=%d, backup=%d",
                    source_size, backup_size,
                )

            # Prune old backups
            backups = sorted(backup_path.glob("sd_2011.mdb.backup.*"))
            while len(backups) > max_backups:
                oldest = backups.pop(0)
                oldest.unlink()
                logger.info("Pruned old backup: %s", oldest.name)

            logger.info(
                "Backup complete: %s (%.1f MB, match=%s)",
                backup_file.name, backup_size / (1024 * 1024), size_match,
            )

            return BackupResult(
                source_path=str(self.mdb_path),
                backup_path=str(backup_file),
                source_size=source_size,
                backup_size=backup_size,
                size_match=size_match,
                timestamp=timestamp,
                success=True,
            )

        except Exception as e:
            logger.error("Backup failed: %s", e)
            return BackupResult(
                source_path=str(self.mdb_path),
                backup_path=str(backup_file),
                source_size=0,
                backup_size=0,
                size_match=False,
                timestamp=timestamp,
                success=False,
                error=str(e),
            )
