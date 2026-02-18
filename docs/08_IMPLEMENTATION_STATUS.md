# SDGW 1914-1919 Implementation Status

**Date:** 16 February 2026
**For:** Developer agents picking up Phase C (UI) or maintenance work

---

## Project State: Phases A, B & C Complete

This is a WW1 military personnel database modernization project. A legacy Windows CD-ROM app ("Soldiers Died in the Great War 1914-1919") containing 703,806 records in an MS Access `.mdb` file has been extracted, migrated into SQLite, and served via a Flask web UI.

---

## What Has Been Built

### Phase A: Data Access Layer (DONE)

Extracts all data from the legacy `.mdb` file to CSV using `mdbtools`.

| File | What It Does |
| ------ | ------------- |
| `src/data_access.py` | `DataExtractor` class — wraps mdbtools subprocess calls, exports tables to CSV, validates row counts, creates backups |
| `src/scripts/export_data.py` | CLI runner — backs up MDB, exports all 7 tables, validates counts |
| `src/scripts/validate_export.py` | Validates exported CSVs — row counts, spot checks, encoding |
| `src/scripts/backup.py` | Creates timestamped MDB backup, prunes old ones (keeps 5) |
| `src/scripts/profile_data.py` | Profiles every field for cardinality, null rates, top values — outputs `DATA_PROFILE.md` to guide search UI design |
| `tests/test_data_access.py` | 14 tests, all passing |

### Phase B: Data Migration (DONE)

Loads CSVs into a normalized SQLite database with indexes for multi-parameter search.

| File | What It Does |
| ------ | ------------- |
| `src/schema.sql` | Full DDL — 8 tables (7 data + 1 lookup), 27 indexes, includes `surname_lookup` materialised table |
| `src/data_migration.py` | `DataMigrator` class — type conversions, date parsing (DD/MM/YY → ISO 8601), chunked inserts for SOLDIERS (5000/batch) |
| `src/scripts/migrate_personnel.py` | CLI runner — drops old DB, applies schema, loads all tables in FK order |
| `src/scripts/validate_migration.py` | Post-migration validation — row counts, null checks, date parsing verification, search performance benchmarks, spot checks |
| `tests/test_migration.py` | 25 tests, all passing |

**Key output:**

- `data/sd_2011.db` — 257.3 MB SQLite database, fully indexed, ready for queries

### Phase C: Flask Web UI (DONE)

Multi-parameter search, paginated results, and detail view as a Flask web app.

| File | What It Does |
| ------ | ------------- |
| `src/web_app.py` | Flask application — search form, results page, detail view, autocomplete API, filter-options API, 404 handler |
| `src/templates/home.html` | Search form with Tom Select dropdowns, surname autocomplete, dynamic filter narrowing |
| `src/templates/search_results.html` | Paginated results with card/table toggle, sort controls, filter pills, print support |
| `src/templates/detail.html` | Full record view with related records, record-by-record navigation within search results |
| `src/templates/404.html` | Friendly 404 error page |
| `src/static/style.css` | Responsive CSS with WCAG AAA contrast, 18px+ fonts, 44px touch targets, print styles |
| `tests/test_web_app.py` | 43 tests, all passing |

**Features implemented:**

- Multi-parameter search (surname, first name, service number, rank, battalion, birth town, enlistment location, decoration, death location, death date range, record type)
- Surname autocomplete via `surname_lookup` table
- Dynamic dropdown narrowing (filter options update based on current search criteria)
- Paginated results (50 per page) with First/Previous/Next/Last navigation
- 5 sort options (Name A-Z/Z-A, Death Date earliest/latest, Rank)
- Card and Table view toggle (saved in sessionStorage)
- Filter pills showing active search criteria
- Record-by-record prev/next navigation within search results
- Related records (same battalion, same death date, same birthplace)
- Print support (single record and results list)
- WCAG AAA accessibility (skip-to-main, ARIA landmarks, 7:1 contrast, keyboard navigable)
- Friendly 404 error page

---

## Database Schema

### Tables & Row Counts

