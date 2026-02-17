#!/usr/bin/env python3
"""Unit tests for the SDGW Data Migration module."""

import sqlite3
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.data_migration import (
    DataMigrator,
    clean_text,
    parse_death_date,
    safe_float,
    safe_int,
)

EXPORT_DIR = str(project_root / "data" / "exports")
SCHEMA_PATH = str(project_root / "src" / "schema.sql")
HAS_EXPORTS = (Path(EXPORT_DIR) / "SD_RANKS.csv").exists()

requires_exports = pytest.mark.skipif(
    not HAS_EXPORTS, reason="CSV exports not available"
)


class TestDateParsing:
    def test_true_date_format(self):
        assert parse_death_date("", "09/05/15 00:00:00") == "1915-09-05"

    def test_true_date_1918(self):
        assert parse_death_date("", "05/20/18 00:00:00") == "1918-05-20"

    def test_raw_date_fallback(self):
        assert parse_death_date("05/09/15", "") == "1915-09-05"

    def test_raw_date_1916(self):
        assert parse_death_date("15/05/16", "") == "1916-05-15"

    def test_true_date_preferred_over_raw(self):
        result = parse_death_date("05/09/15", "09/05/15 00:00:00")
        assert result == "1915-09-05"

    def test_empty_returns_none(self):
        assert parse_death_date("", "") is None

    def test_whitespace_returns_none(self):
        assert parse_death_date("  ", "  ") is None


class TestSafeInt:
    def test_integer_string(self):
        assert safe_int("42") == 42

    def test_float_string(self):
        assert safe_int("42.0") == 42

    def test_empty_returns_none(self):
        assert safe_int("") is None

    def test_whitespace_returns_none(self):
        assert safe_int("  ") is None

    def test_invalid_returns_none(self):
        assert safe_int("abc") is None


class TestSafeFloat:
    def test_float_string(self):
        assert safe_float("3.14") == 3.14

    def test_integer_string(self):
        assert safe_float("42") == 42.0

    def test_empty_returns_none(self):
        assert safe_float("") is None


class TestCleanText:
    def test_strips_whitespace(self):
        assert clean_text("  SMITH  ") == "SMITH"

    def test_empty_returns_none(self):
        assert clean_text("") is None

    def test_whitespace_returns_none(self):
        assert clean_text("   ") is None

    def test_preserves_content(self):
        assert clean_text("NORWICH, NORFOLK") == "NORWICH, NORFOLK"


class TestMigratorInit:
    def test_missing_schema_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            DataMigrator(str(tmp_path / "test.db"), "/nonexistent/schema.sql")

    def test_valid_init(self, tmp_path):
        schema = tmp_path / "schema.sql"
        schema.write_text("-- empty schema")
        migrator = DataMigrator(str(tmp_path / "test.db"), str(schema))
        assert migrator.db_path == tmp_path / "test.db"


@requires_exports
class TestSchemaCreation:
    def test_create_database(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        migrator = DataMigrator(db_path, SCHEMA_PATH)
        migrator.create_database()

        conn = sqlite3.connect(db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert "ranks" in tables
        assert "officers" in tables
        assert "soldiers" in tables
        assert "battalions_sd" in tables
        assert "battalions_od" in tables


@requires_exports
class TestLoadRanks:
    def test_load_ranks(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        migrator = DataMigrator(db_path, SCHEMA_PATH)
        migrator.create_database()
        result = migrator.load_ranks(str(Path(EXPORT_DIR) / "SD_RANKS.csv"))

        assert result.success
        assert result.rows_loaded == 547
        assert result.rows_skipped == 0


@requires_exports
class TestLoadBattalions:
    def test_load_battalions_sd(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        migrator = DataMigrator(db_path, SCHEMA_PATH)
        migrator.create_database()
        result = migrator.load_battalions_sd(str(Path(EXPORT_DIR) / "SD_Battalions.csv"))

        assert result.success
        assert result.rows_loaded == 721


@requires_exports
class TestFullMigration:
    def test_full_migration(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        migrator = DataMigrator(db_path, SCHEMA_PATH)
        report = migrator.run_full_migration(EXPORT_DIR)

        assert report.all_success
        assert report.total_rows_loaded > 700000
        assert report.total_errors == 0

        # Verify we can query
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM soldiers")
        assert cursor.fetchone()[0] == 661960

        cursor = conn.execute("SELECT COUNT(*) FROM officers")
        assert cursor.fetchone()[0] == 41846
        conn.close()
