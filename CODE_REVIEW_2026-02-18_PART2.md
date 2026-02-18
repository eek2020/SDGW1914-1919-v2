# Code Review — SDGW 1914-1919 Personnel Database

## Part 2 of 2: Low Priority Issues, Quick Wins, Long-term Improvements, Positive Findings & Summary

---

## Low Priority / Enhancements

### Issue #16: `requirements.txt` Has No Pinned Versions

- **Severity:** Low
- **Category:** Maintainability / Reproducibility
- **Current Implementation:**

```text
pytest>=7.0
Flask>=3.0
beautifulsoup4>=4.12
```

- **Proposed Solution:**

Pin to exact versions for reproducible builds. Generate with `pip3 freeze > requirements.txt` after verifying the working environment:

```text
Flask==3.1.0
Werkzeug==3.1.3
pytest==8.3.4
beautifulsoup4==4.12.3
```

- **Reasoning:** `>=` constraints allow silent upgrades that can introduce breaking changes between deployments.
- **Expected Benefits:** Reproducible installs across environments; no surprise breakage on `pip install`.
- **Trade-offs:** Requires periodic manual version bumps to pick up security patches.
- **Effort Estimate:** Small
- **Priority:** Nice-to-have

---

### Issue #17: `server.sh` Logs to `/tmp` — Lost on System Restart

- **Severity:** Low
- **Category:** Operability
- **Current Implementation:**

```bash
# server.sh line 7
LOGFILE="/tmp/sdgw_server.log"
```

- **Proposed Solution:**

```bash
LOGFILE="$APP_DIR/logs/sdgw_server.log"
mkdir -p "$APP_DIR/logs"
```

- **Reasoning:** `/tmp` is cleared on reboot. Post-crash log analysis becomes impossible if the machine restarts before logs are inspected.
- **Expected Benefits:** Persistent logs survive reboots; consistent with the project's existing `logs/` directory.
- **Trade-offs:** Logs directory will grow over time; add log rotation (e.g., `logrotate`) for long-running deployments.
- **Effort Estimate:** Small
- **Priority:** Nice-to-have

---

### Issue #18: `human_date` / `human_date_short` Template Filters Are Near-Duplicate

- **Severity:** Low
- **Category:** Redundancy
- **Current Implementation:**

```python
# src/web_app.py lines 22–43
@app.template_filter('humandate')
def human_date(value):
    if not value:
        return ''
    try:
        dt = datetime.strptime(str(value), '%Y-%m-%d')
        return dt.strftime('%-d %B %Y')
    except (ValueError, TypeError):
        return str(value)

@app.template_filter('humandate_short')
def human_date_short(value):
    if not value:
        return ''
    try:
        dt = datetime.strptime(str(value), '%Y-%m-%d')
        return dt.strftime('%-d %b %Y')
    except (ValueError, TypeError):
        return str(value)
```

Both functions share identical guard logic, parsing, and error handling. Only the `strftime` format string differs.

- **Proposed Solution:**

```python
def _format_date(value, fmt):
    if not value:
        return ''
    try:
        return datetime.strptime(str(value), '%Y-%m-%d').strftime(fmt)
    except (ValueError, TypeError):
        return str(value)

@app.template_filter('humandate')
def human_date(value):
    return _format_date(value, '%-d %B %Y')

@app.template_filter('humandate_short')
def human_date_short(value):
    return _format_date(value, '%-d %b %Y')
```

- **Reasoning:** Any future change to error handling (e.g., logging parse failures) must currently be made in two places.
- **Expected Benefits:** Single point of change for date parsing logic.
- **Trade-offs:** None.
- **Effort Estimate:** Small
- **Priority:** Nice-to-have

---

### Issue #19: `_is_dropdown_only_filter_request` and `_is_simple_dropdown_only_request` Have Overlapping Logic

- **Severity:** Low
- **Category:** Redundancy
- **Current Implementation:**

```python
# src/web_app.py lines 481–507
def _is_dropdown_only_filter_request(params): ...   # checks free_text, date, dropdown keys
def _is_simple_dropdown_only_request(params): ...   # checks a narrower set of simple keys
```