| Table | Rows | Purpose |
| ------- | ------ | --------- |
| `ranks` | 547 | Rank reference (ID, rank_group, rank_new, rank_original) |
| `battalions_sd` | 721 | Battalion names (Scottish Division) |
| `battalions_od` | 480 | Battalion names (Other Districts) |
| `regiment_battalion_sd` | 1,987 | Regiment-to-battalion mapping (SD) |
| `regiment_battalion_od` | 1,662 | Regiment-to-battalion mapping (OD) |
| `officers` | 41,846 | Officer personnel records |
| `soldiers` | 661,960 | Enlisted soldier records |
| `surname_lookup` | 50,323 | Materialised distinct surnames (union of officers + soldiers), indexed for fast autocomplete |
| **TOTAL** | **709,203** | (personnel records) |

### Officers Table Columns

```text
officer_id       INTEGER PK     -- Original O_ID
reg_sort         REAL           -- Regiment sort order
regiment_id      REAL           -- Regiment reference
battalion_id     INTEGER NOT NULL -- FK → battalions_sd
surname          TEXT NOT NULL   -- e.g. "ADAMSON"
christian_names  TEXT            -- e.g. "W C" or "JOHN CLAUDE HORSEY"
initials         TEXT            -- e.g. "W C"
decoration       TEXT            -- e.g. "DSO", "MC" (90.7% null)
rank_text        TEXT            -- Denormalized rank string e.g. "CAPT (TP)"
rank_id          INTEGER         -- FK → ranks
dc_id            REAL            -- Death cause ID
death_date_raw   TEXT            -- Original text e.g. "05/09/15"
death_date       TEXT            -- Parsed ISO e.g. "1915-09-05"
additional_text  TEXT            -- Free text notes (64.4% null)
rnk_id           INTEGER         -- Secondary rank reference
```

### Soldiers Table Columns

```text
soldier_id       INTEGER PK     -- Original S_ID
reg_sort         REAL
regiment_id      REAL
battalion_id     INTEGER NOT NULL -- FK → battalions_sd
surname          TEXT NOT NULL   -- e.g. "AINSLIE"
christian_names  TEXT            -- e.g. "JAMES"
initials         TEXT
birth_town       TEXT            -- e.g. "NORWICH, NORFOLK" (10.8% null)
enlistment_loc   TEXT            -- e.g. "WOOLWICH" (0.2% null)
enlistment_place TEXT            -- More specific place (51.7% null)
number_prefix    TEXT
service_number   TEXT            -- e.g. "4493" (250K unique values)
rank_text        TEXT            -- e.g. "TPR."
dc_id            REAL
death_date_raw   TEXT
death_date       TEXT            -- ISO 8601
additional_text  TEXT            -- (78.9% null)
number_sort      INTEGER
death_loc_id     REAL
death_location   TEXT            -- e.g. "France & Flanders" (137 unique values)
town_id          REAL
rank_id          INTEGER         -- FK → ranks
rnk_old          REAL
rnk_id           INTEGER
```

### Ranks Table Columns

```text
rank_id          INTEGER PK     -- Original ID from SD_RANKS
new_rank_id      INTEGER
rank_group       TEXT NOT NULL   -- 4 values: "Privates", "NCOs", "Warrant Officers", "Officers"
rank_new         TEXT NOT NULL   -- 114 normalized names e.g. "Armourer"
rank_original    TEXT NOT NULL   -- 539 original names e.g. "ARMR./PTE."
my_rank_id       INTEGER
```

### Indexes (27 total)

**Single-column search indexes:**

- `idx_soldiers_surname`, `idx_soldiers_christian_names`, `idx_soldiers_service_number`
- `idx_soldiers_battalion`, `idx_soldiers_rank`, `idx_soldiers_death_location`
- `idx_soldiers_birth_town`, `idx_soldiers_enlistment_loc`, `idx_soldiers_death_date`
- `idx_officers_surname`, `idx_officers_christian_names`, `idx_officers_battalion`
- `idx_officers_rank`, `idx_officers_decoration`, `idx_officers_death_date`
- `idx_ranks_group`, `idx_ranks_new`
- `idx_surname_lookup` — on the materialised `surname_lookup` table

**Composite indexes for multi-parameter queries:**

