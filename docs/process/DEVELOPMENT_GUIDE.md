# Development Guide

## SDGW 1914-1919 Personnel Database

---

## Prerequisites

- **Python 3.11+**
- **mdbtools** (only needed for re-extracting from legacy `.mdb` file)
- **pip** packages: see `requirements.txt`

---

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url>

# 2. Install Python dependencies
pip3 install -r requirements.txt

# 3. Start the server
./server.sh start

# 4. Open in browser
open http://127.0.0.1:5001
```

The application requires `data/sd_2011.db` (SQLite database, 257 MB). This file is gitignored due to size. If you don't have it, see [Rebuilding the Database](#rebuilding-the-database) below.

---

## Server Management

The `server.sh` script manages the Flask development server:

```bash
./server.sh start     # Start server on port 5001 (background)
./server.sh stop      # Stop the server
./server.sh restart   # Restart
./server.sh status    # Check if running
```

- **Port:** 5001
- **PID file:** `/tmp/sdgw_server.pid`
- **Log file:** `/tmp/sdgw_server.log`
- **Host:** 127.0.0.1 (localhost only)

Alternatively, run directly:

```bash
python3 src/web_app.py
```

---

## Running Tests

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test files
python3 -m pytest tests/test_data_access.py -v    # 14 tests (Phase A)
python3 -m pytest tests/test_migration.py -v       # 25 tests (Phase B)
python3 -m pytest tests/test_web_app.py -v         # 43 tests (Phase C routes)
python3 -m pytest tests/test_ui.py -v              # 38 tests (UI/accessibility)
```

**Total:** 120 tests across 4 files.

**Note:** `test_data_access.py` requires `data/sd_2011.mdb` and `mdbtools` installed. Tests are skipped automatically if these are not available. All other tests require `data/sd_2011.db`.

---

## Dependencies

Defined in `requirements.txt`:

| Package | Version | Purpose |
| --- | --- | --- |
| pytest | >= 7.0 | Test framework |
| Flask | >= 3.0 | Web framework |
| beautifulsoup4 | >= 4.12 | HTML parsing in UI tests |

No other runtime dependencies. The application uses only Python standard library modules plus Flask.

---

## Rebuilding the Database

If you need to recreate `data/sd_2011.db` from scratch:

### Step 1: Extract CSVs from legacy MDB (requires mdbtools)

```bash
brew install mdbtools   # macOS
python3 src/scripts/export_data.py
```

This exports all 7 tables from `data/sd_2011.mdb` to `data/exports/`.

### Step 2: Validate exports

```bash
python3 src/scripts/validate_export.py
```

### Step 3: Run migration

```bash
python3 src/scripts/migrate_personnel.py
```

This creates `data/sd_2011.db` with the core schema and loads all data.

### Step 4: Apply annotation schema

```bash
python3 src/scripts/apply_amendments.py
```

### Step 5: Load reference data

```bash
sqlite3 data/sd_2011.db < src/reference_data.sql
```

### Step 6: Validate migration

```bash
python3 src/scripts/validate_migration.py
```

---

## Project Architecture

```text
src/web_app.py          Main Flask application (1,691 lines)
                        Routes: /, /search, /record/<type>/<id>, /export-csv,
                        /settings, /about, /api/surname-suggest,
                        /api/filter-options, /api/fuzzy-suggest,
                        /api/annotations/stats, annotation/image CRUD routes

src/annotations.py      AnnotationManager class for user-contributed data
                        and image uploads with audit trail

src/data_access.py      DataExtractor class (mdbtools wrapper, one-time use)
src/data_migration.py   DataMigrator class (CSV → SQLite, one-time use)

src/schema.sql              Core DDL (8 tables, 27 indexes)
src/schema_amendments.sql   Annotation/image DDL (4 tables, 2 views)
src/reference_data.sql      Regiment names, theatres, regions, place keywords
```

---

## Key Application Features

### Search Modes

- **Basic mode:** All dropdown options remain full; no cascading API calls. Simpler but less focused.
- **Advanced mode:** Dropdowns cascade based on active filters via `/api/filter-options`. More precise but requires API round-trips.

Mode is toggled in the nav bar and persisted in `localStorage` under key `sdgw_search_mode`.

### Display Settings

Users can customise their experience via the Settings page:

- **Theme:** Light / Dark / System
- **Detail density:** Compact / Normal / Comfortable
- **Detail layout:** Split / Stacked
- **Font size:** Adjustable

Settings are stored in `localStorage` under key `sdgw_display_settings`.

### Caching

Filter options responses are cached in-memory with:

- **TTL:** 20 seconds
- **Max entries:** 256
- **Slow log threshold:** 250 ms (logged to console)

---

## Coding Conventions

- **Python style:** Standard PEP 8. No linter enforced but code follows conventions.
- **SQL:** Uppercase keywords, lowercase identifiers.
- **HTML/CSS:** Semantic HTML5, ARIA landmarks, WCAG AAA contrast targets.
- **Templates:** Jinja2 with server-side rendering. No SPA framework.
- **JavaScript:** Vanilla JS in templates. Tom Select CDN for enhanced dropdowns. No build step.
- **Database access:** Direct `sqlite3` module. No ORM. Parameterised queries throughout.

---

## Schema Reference

See `docs/architecture/DATABASE_SCHEMA.md` for the complete schema documentation.
