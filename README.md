# SDGW 1914-1919

Modern web application for searching **703,806 World War I military personnel records** from the "Soldiers Died in the Great War 1914-19" dataset. Originally a Windows CD-ROM application (Version 2.5, The Naval & Military Press Ltd.), now a Flask web app with SQLite backend.

---

## Project Status

| Phase | Status | Tests |
| --- | --- | --- |
| **A: Data Access** — Extract from legacy `.mdb` | Complete | 14 passing |
| **B: Data Migration** — Load into SQLite | Complete | 25 passing |
| **C: Web UI** — Flask search & display | Complete | 81 passing |
| **D: Desktop App** — Standalone `.exe` for Windows | Not started | — |
| **Total** | | **120 tests** |

---

## Quick Start

### Prerequisites

- Python 3.11+
- `data/sd_2011.db` (SQLite database, 257 MB — gitignored; see [Rebuilding the Database](#rebuilding-the-database))

### Run

**For end users (recommended) — one-click launcher with the SDGW icon:**

After a one-time `pip3 install -r requirements.txt`:

- **macOS** — double-click `SDGW 1914-1919.app` in the repo root. The app window opens with the SDGW icon; closing the window stops the embedded server.
- **Windows** — double-click `SDGW 1914-1919.bat` (or a desktop shortcut to it; right-click → Properties → Change Icon → `src\static\SDGW1419.ico`). Closing the window stops the server.

Both launchers use a single native window (no browser, no separate server step). The first launch on macOS may prompt Gatekeeper — right-click the `.app` once and choose "Open" to approve it.

**For developers — command-line:**

```bash
pip3 install -r requirements.txt
./server.sh start
# Open http://127.0.0.1:5001
```

Or run the Flask app directly:

```bash
python3 src/web_app.py
# Open http://127.0.0.1:5001
```

### Test

```bash
python3 -m pytest tests/ -v
```

---

## Features

- **12-field multi-parameter search** — surname, christian names, initials, service number, rank, battalion, birth town, enlistment location, decoration, death location, death date range, record type
- **Surname autocomplete** — 50,323 distinct surnames with instant suggestions
- **Cascading filters** — dropdowns narrow based on active filters (Advanced mode)
- **Basic/Advanced search mode** — toggle in nav bar; persisted in localStorage
- **Paginated results** — 20 per page with First/Previous/Next/Last navigation
- **Card and table view** — toggle saved in sessionStorage
- **5 sort options** — Name A-Z/Z-A, Death Date earliest/latest, Rank
- **Removable filter pills** — click to remove individual filters
- **Record detail view** — grouped sections, related records, record-by-record navigation
- **Breadcrumb navigation** — Home > Results > Record
- **CSV export** — up to 10,000 rows, UTF-8 with BOM for Excel
- **Copy to clipboard** — one-click formatted record text
- **Human-readable dates** — "5 September 1915" (not ISO format)
- **Print support** — individual records and results lists
- **WCAG AAA accessibility** — 7:1 contrast, 18px+ fonts, 44px touch targets, keyboard navigation, ARIA landmarks, skip-to-main
- **Display settings** — theme (light/dark/system), density, layout, font size
- **Annotation system** — user-contributed supplemental data and image uploads (backend complete)

---

## Database

**SQLite:** `data/sd_2011.db` (257 MB)

| Table | Rows | Purpose |
| --- | --- | --- |
| `soldiers` | 661,960 | Enlisted soldier records |
| `officers` | 41,846 | Officer records |
| `ranks` | 547 | Rank reference |
| `battalions_sd` | 721 | Scottish Division battalions |
| `battalions_od` | 480 | Other Districts battalions |
| `regiment_battalion_sd` | 1,987 | Regiment-battalion mapping (SD) |
| `regiment_battalion_od` | 1,662 | Regiment-battalion mapping (OD) |
| `surname_lookup` | 50,323 | Autocomplete index |

27 indexes for multi-parameter search. Additional tables for annotations, images, and reference data.

See `docs/architecture/DATABASE_SCHEMA.md` for full schema reference.

---

## Rebuilding the Database

If `data/sd_2011.db` is not available:

```bash
# 1. Install mdbtools (macOS)
brew install mdbtools

# 2. Export CSVs from legacy MDB
python3 src/scripts/export_data.py

# 3. Validate exports
python3 src/scripts/validate_export.py

# 4. Migrate to SQLite
python3 src/scripts/migrate_personnel.py

# 5. Apply annotation schema
python3 src/scripts/apply_amendments.py

# 6. Load reference data
sqlite3 data/sd_2011.db < src/reference_data.sql

# 7. Validate
python3 src/scripts/validate_migration.py
```

---

## Project Structure

```text
SDGW 1914-1919/
├── src/
│   ├── web_app.py              Flask application (1,691 lines)
│   ├── annotations.py          Annotation/image manager
│   ├── data_access.py          MDB data extractor
│   ├── data_migration.py       CSV → SQLite migrator
│   ├── schema.sql              Core database DDL
│   ├── schema_amendments.sql   Annotation/image schema
│   ├── reference_data.sql      Regiment names, theatres, regions
│   ├── scripts/                Utility scripts
│   ├── templates/              7 Jinja2 HTML templates
│   └── static/                 CSS, icons
├── tests/                      120 tests across 4 files
├── data/                       Database and exports (gitignored)
├── docs/                       Documentation
│   ├── MASTER_PLAN.md          Single source of truth
│   ├── architecture/           Schema reference
│   ├── process/                Development guide
│   └── archive/                Archived PRDs and plans
├── launcher.py                 Single-window launcher (Flask + pywebview)
├── SDGW 1914-1919.app/         macOS double-click app bundle
├── SDGW 1914-1919.bat          Windows double-click launcher
├── requirements.txt            Python dependencies
└── server.sh                   Server management script (CLI / dev)
```

---

## Documentation

- **[Master Plan](docs/MASTER_PLAN.md)** — Single source of truth for project status, architecture, and roadmap
- **[Database Schema](docs/architecture/DATABASE_SCHEMA.md)** — Complete schema reference
- **[Development Guide](docs/process/DEVELOPMENT_GUIDE.md)** — Setup, testing, and coding conventions

### Archived Documents

All original PRDs and planning documents are preserved in `docs/archive/` with completion summaries:

- `docs/archive/prds/` — PRDs A through E with status annotations
- `docs/archive/plans/` — Superseded planning documents, reports, and analysis

---

## Acknowledgements

- **Original data:** "Soldiers Died in the Great War 1914-19 Version 2.5" by The Naval & Military Press Ltd.
- **Licence:** Vendor has granted permission for modernisation and web deployment.

---

**Note:** Database files (`data/*.db`, `data/*.mdb`) are gitignored due to size. See [Rebuilding the Database](#rebuilding-the-database) for recreation instructions.