- `idx_soldiers_surname_battalion` — surname + battalion filter
- `idx_soldiers_surname_rank` — surname + rank filter
- `idx_soldiers_battalion_rank` — battalion + rank filter
- `idx_soldiers_battalion_death` — battalion + date range
- `idx_officers_surname_battalion` — surname + battalion filter

---

## Multi-Parameter Search: The Standard Query Method

**CRITICAL FOR PHASE C:** All search routes MUST follow this pattern. It applies to every searchable field.

### The Pattern: Dynamic WHERE Clause Builder

Every search parameter is optional. Non-empty parameters are AND-combined. Empty ones are ignored. All text matching is case-insensitive using `UPPER()`.

```python
import sqlite3

def build_search_query(params: dict, record_type: str = "all", page: int = 1, per_page: int = 50):
    """
    Build a multi-parameter search query from user-supplied form fields.

    This is THE standard search method. Use it for all search routes.
    Every new searchable field follows the same pattern: check if param
    is provided, append a WHERE clause, add the bound value.

    Args:
        params: dict of field_name -> user_value (from form submission)
        record_type: "all", "officers", or "soldiers"
        page: 1-based page number
        per_page: results per page

    Returns:
        (sql, bound_params, count_sql, count_params) tuple
    """

    # ── Step 1: Define searchable fields and their SQL expressions ──
    #
    # For each field the user can search on, define:
    #   - param_key: the form field name
    #   - sql_column: the column in the DB
    #   - match_type: how to compare
    #
    # MATCH TYPES:
    #   "prefix"   → surname LIKE 'SMITH%'     (uses index, fast)
    #   "contains" → birth_town LIKE '%LONDON%' (no index, slower but necessary)
    #   "exact"    → battalion_id = 42          (uses index, fastest)
    #   "gte"      → death_date >= '1916-01-01' (range scan)
    #   "lte"      → death_date <= '1916-12-31' (range scan)

    FIELD_RULES = {
        # ── Free text fields (high cardinality) ──
        "surname":        {"column": "surname",         "match": "prefix"},
        "christian_names":{"column": "christian_names",  "match": "prefix"},
        "service_number": {"column": "service_number",   "match": "exact"},    # soldiers only
        "birth_town":     {"column": "birth_town",       "match": "contains"}, # soldiers only
        "enlistment_loc": {"column": "enlistment_loc",   "match": "contains"}, # soldiers only

        # ── Dropdown/searchable dropdown fields (low-medium cardinality) ──
        "battalion_id":   {"column": "battalion_id",     "match": "exact"},
        "rank_id":        {"column": "rank_id",          "match": "exact"},
        "death_location": {"column": "death_location",   "match": "exact"},    # soldiers only
        "decoration":     {"column": "decoration",       "match": "contains"}, # officers only

        # ── Date range fields ──
        "death_date_from":{"column": "death_date",       "match": "gte"},
        "death_date_to":  {"column": "death_date",       "match": "lte"},
    }

    # ── Step 2: Build WHERE clauses from provided params ──

    where_clauses = []
    bound_values = []

    for param_key, rule in FIELD_RULES.items():
        value = params.get(param_key, "").strip()
        if not value:
            continue

        col = rule["column"]
        match = rule["match"]

        if match == "prefix":
            where_clauses.append(f"UPPER({col}) LIKE ?")
            bound_values.append(f"{value.upper()}%")

        elif match == "contains":
            where_clauses.append(f"UPPER({col}) LIKE ?")
            bound_values.append(f"%{value.upper()}%")

        elif match == "exact":
            # Numeric IDs pass as int; text values use UPPER match
            try:
                int_val = int(value)
                where_clauses.append(f"{col} = ?")
                bound_values.append(int_val)
            except ValueError:
                where_clauses.append(f"UPPER({col}) = ?")
                bound_values.append(value.upper())

        elif match == "gte":
            where_clauses.append(f"{col} >= ?")
            bound_values.append(value)

        elif match == "lte":
            where_clauses.append(f"{col} <= ?")
            bound_values.append(value)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # ── Step 3: Build full query for selected record type ──

    # Column sets for the SELECT (display-friendly names)
    OFFICER_COLS = """
        officer_id AS id, 'officer' AS record_type,
        surname, christian_names, initials, decoration,
        rank_text, battalion_id, death_date, additional_text
    """
    SOLDIER_COLS = """
        soldier_id AS id, 'soldier' AS record_type,
        surname, christian_names, initials, service_number,
        rank_text, battalion_id, death_date, death_location,
        birth_town, enlistment_loc, additional_text
    """

    offset = (page - 1) * per_page

    if record_type == "officers":
        sql = f"SELECT {OFFICER_COLS} FROM officers WHERE {where_sql} ORDER BY surname, christian_names LIMIT ? OFFSET ?"
        count_sql = f"SELECT COUNT(*) FROM officers WHERE {where_sql}"

    elif record_type == "soldiers":
        sql = f"SELECT {SOLDIER_COLS} FROM soldiers WHERE {where_sql} ORDER BY surname, christian_names LIMIT ? OFFSET ?"
        count_sql = f"SELECT COUNT(*) FROM soldiers WHERE {where_sql}"

    else:  # "all" — UNION both tables
        # Use common columns only for the UNION
        COMMON_COLS = "surname, christian_names, initials, rank_text, battalion_id, death_date, additional_text"
        sql = f"""
            SELECT officer_id AS id, 'officer' AS record_type, {COMMON_COLS}
            FROM officers WHERE {where_sql}
            UNION ALL
            SELECT soldier_id AS id, 'soldier' AS record_type, {COMMON_COLS}
            FROM soldiers WHERE {where_sql}
            ORDER BY surname, christian_names
            LIMIT ? OFFSET ?
        """
        count_sql = f"""
            SELECT
                (SELECT COUNT(*) FROM officers WHERE {where_sql}) +
                (SELECT COUNT(*) FROM soldiers WHERE {where_sql})
        """
        # UNION needs params doubled (once for officers, once for soldiers)
        bound_values = bound_values + bound_values

    query_params = bound_values + [per_page, offset]
    count_params = bound_values  # count query doesn't need LIMIT/OFFSET

    return sql, query_params, count_sql, count_params


# ── Step 4: Execute ──

def execute_search(db_path: str, params: dict, record_type: str = "all", page: int = 1, per_page: int = 50):
    """Execute a multi-parameter search and return results + total count."""
    sql, query_params, count_sql, count_params = build_search_query(params, record_type, page, per_page)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    results = conn.execute(sql, query_params).fetchall()
    total = conn.execute(count_sql, count_params).fetchone()[0]

    conn.close()

    return {
        "results": [dict(row) for row in results],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }
```