Both functions classify filter requests by what fields are active. They share the concept of "dropdown-only" but implement it with different key sets and logic, making the relationship between them opaque. A future filter field addition requires updating both functions.

- **Proposed Solution:**

At minimum, add a docstring to each explaining how they relate and when each is used. Longer-term, consolidate into a single `_classify_filter_request(params)` that returns an enum or string tag (`'none'`, `'simple_dropdown'`, `'dropdown_only'`, `'mixed'`).

- **Reasoning:** The relationship between the two functions is not obvious to a new contributor; the risk of one being updated without the other is real.
- **Effort Estimate:** Small
- **Priority:** Nice-to-have

---

### Issue #20: `_results_filter_options` Duplicates the Rank/Battalion/Regiment Query Pattern from `filter_options`

- **Severity:** Low
- **Category:** Redundancy
- **Current Implementation:**

`_results_filter_options` (lines 585–668) and the `else` branch of `filter_options` (lines 1116–1155) both independently collect distinct `rank_id`, `battalion_id`, and `regiment_id` sets, then look up their display names with near-identical SQL. The battalion lookup SQL in particular is copy-pasted verbatim:

```python
# Appears in both _results_filter_options (line 648) and filter_options (line 1138):
f"SELECT bs.battalion_id, bs.name, rg.name AS regiment_name "
f"FROM battalions_sd bs "
f"LEFT JOIN regiment_battalion_sd rb ON rb.battalion_id = bs.battalion_id "
f"LEFT JOIN regiments rg ON rg.regiment_id = rb.regiment_id "
f"WHERE bs.battalion_id IN ({ph}) "
f"ORDER BY COALESCE(rg.name, 'Other'), bs.name"
```

- **Proposed Solution:**

Extract a shared helper:

```python
def _lookup_battalions_by_ids(db, battalion_ids):
    if not battalion_ids:
        return []
    ph = ','.join('?' * len(battalion_ids))
    return [{'battalion_id': r[0], 'name': r[1], 'regiment_name': r[2] or 'Other'}
            for r in db.execute(
                f"SELECT bs.battalion_id, bs.name, rg.name AS regiment_name "
                f"FROM battalions_sd bs "
                f"LEFT JOIN regiment_battalion_sd rb ON rb.battalion_id = bs.battalion_id "
                f"LEFT JOIN regiments rg ON rg.regiment_id = rb.regiment_id "
                f"WHERE bs.battalion_id IN ({ph}) "
                f"ORDER BY COALESCE(rg.name, 'Other'), bs.name",
                list(battalion_ids)
            )]
```

- **Reasoning:** Any change to the battalion display query (e.g., adding a sort_order column) must currently be made in two places.
- **Effort Estimate:** Small
- **Priority:** Nice-to-have

---

### Issue #21: `detail` Route Hardcodes `20` for Page Calculation Instead of Using `per_page`

- **Severity:** Low
- **Category:** Bug / Maintainability
- **Current Implementation:**

```python
# src/web_app.py line 905
results_page = (int(pos) // 20) + 1  # 20 per page
```

The `search` route defines `per_page = 20` (line 711), but the `detail` route hardcodes `20` independently. If `per_page` is ever changed in `search`, the back-to-results page calculation in `detail` will silently produce wrong page numbers.

- **Proposed Solution:**

```python
RESULTS_PER_PAGE = 20  # Define once as a module-level constant

# In search():
per_page = RESULTS_PER_PAGE

# In detail():
results_page = (int(pos) // RESULTS_PER_PAGE) + 1
```

- **Reasoning:** Magic number duplication; a single constant change in `search` would break navigation in `detail`.
- **Effort Estimate:** Small
- **Priority:** Nice-to-have

---

### Issue #22: `serve_image` Has No Cache Headers — Images Re-fetched on Every Page Load

- **Severity:** Low
- **Category:** Performance
- **Current Implementation:**

