# SDGW 1914-1919 — Master Plan

## Single Source of Truth for Project Planning

**Last Updated:** February 2026
**Version:** 1.0

---

## 1. Product Vision

Transform the legacy "Soldiers Died in the Great War 1914-19" CD-ROM application (Version 2.5, published by The Naval & Military Press Ltd.) into a modern, accessible system for searching 703,806 World War I military personnel records. The target audience is genealogy researchers, historians, and family members — many aged 60–80+ — who need a simple, forgiving interface with large text, high contrast, and zero technical setup.

---

## 2. Current System Overview

### Architecture

```text
┌──────────────────────────────────────────────────────────┐
│  Flask Web Application (src/web_app.py)                  │
│  ├─ Search (12-field multi-parameter)                    │
│  ├─ Results (paginated, card/table toggle, CSV export)   │
│  ├─ Detail (record view, related records, annotations)   │
│  ├─ APIs (/api/surname-suggest, /api/filter-options,     │
│  │        /api/fuzzy-suggest, /api/annotations/stats)    │
│  └─ Settings (theme, density, layout, font size)         │
├──────────────────────────────────────────────────────────┤
│  Annotation System (src/annotations.py)                  │
│  └─ User-contributed supplemental data & images          │
├──────────────────────────────────────────────────────────┤
│  SQLite Database (data/sd_2011.db — 257 MB)              │
│  ├─ Core: 8 tables, 27 indexes (src/schema.sql)         │
│  ├─ Annotations: 4 tables, 2 views                      │
│  │   (src/schema_amendments.sql)                         │
│  └─ Reference: regiment names, theatre groups, regions   │
│      (src/reference_data.sql)                            │
├──────────────────────────────────────────────────────────┤
│  Data Pipeline (one-time, completed)                     │
│  ├─ Extract: MDB → CSV (src/data_access.py)             │
│  └─ Load: CSV → SQLite (src/data_migration.py)          │
└──────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Notes |
| --- | --- | --- |
| Backend | Python 3.11+ / Flask 3.0+ | Single-file app (`src/web_app.py`, 1,691 lines) |
| Database | SQLite | File-based; `data/sd_2011.db` (257 MB) |
| Frontend | HTML5 / CSS3 / JavaScript | Server-rendered Jinja2 templates; Tom Select for dropdowns |
| Data Extraction | mdbtools v1.0.1 | One-time CSV export from legacy `.mdb` file |
| Testing | pytest / BeautifulSoup | 120 tests across 4 test files |
| Server | `server.sh` | Bash script; port 5001; PID file at `/tmp/sdgw_server.pid` |

### Database Schema

**Core Tables (src/schema.sql):**

| Table | Rows | Purpose |
| --- | --- | --- |
| `ranks` | 547 | Rank reference (group, normalised name, original name) |
| `battalions_sd` | 721 | Scottish Division battalion names |
| `battalions_od` | 480 | Other Districts battalion names |
| `regiment_battalion_sd` | 1,987 | Regiment-to-battalion mapping (SD) |
| `regiment_battalion_od` | 1,662 | Regiment-to-battalion mapping (OD) |
| `officers` | 41,846 | Officer personnel records |
| `soldiers` | 661,960 | Enlisted soldier records |
| `surname_lookup` | 50,323 | Materialised distinct surnames for autocomplete |

**Annotation Tables (src/schema_amendments.sql):**

| Table | Purpose |
| --- | --- |
| `record_annotations` | User-contributed supplemental fields (15 optional text fields) |
| `annotation_history` | Full audit trail of annotation changes |
| `record_images` | Image BLOBs with metadata (max 10 MB each) |
| `user_confirmations` | Action logging for all user modifications |

**Reference Tables (src/reference_data.sql):**

| Table | Purpose |
| --- | --- |
| `ref_regiment_names` | Human-readable regiment names mapped to regiment_id |
| `ref_theatre_groups` | Death location → theatre of war grouping |
| `ref_region_places` | Counties and cities for birth/enlistment classification |
| `ref_place_keywords` | Overseas/region keyword indicators |

### Key Configuration Values

| Setting | Value | Location |
| --- | --- | --- |
| Server port | 5001 | `server.sh`, `src/web_app.py` |
| Results per page | 20 | `src/web_app.py` |
| Filter cache TTL | 20 seconds | `src/web_app.py` |
| Filter cache max entries | 256 | `src/web_app.py` |
| Slow log threshold | 250 ms | `src/web_app.py` |
| Max CSV export rows | 10,000 | `src/web_app.py` |
| Max image size | 10 MB | `src/annotations.py` |
| Text suggestion limit | 60 | `src/web_app.py` |

---

## 3. Engineering Principles

1. **Codebase is the source of truth** — Documentation follows implementation, not the reverse.
2. **Accessibility first** — WCAG AAA contrast (7:1), 18px+ fonts, 44px touch targets, keyboard navigation, screen reader support.
3. **Senior-friendly design** — Every interaction designed for users aged 65+. Large controls, forgiving input, minimal jargon.
4. **Data integrity** — Original historical records are immutable. User contributions stored separately with full audit trails.
5. **Single-file simplicity** — SQLite database, no external services, no authentication. Desktop-deployable.
6. **Test before ship** — 120 automated tests covering data access, migration, web routes, and UI structure.

---

## 4. Completed Work

### Phase A: Data Access Layer — COMPLETED

Extracts all data from the legacy `.mdb` file to CSV using `mdbtools`.

- **Core:** `src/data_access.py` — `DataExtractor` class
- **Scripts:** `export_data.py`, `validate_export.py`, `backup.py`, `profile_data.py`
- **Tests:** `tests/test_data_access.py` — 14 tests passing
- **Output:** `data/exports/` — CSV files for all 7 tables
- **Archived PRD:** `docs/archive/prds/PRD_A_DATA_ACCESS_LAYER.md`

### Phase B: Data Migration — COMPLETED

Loads CSVs into normalised SQLite database with indexes for multi-parameter search.

- **Core:** `src/data_migration.py` — `DataMigrator` class; `src/schema.sql` — DDL
- **Scripts:** `migrate_personnel.py`, `validate_migration.py`
- **Tests:** `tests/test_migration.py` — 25 tests passing
- **Output:** `data/sd_2011.db` — 257 MB, fully indexed
- **Archived PRD:** `docs/archive/prds/PRD_B_DATA_MIGRATION.md`

### Phase C: Web UI — COMPLETED

Flask web application with multi-parameter search, paginated results, and detail view.

- **Core:** `src/web_app.py` — Flask app (1,691 lines)
- **Templates:** `home.html`, `search_results.html`, `detail.html`, `settings.html`, `about.html`, `annotation_form.html`, `404.html`
- **Styling:** `src/static/style.css` — Responsive, WCAG AAA, dark/light/system themes
- **Tests:** `tests/test_web_app.py` (43 tests) + `tests/test_ui.py` (38 tests)
- **Archived PRD:** `docs/archive/prds/PRD_C_BASIC_UI.md`

**Features delivered:**

- 12-field multi-parameter search (surname, christian names, initials, service number, rank, battalion, birth town, enlistment location, decoration, death location, death date range, record type)
- Surname autocomplete from 50,323 distinct surnames
- Dynamic filter narrowing (cascading dropdowns in Advanced mode)
- Basic/Advanced search mode toggle (persisted in localStorage)
- Paginated results (20/page) with First/Previous/Next/Last
- Card and table view toggle (persisted in sessionStorage)
- 5 sort options (Name A-Z/Z-A, Death Date earliest/latest, Rank)
- Removable filter pills
- Record-by-record First/Prev/Next/Last navigation in detail view
- Related records (same battalion, death date, birthplace)
- Breadcrumb navigation (Home > Results > Record)
- CSV export (max 10,000 rows, UTF-8 BOM)
- Copy record to clipboard
- Human-readable death dates ("5 September 1915")
- Print support (single records and results lists)
- Escape key returns to home
- WCAG AAA accessibility (skip-to-main, ARIA landmarks, 7:1 contrast, keyboard nav)
- User display settings (theme, density, layout, font size)

### Enhancement Backlog (PRD E) — PARTIALLY COMPLETED

8 of 13 enhancements delivered. See archived PRD: `docs/archive/prds/PRD_E_ENHANCEMENTS.md`

**Completed:** ENH-01 (dates), ENH-02 (UI tests), ENH-03 (breadcrumbs), ENH-04 (CSV export), ENH-05 (copy to clipboard), ENH-10 (First/Last nav), ENH-11 (PRD B alignment), ENH-12 (PRD C alignment)

### Annotation & Image System — BACKEND COMPLETE

- **Core:** `src/annotations.py` — `AnnotationManager` class
- **Schema:** `src/schema_amendments.sql` — 4 tables + 2 views
- **Routes:** All CRUD routes in `src/web_app.py`
- **Templates:** `src/templates/annotation_form.html` created
- **Status:** Backend complete; UI integration in detail page pending polish

---

## 5. Active Initiatives

### 5.1 Remaining Web UI Polish (Priority: Medium)

Carried forward from PRD E and Sprint 2 remaining items.

| Item | Description | Effort |
| --- | --- | --- |
| Formal accessibility audit | Run WAVE/Lighthouse on all pages; fix errors; document results | 2–4 hrs |
| Loading/searching indicator | CSS spinner on form submit with `role="status"` | 1 hr |
| User guide | `docs/product/USER_GUIDE.md` for 65+ audience | 4 hrs |
| Saved record lists / bookmarks | localStorage-based bookmarks with export | 1 week |
| Progressive search form disclosure | Collapse advanced fields below fold | 4 hrs |
| Per-page selector | Allow 10/20/50 results per page | 2 hrs |

### 5.2 Desktop Application (Priority: High — Phase D)

Standalone Windows 11 `.exe` for non-technical end users. Fully specified in archived PRD D (`docs/archive/prds/PRD_D_DESKTOP_APPLICATION.md`).

| Phase | Scope | Effort |
| --- | --- | --- |
| D1 | Desktop shell (pywebview + Flask) | 1 week |
| D2 | Senior UX overhaul (20px fonts, 48px buttons) | 2 weeks |
| D3 | Fuzzy search (Soundex, multi-pass, "Did you mean?") | 1 week |
| D4 | Windows build (PyInstaller → SDGW.exe) | 1 week |

**Key dependencies:** pywebview, PyInstaller, Soundex columns in schema, Windows 11 build machine.

---

## 6. Technical Debt Inventory

| Item | Severity | Description |
| --- | --- | --- |
| Annotation UI integration | Medium | Backend complete but detail page doesn't fully display annotations/images |
| No authentication | Low | Single-user desktop app; multi-user web deployment would need auth |
| `reference_data.sql` not auto-applied | Low | Regiment names, theatre groups exist but must be manually loaded |
| `enhance_search.py` / `optimize_filter_performance.py` | Low | Utility scripts without documentation or tests |
| Large `web_app.py` (1,691 lines) | Low | Could benefit from route blueprints for maintainability |
| No CI/CD pipeline | Low | Tests run manually via `pytest`; no GitHub Actions or similar |

---

## 7. Future Roadmap

### Near Term (Next 4 Weeks)

1. Formal accessibility audit and fixes
2. User guide documentation
3. Begin PRD D Phase D1 (Desktop shell)

### Medium Term (Weeks 5–10)

1. PRD D Phases D2–D3 (Senior UX + Fuzzy search)
2. Windows build and distribution testing
3. Annotation UI polish in detail page

### Long Term (Post-Launch)

1. Saved record lists / bookmarks
2. Geographic hierarchy for birth/residence locations
3. Admin review queue for user contributions
4. Image thumbnails and lightbox viewer
5. OCR integration for document images

---

## 8. Project Structure

```text
SDGW 1914-1919/
├── README.md                          Project overview and quick start
├── requirements.txt                   Python dependencies (pytest, Flask, beautifulsoup4)
├── server.sh                          Server management (start/stop/restart/status)
├── access_test.py                     Legacy MDB connectivity test
├── data/
│   ├── sd_2011.mdb                    Legacy Access database (gitignored)
│   ├── sd_2011.db                     SQLite database (gitignored, 257 MB)
│   ├── exports/                       CSV exports + DATA_PROFILE.md
│   └── backups/                       MDB backups (gitignored)
├── src/
│   ├── web_app.py                     Flask application (1,691 lines)
│   ├── annotations.py                 Annotation/image manager
│   ├── data_access.py                 MDB data extractor
│   ├── data_migration.py              CSV → SQLite migrator
│   ├── schema.sql                     Core database DDL (8 tables, 27 indexes)
│   ├── schema_amendments.sql          Annotation/image schema (4 tables, 2 views)
│   ├── reference_data.sql             Regiment names, theatres, regions, keywords
│   ├── __init__.py                    Package marker
│   ├── scripts/
│   │   ├── export_data.py             CSV export runner
│   │   ├── backup.py                  MDB backup utility
│   │   ├── validate_export.py         CSV validation
│   │   ├── migrate_personnel.py       SQLite migration runner
│   │   ├── validate_migration.py      Post-migration validation
│   │   ├── apply_amendments.py        Apply annotation schema
│   │   ├── profile_data.py            Field profiling for UI design
│   │   ├── enhance_search.py          Search enhancement utilities
│   │   └── optimize_filter_performance.py  Filter performance tuning
│   ├── templates/
│   │   ├── home.html                  Search form (Tom Select, Basic/Advanced mode)
│   │   ├── search_results.html        Paginated results (card/table, CSV export)
│   │   ├── detail.html                Record detail (navigation, related, clipboard)
│   │   ├── settings.html              Display preferences
│   │   ├── about.html                 About page
│   │   ├── annotation_form.html       Annotation editor
│   │   └── 404.html                   Error page
│   └── static/
│       ├── style.css                  Responsive CSS (WCAG AAA, themes, print)
│       └── SDGW1419.ico               Application icon
├── tests/
│   ├── test_data_access.py            14 tests (Phase A)
│   ├── test_migration.py              25 tests (Phase B)
│   ├── test_web_app.py                43 tests (Phase C routes)
│   └── test_ui.py                     38 tests (UI structure/accessibility)
├── old_system/                        Legacy CD-ROM application files
│   ├── screens/                       13 screenshots of original UI
│   ├── help/SDHELP.exe                Original help system
│   ├── runtime/                       Neuron105 runtime environment
│   └── README.TXT                     Original installation instructions
└── docs/
    ├── MASTER_PLAN.md                 ← This document (single source of truth)
    ├── architecture/
    │   └── DATABASE_SCHEMA.md         Schema reference
    ├── process/
    │   └── DEVELOPMENT_GUIDE.md       Setup, testing, deployment
    ├── product/
    │   └── (USER_GUIDE.md — pending)
    ├── archive/
    │   ├── prds/                       Archived PRDs with completion summaries
    │   │   ├── PRD_A_DATA_ACCESS_LAYER.md    (COMPLETED)
    │   │   ├── PRD_B_DATA_MIGRATION.md       (COMPLETED)
    │   │   ├── PRD_C_BASIC_UI.md             (COMPLETED)
    │   │   ├── PRD_D_DESKTOP_APPLICATION.md  (NOT STARTED)
    │   │   └── PRD_E_ENHANCEMENTS.md         (PARTIALLY COMPLETED)
    │   └── plans/                      Superseded planning documents
    │       ├── 01_DATA_ACCESS_PLAN.md
    │       ├── 02_ACCESS_REPORT.md
    │       ├── 06_IMPLEMENTATION_PLAN.md
    │       ├── 07_LEGACY_SYSTEM_ANALYSIS.md
    │       ├── 08_IMPLEMENTATION_STATUS.md
    │       ├── 10_PARITY_REPORT.md
    │       ├── 12_EXECUTIVE_SUMMARY.md
    │       ├── 13_UI_ENHANCEMENTS_SPRINT_2.md
    │       ├── 14_ANNOTATION_IMAGE_FEATURES.md
    │       ├── INDEX.md
    │       ├── PROJECT_SUMMARY.md
    │       ├── ai_help.md
    │       └── initial_help.md
    └── screen_ideas/                   UI design reference images
```

---

## 9. Test Coverage

| Test File | Tests | Scope |
| --- | --- | --- |
| `tests/test_data_access.py` | 14 | DataExtractor: init, tables, export, validate, backup |
| `tests/test_migration.py` | 25 | Date parsing, type conversion, schema, data loading |
| `tests/test_web_app.py` | 43 | Flask routes, search, detail, APIs, filter options |
| `tests/test_ui.py` | 38 | HTML structure, breadcrumbs, pills, accessibility, CSV |
| **Total** | **120** | All passing |

**Run all tests:** `python3 -m pytest tests/ -v`

---

## 10. Ownership & Contact

This is a solo/small-team project. All code authored by the engineering team with AI pair programming assistance (Cascade).

**Key decisions are documented in archived PRDs.** For historical context on any design choice, consult the relevant archived PRD in `docs/archive/prds/`.

---

**Document Status:** Authoritative — this is the single source of truth for project planning.
**Supersedes:** All prior planning documents (now in `docs/archive/plans/`).