### Adding a New Searchable Field

To make any new field searchable, add ONE entry to `FIELD_RULES`:

```python
# Example: add enlistment_place as a searchable field
"enlistment_place": {"column": "enlistment_place", "match": "contains"},
```

That's it. The query builder, parameterisation, and pagination all work automatically. No other code changes needed.

### Match Types Reference

| Match Type | SQL Generated | Index Used? | Use For |
| --- | --- | --- | --- |
| `prefix` | `UPPER(col) LIKE 'VALUE%'` | Yes (with index on col) | Surname, first name — fast prefix search |
| `contains` | `UPPER(col) LIKE '%VALUE%'` | No (full scan on column) | Birth town, enlistment — substring match |
| `exact` | `col = value` | Yes | Battalion ID, rank ID, service number — exact match |
| `gte` | `col >= value` | Yes (range scan) | Date from — lower bound |
| `lte` | `col <= value` | Yes (range scan) | Date to — upper bound |

### Dropdown Population Queries

```sql
-- Rank groups (4 values → dropdown)
SELECT DISTINCT rank_group FROM ranks ORDER BY rank_group;

-- Ranks (114 normalized names → searchable dropdown)
SELECT rank_id, rank_new, rank_group FROM ranks ORDER BY rank_group, rank_new;

-- Battalions (721 → searchable dropdown)
SELECT battalion_id, name FROM battalions_sd ORDER BY name;

-- Death locations (137 → searchable dropdown)
SELECT DISTINCT death_location FROM soldiers WHERE death_location IS NOT NULL ORDER BY death_location;

-- Surnames (50,323 → autocomplete, from materialised lookup table)
SELECT surname FROM surname_lookup WHERE surname LIKE ? ORDER BY surname LIMIT 20;
-- Bind param: f"{user_input.upper()}%"
```