```python
# src/web_app.py lines 1627–1643
@app.route('/image/<int:image_id>')
def serve_image(image_id):
    image = manager.get_image(image_id)
    return send_file(
        io.BytesIO(image['image_data']),
        mimetype=image['image_type'],
        as_attachment=False
    )
```

No `Cache-Control`, `ETag`, or `Last-Modified` headers are set. Every page load that displays an image will re-fetch it from the database.

- **Proposed Solution:**

```python
from flask import make_response
import hashlib

@app.route('/image/<int:image_id>')
def serve_image(image_id):
    image = manager.get_image(image_id)
    if not image:
        return "Image not found", 404
    etag = hashlib.md5(image['image_data']).hexdigest()
    if request.headers.get('If-None-Match') == etag:
        return '', 304
    resp = make_response(image['image_data'])
    resp.headers['Content-Type'] = image['image_type']
    resp.headers['ETag'] = etag
    resp.headers['Cache-Control'] = 'public, max-age=86400'
    return resp
```

- **Reasoning:** Images are static once uploaded; there is no reason to re-read them from the database on every request.
- **Expected Benefits:** Eliminates redundant DB reads for image-heavy detail pages; reduces perceived load time.
- **Trade-offs:** Stale cache if an image is replaced (mitigated by ETag validation).
- **Effort Estimate:** Small
- **Priority:** Nice-to-have

---

### Issue #23: Tests Use the Real Production Database — No Test Isolation

- **Severity:** Low
- **Category:** Testability / Reliability
- **Current Implementation:**

```python
# tests/test_web_app.py lines 7–12
@pytest.fixture
def client():
    """Flask test client using the real database."""
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c
```

All tests run against the live `data/sd_2011.db`. Tests that assert on specific record counts or content (e.g., `assert b'SMITH' in r.data`) will fail if the database is unavailable or its content changes.

- **Proposed Solution:**

Add a `conftest.py` that creates a minimal in-memory SQLite database with a small fixture dataset for unit tests, while keeping the real-DB tests as an optional integration suite:

```python
# tests/conftest.py
import pytest
import sqlite3
from src.web_app import app, DB_PATH

@pytest.fixture(scope='session')
def test_db(tmp_path_factory):
    db_path = tmp_path_factory.mktemp('data') / 'test.db'
    # Create schema and insert minimal fixture rows
    conn = sqlite3.connect(db_path)
    # ... apply schema.sql, insert 2-3 soldiers and officers
    conn.close()
    return db_path
```

- **Reasoning:** Tests that depend on production data are fragile, slow, and cannot run in CI without the database file.
- **Expected Benefits:** Fast, isolated, reproducible unit tests; CI-friendly.
- **Trade-offs:** Fixture maintenance overhead; real-DB integration tests still needed for full confidence.
- **Effort Estimate:** Medium
- **Priority:** Nice-to-have

---

### Issue #24: `_validate_setup` in `DataExtractor` Runs `mdb-tables --version` to Check for mdbtools

- **Severity:** Low
- **Category:** Code Quality
- **Current Implementation:**

```python
# src/data_access.py lines 99–108
subprocess.run(
    ["mdb-tables", "--version"],
    capture_output=True,
    timeout=5,
)
```

`mdb-tables` does not accept a `--version` flag; it will exit with an error code. The code only checks `FileNotFoundError` (tool not installed), not the return code, so this works by accident — but it is misleading and will confuse anyone reading it.

- **Proposed Solution:**

```python
import shutil

def _validate_setup(self):
    if not self.mdb_path.exists():
        raise FileNotFoundError(f"Database not found: {self.mdb_path}")
    if self.mdb_path.suffix.lower() != ".mdb":
        raise ValueError(f"Expected .mdb file, got: {self.mdb_path.suffix}")
    if shutil.which("mdb-export") is None:
        raise EnvironmentError(
            "mdbtools not installed. Install with: brew install mdbtools"
        )
```

- **Reasoning:** `shutil.which` is the idiomatic way to check for a tool's presence; it avoids spawning a subprocess and is unambiguous.
- **Effort Estimate:** Small
- **Priority:** Nice-to-have

