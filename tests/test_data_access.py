#!/usr/bin/env python3
"""Unit tests for the SDGW Data Access Layer."""

import csv
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.data_access import DataExtractor, ExportResult, ValidationReport

DB_PATH = str(project_root / "data" / "sd_2011.mdb")
HAS_MDB = Path(DB_PATH).exists()
HAS_MDBTOOLS = shutil.which("mdb-export") is not None

requires_mdb = pytest.mark.skipif(
    not HAS_MDB, reason="MDB database file not available"
)
requires_mdbtools = pytest.mark.skipif(
    not HAS_MDBTOOLS, reason="mdbtools not installed"
)


class TestDataExtractorInit:
    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            DataExtractor("/nonexistent/file.mdb")

    def test_wrong_extension_raises(self, tmp_path):
        bad_file = tmp_path / "test.txt"
        bad_file.write_text("not a database")
        with pytest.raises(ValueError, match="Expected .mdb"):
            DataExtractor(str(bad_file))

    @requires_mdb
    @requires_mdbtools
    def test_valid_init(self):
        extractor = DataExtractor(DB_PATH)
        assert extractor.mdb_path.exists()


@requires_mdb
@requires_mdbtools
class TestGetTables:
    def test_returns_seven_tables(self):
        extractor = DataExtractor(DB_PATH)
        tables = extractor.get_tables()
        assert len(tables) == 7

    def test_contains_expected_tables(self):
        extractor = DataExtractor(DB_PATH)
        tables = extractor.get_tables()
        expected = {"SD_RANKS", "SD_Battalions", "REGBATS", "OD_REGBATS",
                    "OD_Battalions", "OFFICERS", "SOLDIERS"}
        assert set(tables) == expected


@requires_mdb
@requires_mdbtools
class TestExtractTable:
    def test_export_small_table(self, tmp_path):
        extractor = DataExtractor(DB_PATH)
        csv_path = str(tmp_path / "SD_RANKS.csv")
        result = extractor.extract_table("SD_RANKS", csv_path)

        assert result.success
        assert result.row_count == 547
        assert result.column_count > 0
        assert Path(csv_path).exists()
        assert result.checksum is not None

    def test_export_creates_valid_csv(self, tmp_path):
        extractor = DataExtractor(DB_PATH)
        csv_path = str(tmp_path / "SD_Battalions.csv")
        extractor.extract_table("SD_Battalions", csv_path)

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            assert len(header) > 0
            rows = list(reader)
            assert len(rows) == 721

    def test_export_officers(self, tmp_path):
        extractor = DataExtractor(DB_PATH)
        csv_path = str(tmp_path / "OFFICERS.csv")
        result = extractor.extract_table("OFFICERS", csv_path)

        assert result.success
        assert result.row_count == 41846


@requires_mdb
@requires_mdbtools
class TestExportAll:
    def test_exports_all_tables(self, tmp_path):
        extractor = DataExtractor(DB_PATH)
        results = extractor.export_all(str(tmp_path))

        assert len(results) == 7
        assert all(r.success for r in results.values())

        # Check files exist
        for table in results:
            assert (tmp_path / f"{table}.csv").exists()


@requires_mdb
@requires_mdbtools
class TestValidateExport:
    def test_validate_after_export(self, tmp_path):
        extractor = DataExtractor(DB_PATH)
        extractor.export_all(str(tmp_path))
        report = extractor.validate_export(str(tmp_path))

        assert report.all_pass
        assert report.tables_checked == 7
        assert len(report.errors) == 0

    def test_validate_missing_csv(self, tmp_path):
        extractor = DataExtractor(DB_PATH)
        report = extractor.validate_export(str(tmp_path))

        assert not report.all_pass
        assert len(report.errors) > 0


@requires_mdb
@requires_mdbtools
class TestBackup:
    def test_create_backup(self, tmp_path):
        extractor = DataExtractor(DB_PATH)
        result = extractor.create_backup(str(tmp_path))

        assert result.success
        assert result.size_match
        assert Path(result.backup_path).exists()

    def test_prune_old_backups(self, tmp_path):
        extractor = DataExtractor(DB_PATH)

        # Create 6 backups, should keep only 5
        for i in range(6):
            extractor.create_backup(str(tmp_path), max_backups=5)

        backups = list(tmp_path.glob("sd_2011.mdb.backup.*"))
        assert len(backups) <= 5


class TestExpectedCounts:
    def test_expected_counts_defined(self):
        assert "OFFICERS" in DataExtractor.EXPECTED_COUNTS
        assert "SOLDIERS" in DataExtractor.EXPECTED_COUNTS
        assert DataExtractor.EXPECTED_COUNTS["OFFICERS"] == 41846
        assert DataExtractor.EXPECTED_COUNTS["SOLDIERS"] == 661960