### Autocomplete Endpoint Pattern

```python
@app.route("/api/autocomplete/<field>")
def autocomplete(field):
    q = request.args.get("q", "").strip().upper()
    if len(q) < 2:
        return jsonify([])

    AUTOCOMPLETE_QUERIES = {
        "surname":    ("SELECT surname FROM surname_lookup WHERE surname LIKE ? ORDER BY surname LIMIT 20", f"{q}%"),
        "birth_town": ("SELECT DISTINCT birth_town FROM soldiers WHERE UPPER(birth_town) LIKE ? ORDER BY birth_town LIMIT 20", f"{q}%"),
        "enlistment": ("SELECT DISTINCT enlistment_loc FROM soldiers WHERE UPPER(enlistment_loc) LIKE ? ORDER BY enlistment_loc LIMIT 20", f"{q}%"),
    }

    if field not in AUTOCOMPLETE_QUERIES:
        return jsonify([])

    sql, param = AUTOCOMPLETE_QUERIES[field]
    conn = get_db()
    rows = conn.execute(sql, (param,)).fetchall()
    return jsonify([row[0] for row in rows if row[0]])
```

---

## Multi-Parameter Search UI Data Profile

The profiler (`src/scripts/profile_data.py`) analyzed every searchable field. Key findings:

| UI Control | Fields | Rationale |
| --- | --- | --- |
| **free_text_search** | Surname (47K unique, 50K in lookup), Christian Names (57K), Service Number (251K), Birth Town (85K), Enlistment Loc (25K) | High cardinality — need text input with autocomplete |
| **searchable_dropdown** | Death Location (137 unique), Decoration (69), Battalion (721) | Medium cardinality — filterable list |
| **dropdown** | Rank Group (4 values), Rank ID (officers: 7, soldiers: 4) | Low cardinality — simple select |
| **date_range_picker** | Death Date | Date field — from/to range |
| **toggle** | Officer vs Soldier | Binary choice |

**Full profile at:** `data/exports/DATA_PROFILE.md`

---

## Verified Performance (from validation run)

| Query Pattern | Example | Results | Time |
| --- | --- | --- | --- |
| Surname exact | `surname = 'SMITH'` | 9,802 | 0.2ms |
| Surname prefix | `surname LIKE 'SMI%'` | 10,032 | 19.9ms |
| Battalion filter | `battalion_id = 1` | 149 | 0.1ms |
| Rank filter | `rank_id = 1` | 538,520 | 9.0ms |
| Birth town | `birth_town = 'LONDON'` | 2,877 | 0.1ms |
| Death location | `death_location = 'France & Flanders'` | 552,471 | 12.3ms |
| Date range | `death_date BETWEEN '1916-07-01' AND '1916-07-31'` | 48,816 | 1.2ms |
| Multi: surname+battalion | `surname = 'SMITH' AND battalion_id = 1` | 1 | 0.0ms |
| Multi: surname+rank+date | `surname LIKE 'SM%' AND rank_id = 1 AND death_date > '1916-01-01'` | 7,329 | 62.1ms |
| Join: soldiers+ranks | `JOIN ranks ... WHERE rank_group = 'Privates'` | 661,178 | 10.6ms |

All queries under 100ms. UI target of <1s response time is easily achievable.

---

## How to Run Everything

```bash
# Prerequisites
brew install mdbtools
pip install -r requirements.txt   # pytest, Flask

# Phase A: Export from MDB to CSV
python3 src/scripts/export_data.py
python3 src/scripts/validate_export.py

# Phase B: Migrate CSV to SQLite
python3 src/scripts/migrate_personnel.py
python3 src/scripts/validate_migration.py

# Profile data for search UI design
python3 src/scripts/profile_data.py

# Phase C: Run Flask web app
python3 src/web_app.py
# Opens at http://127.0.0.1:5000

# Run all tests
python3 -m pytest tests/ -v
```