---

## Quick Wins

High-impact, low-effort improvements that can be done immediately:

1. **[Issue #1]** — Replace hardcoded `secret_key` with `os.environ.get('FLASK_SECRET_KEY')`. 10-minute change.
2. **[Issue #4]** — Delete the dead `_build_where` function (lines 1371–1397 of `web_app.py`). 1-minute change.
3. **[Issue #5]** — Extract `_annotation_fields_from_form()` helper to eliminate the duplicated 15-field dict. 15-minute change.
4. **[Issue #9]** — Add `VALID_ANNOTATION_FIELDS` allowlist guard to `update_annotation`. 10-minute change.
5. **[Issue #12]** — Fix N+1 query in `_with_group` for `birth_town` and `enlistment_loc`. 20-minute change.
6. **[Issue #17]** — Change `LOGFILE` in `server.sh` to `$APP_DIR/logs/sdgw_server.log`. 2-minute change.
7. **[Issue #18]** — Extract `_format_date` helper to deduplicate the two template filters. 10-minute change.
8. **[Issue #21]** — Define `RESULTS_PER_PAGE = 20` constant and use it in both `search` and `detail`. 5-minute change.
9. **[Issue #24]** — Replace `subprocess.run(["mdb-tables", "--version"])` with `shutil.which("mdb-export")`. 5-minute change.

---

## Long-term Improvements

Items for the technical roadmap:

1. **[Issue #2]** — Implement proper write authentication (Flask-Login or passphrase). Recommended within next sprint before any public access.
2. **[Issue #3]** — Migrate image storage from SQLite BLOBs to filesystem paths. Recommended before the image upload feature is used at scale; requires a one-time data migration.
3. **[Issue #6]** — Refactor record navigation to use a 3-record window query instead of 5 separate `_run_search` calls. Recommended when performance profiling shows detail page latency is a concern.
4. **[Issue #7]** — Add `threading.Lock` to the filter options cache. Recommended before any multi-threaded deployment (gunicorn with `--threads`).
5. **[Issue #8]** — Refactor `AnnotationManager` to accept and reuse the Flask request-scoped DB connection. Recommended alongside Issue #3 migration work.
6. **[Issue #11]** — Add caching and query reduction to `fuzzy_suggest`. Recommended when user testing reveals slow autocomplete on large queries.
7. **[Issue #15]** — Fix the `UNIQUE` constraint on `record_annotations` with a partial index. Requires a schema migration; recommended before annotation history accumulates.
8. **[Issue #23]** — Add a fixture-based test database for unit test isolation. Recommended before adding CI/CD pipeline.

---

## Positive Findings

Well-implemented patterns and good practices observed in the codebase:

- **Parameterised queries throughout** — All user-supplied values are passed as bound parameters to SQLite, not interpolated into SQL strings. This is the correct baseline for SQL injection prevention.
- **Bounded in-memory cache with TTL and eviction** — The `_filter_options_cache` implementation (TTL 20s, max 256 entries, LRU-style eviction) is a thoughtful, lightweight solution that avoids a full caching dependency.
- **Slow-query logging** — The `FILTER_OPTIONS_SLOW_LOG_MS = 250` threshold with structured breakdown logging (`rank_bat_reg_ms`, `soldier_facets_ms`, etc.) is excellent operational practice.
- **Soft deletes for annotations and images** — Using `is_active` flags rather than hard deletes preserves audit history and supports future recovery workflows.
- **Comprehensive accessibility** — ARIA landmarks, skip-to-main links, `role` attributes, and keyboard navigation are present throughout the templates. This is clearly a first-class concern.
- **Clean query builder abstraction** — `_build_conditions`, `_get_order_by`, and `_run_search` provide a well-factored, reusable search pipeline that handles officer/soldier/union cases cleanly.
- **Annotation history tracking** — Field-level change history with `old_value`/`new_value` and `change_reason` in `annotation_history` is a solid audit trail design.
- **Test coverage breadth** — The test suite covers home, search, detail, API endpoints, UI structure, accessibility, pagination, and filter pills. The use of BeautifulSoup for structural HTML assertions is appropriate.
- **`server.sh` process management** — The PID-file-based start/stop/restart/status pattern with stale-PID detection is robust for a single-server deployment.
- **`_parse_search_params` centralisation** — All request parameter extraction goes through one function, making it easy to audit what the application accepts and ensuring consistent stripping/defaulting.

---

## Recommendations Summary

| Issue | Title | Severity | Effort | Priority | Category |
| ------- | ------- | ---------- | -------- | ---------- | ---------- |
| #1 | Hardcoded secret key | Critical | Small | Must-fix | Security |
| #2 | No auth on write endpoints | Critical | Small–Med | Must-fix | Security |
| #3 | Images as SQLite BLOBs | High | Medium | Should-fix | Performance |
| #4 | Dead `_build_where` function | High | Small | Must-fix | Redundancy |
| #5 | Duplicate `fields` dict in annotation handler | High | Small | Must-fix | Redundancy |
| #6 | 10 queries per detail page navigation | High | Medium | Should-fix | Performance |
| #7 | Thread-unsafe filter cache | Medium | Small | Should-fix | Bug |
| #8 | AnnotationManager opens new DB conn per call | Medium | Medium | Should-fix | Performance |
| #9 | `update_annotation` accepts arbitrary column names | Medium | Small | Must-fix | Security |
| #10 | f-string column interpolation without internal guard | Medium | Small | Should-fix | Security |
| #11 | `fuzzy_suggest` runs 22+ queries with no cache | Medium | Medium | Should-fix | Performance |
| #12 | N+1 query in `_with_group` | Medium | Small | Should-fix | Performance |
| #13 | `get_row_count` exports full table | Medium | Small | Should-fix | Performance |
| #14 | `validate_export` loads full CSV into memory | Medium | Small | Should-fix | Memory |
| #15 | Incorrect UNIQUE constraint on annotations | Medium | Small | Should-fix | Data Integrity |
| #16 | Unpinned `requirements.txt` | Low | Small | Nice-to-have | Maintainability |
| #17 | Logs written to `/tmp` | Low | Small | Nice-to-have | Operability |
| #18 | Duplicate date filter functions | Low | Small | Nice-to-have | Redundancy |
| #19 | Overlapping dropdown-classifier functions | Low | Small | Nice-to-have | Redundancy |
| #20 | Duplicated battalion lookup SQL | Low | Small | Nice-to-have | Redundancy |
| #21 | Hardcoded `20` in detail page calculation | Low | Small | Nice-to-have | Bug |
| #22 | No cache headers on image serving | Low | Small | Nice-to-have | Performance |
| #23 | Tests use real production database | Low | Medium | Nice-to-have | Testability |
| #24 | Misleading mdbtools version check | Low | Small | Nice-to-have | Code Quality |

---

## Next Steps

1. **Immediate (this sprint):** Address Issues #1, #2, #4, #5, #9 — all security or high-impact redundancy fixes with Small effort. Can be completed in under 2 hours combined.
2. **Short-term (next 2 sprints):** Address Issues #7, #10, #12, #15, #18, #21 — correctness and quick-win improvements.
3. **Medium-term (roadmap):** Plan Issues #3, #6, #8, #11, #23 — architectural improvements requiring design decisions or data migrations.
4. **Ongoing:** Pin `requirements.txt` versions (#16) and move logs to `logs/` (#17) as part of next deployment preparation.

---

## Review Sign-off

- **Reviewed by:** Cascade AI Code Review
- **Date:** 18 February 2026
- **Approved for implementation:** [ ] Yes [ ] No [x] Partial — critical and must-fix items recommended for immediate action
- **Follow-up review needed:** [x] Yes — after Issues #1, #2, #3 are addressed
- **Notes:** The codebase is in good overall health. The search/filter pipeline is well-engineered and the accessibility work is commendable. The critical issues (#1 and #2) are straightforward to fix and should be prioritised before any expansion of the annotation/image upload features.