All commands run from project root: `/Users/erichook-marshall/Downloads/SDGW 1914-1919/`

---

## What's Next: Phase D (Desktop App)

Per `docs/06_IMPLEMENTATION_PLAN.md`, the next phase is packaging as a desktop application.

---

## File Tree

```text
SDGW 1914-1919/
├── access_test.py                          # Original POC script
├── requirements.txt                        # pytest, Flask
├── docs/
│   ├── INDEX.md                            # Master doc index
│   ├── PROJECT_SUMMARY.md                  # Executive summary
│   ├── 01_DATA_ACCESS_PLAN.md             # Phase A strategy
│   ├── 02_ACCESS_REPORT.md                # MDB accessibility proof
│   ├── 03_PRD_A_DATA_ACCESS_LAYER.md      # Phase A requirements
│   ├── 04_PRD_B_DATA_MIGRATION.md         # Phase B requirements
│   ├── 05_PRD_C_BASIC_UI.md              # Phase C requirements ← NEXT
│   ├── 06_IMPLEMENTATION_PLAN.md          # 8-week timeline
│   ├── 07_LEGACY_SYSTEM_ANALYSIS.md       # Old CD-ROM app analysis
│   └── 08_IMPLEMENTATION_STATUS.md        # THIS FILE
├── data/
│   ├── sd_2011.mdb                        # Source database (282 MB)
│   ├── sd_2011.db                         # SQLite database (257 MB) ← USE THIS
│   ├── backups/                           # MDB backups
│   └── exports/                           # CSV exports (7 CSVs + DATA_PROFILE.md)
├── src/
│   ├── __init__.py
│   ├── data_access.py                     # DataExtractor class (Phase A)
│   ├── data_migration.py                  # DataMigrator class (Phase B)
│   ├── web_app.py                         # Flask web application (Phase C)
│   ├── schema.sql                         # SQLite DDL (8 tables, 27 indexes)
│   ├── static/
│   │   └── style.css                      # WCAG AAA responsive styles
│   ├── templates/
│   │   ├── home.html                      # Search form with Tom Select
│   │   ├── search_results.html            # Paginated results (card/table)
│   │   ├── detail.html                    # Full record view
│   │   └── 404.html                       # Friendly error page
│   └── scripts/
│       ├── __init__.py
│       ├── export_data.py                 # MDB → CSV export runner
│       ├── validate_export.py             # CSV validation
│       ├── backup.py                      # MDB backup utility
│       ├── profile_data.py                # Data profiler for search UI
│       ├── migrate_personnel.py           # CSV → SQLite migration runner
│       └── validate_migration.py          # Post-migration validation
├── tests/
│   ├── test_data_access.py                # 14 tests (all pass)
│   ├── test_migration.py                  # 25 tests (all pass)
│   └── test_web_app.py                    # 43 tests (all pass)
├── logs/                                  # Runtime logs
└── old_system/                            # Legacy Windows CD-ROM app (reference only)
```

---

## Test Status

```text
tests/test_data_access.py    14 passed    (28.6s — includes live MDB reads)
tests/test_migration.py      25 passed    (0.06s — unit + integration)
tests/test_web_app.py        43 passed    (~60s — uses real database)
TOTAL                        82 passed, 0 failed
```

---

## Known Issues

1. **1 orphaned officer rank reference** — one officer record has a `rank_id` not in the `ranks` table. Cosmetic; does not affect search or display.
2. **SOLDIERS.ENLST_PLC is 51.7% null** — many soldiers have no specific enlistment place. UI should handle gracefully (show "—" or omit).
3. **OFFICERS have no service_number** — only soldiers have service numbers. UI search by service number should scope to soldiers only, or the "all" UNION query should handle the missing column.
4. **DEATH_DATE 100% parse rate** — all raw dates parsed to ISO 8601 successfully. Whether a person died is better determined by `dc_id` or `death_location` presence, not by date nullability.
5. **surname_lookup table** — materialised view of 50,323 distinct surnames across both officers and soldiers. Use for autocomplete. If data is re-migrated, this table is recreated automatically by `schema.sql`.
