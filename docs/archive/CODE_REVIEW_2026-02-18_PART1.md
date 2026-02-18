# Code Review — SDGW 1914-1919 Personnel Database

## Part 1 of 2: Critical, High, and Medium Priority Issues

- **Overall Assessment:** Good
- **Total Issues Found:** 24
- **Critical Issues:** 2
- **High Priority Issues:** 5
- **Medium Priority Issues:** 9
- **Low Priority / Enhancements:** 8
- **Review Date:** 18 February 2026
- **Reviewer:** Cascade AI Code Review
- **Code/Module Reviewed:** Full codebase — `src/web_app.py`, `src/annotations.py`, `src/data_access.py`, `src/schema.sql`, `src/schema_amendments.sql`, `tests/`, `server.sh`, `requirements.txt`

The codebase is a well-structured Flask application serving a ~700k-record WWI personnel database. The architecture is clean, the search/filter pipeline is thoughtfully designed, and accessibility has clearly been a first-class concern. The primary risks are a hardcoded secret key in production code, no authentication on write endpoints, unbounded image storage in SQLite BLOBs, and several redundancy and robustness issues that accumulate into meaningful technical debt.

---

## Critical Issues (Immediate Action Required)

### Issue #1: Hardcoded Secret Key in Production Code

- **Severity:** Critical
- **Category:** Security
- **Current Implementation:**

```python
# src/web_app.py line 19
app.secret_key = 'sdgw-1914-1919-secret-key-change-in-production'
```

- **Proposed Solution:**

```python
import os

def _abort_missing_secret():
    raise RuntimeError(
        "FLASK_SECRET_KEY environment variable must be set before starting the server."
    )

app.secret_key = os.environ.get('FLASK_SECRET_KEY') or _abort_missing_secret()
```

Add to `server.sh` (one-time key generation):

```bash
export FLASK_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
```

Or generate once, store in a `.env` file, and exclude from version control via `.gitignore`.

- **Reasoning:** The comment "change in production" is a known anti-pattern — it is routinely forgotten. If this key is committed to a repository and the app is ever exposed beyond localhost, session cookies can be forged, allowing privilege escalation.
- **Expected Benefits:** Eliminates session-forgery risk; forces a deliberate deployment step.
- **Trade-offs:** Requires one-time environment setup.
- **Effort Estimate:** Small
- **Priority:** Must-fix

---

### Issue #2: No Authentication or Rate-Limiting on Write Endpoints

- **Severity:** Critical
- **Category:** Security
- **Current Implementation:**

```python
# src/web_app.py lines 1502–1579
@app.route('/record/<record_type>/<int:record_id>/annotation', methods=['GET', 'POST'])
def manage_annotation(record_type, record_id):
    ...
    user_name = request.form.get('user_name', 'Anonymous')  # Fully user-controlled
```

Any anonymous user can POST to `/record/*/annotation`, `/record/*/upload-image`, or `/image/*/delete` with no authentication. The only guard is `confirmed == 'yes'` — a trivially satisfied form field. The `user_name` is entirely self-reported.

- **Proposed Solution:**

At minimum, add a shared write-access passphrase checked server-side:

```python
WRITE_PASSPHRASE = os.environ.get('SDGW_WRITE_PASSPHRASE', '')

def _check_write_auth():
    if WRITE_PASSPHRASE and request.form.get('passphrase') != WRITE_PASSPHRASE:
        flash('Incorrect passphrase.', 'error')
        return False
    return True
```

Apply at the top of each write route. Also add rate-limiting via `flask-limiter` on upload and annotation routes to prevent abuse.

- **Reasoning:** Anyone who can reach the server can create, overwrite, or delete annotations and images for any record, and attribute them to any name.
- **Expected Benefits:** Prevents vandalism and data corruption of user-contributed content.
- **Trade-offs:** Adds small UX friction for legitimate contributors.
- **Effort Estimate:** Small–Medium
- **Priority:** Must-fix

---

## High Priority Issues

### Issue #3: Images Stored as BLOBs in SQLite — Scalability Risk

- **Severity:** High
- **Category:** Performance / Architecture
- **Current Implementation:**

```python
# src/annotations.py lines 200–215
cursor = conn.execute("""
    INSERT INTO record_images
    (record_type, record_id, image_data, ...)
    VALUES (?, ?, ?, ...)
""", (record_type, record_id, image_data, ...))
```

```sql
-- src/schema_amendments.sql line 83
image_data BLOB NOT NULL,
```

- **Proposed Solution:**

Store images on the filesystem and keep only the relative path in the database:

```python
import uuid
IMAGE_STORE = Path(os.environ.get('SDGW_IMAGE_DIR', 'data/images'))

def upload_image(self, record_type, record_id, image_data, user_identifier, metadata=None):
    mime_type = self.validate_image(image_data)
    ext = mime_type.split('/')[1]
    filename = f"{record_type}_{record_id}_{uuid.uuid4().hex}.{ext}"
    dest = IMAGE_STORE / filename
    IMAGE_STORE.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(image_data)
    # Store filename in DB instead of BLOB
```

- **Reasoning:** SQLite is not designed for large BLOB storage. With 10 MB per image and potentially thousands of records, the database file will balloon, degrading query performance across the entire application. SQLite also holds a write lock during BLOB reads, blocking all other writes.
- **Expected Benefits:** Dramatically smaller DB file; faster queries; standard HTTP caching for images; easier backup separation.
- **Trade-offs:** Requires filesystem management; backup strategy must include image directory.
- **Effort Estimate:** Medium
- **Priority:** Should-fix

---

### Issue #4: `_build_where` Function is Dead Code — Redundant with `_build_conditions`

- **Severity:** High
- **Category:** Code Quality / Redundancy
- **Current Implementation:**

```python
# src/web_app.py lines 1371–1397
def _build_where(table, surname, christian_names, service_number,
                 birth_town, death_date_from, death_date_to):
    """Build WHERE clause using only index-friendly conditions for fast DB scan."""
    conditions = ["1=1"]
    params = []
    if surname:
        conditions.append("surname LIKE ?")
        ...
```

This function duplicates a subset of `_build_conditions` (lines 235–306) and is **never called anywhere in the codebase**. It was likely a precursor to `_build_conditions` that was never removed.

- **Proposed Solution:**

Delete `_build_where` entirely (lines 1371–1397 of `src/web_app.py`). Verify first:

```bash
grep -rn "_build_where" src/
```

- **Reasoning:** Dead code increases cognitive load, creates maintenance confusion (which function should be updated when logic changes?), and may mislead future developers into thinking it is used.
- **Expected Benefits:** Reduced codebase size; eliminates a maintenance trap.
- **Trade-offs:** None.
- **Effort Estimate:** Small
- **Priority:** Must-fix

---

### Issue #5: Duplicate `fields` Dict Construction in `manage_annotation`

- **Severity:** High
- **Category:** Redundancy / Maintainability
- **Current Implementation:**

```python
# src/web_app.py lines 1520–1536 (create branch) and 1545–1561 (update branch)
# Identical 15-field dict built twice:
fields = {
    'additional_names': request.form.get('additional_names'),
    'birth_date': request.form.get('birth_date'),
    'birth_place_detail': request.form.get('birth_place_detail'),
    'family_info': request.form.get('family_info'),
    'pre_war_occupation': request.form.get('pre_war_occupation'),
    'enlistment_details': request.form.get('enlistment_details'),
    'service_notes': request.form.get('service_notes'),
    'casualty_details': request.form.get('casualty_details'),
    'burial_memorial': request.form.get('burial_memorial'),
    'medals_honors': request.form.get('medals_honors'),
    'personal_effects': request.form.get('personal_effects'),
    'newspaper_mentions': request.form.get('newspaper_mentions'),
    'family_stories': request.form.get('family_stories'),
    'research_notes': request.form.get('research_notes'),
    'sources': request.form.get('sources'),
}
```

- **Proposed Solution:**

```python
ANNOTATION_FORM_FIELDS = (
    'additional_names', 'birth_date', 'birth_place_detail', 'family_info',
    'pre_war_occupation', 'enlistment_details', 'service_notes',
    'casualty_details', 'burial_memorial', 'medals_honors',
    'personal_effects', 'newspaper_mentions', 'family_stories',
    'research_notes', 'sources',
)

def _annotation_fields_from_form():
    return {f: request.form.get(f) for f in ANNOTATION_FORM_FIELDS}
```

Then in both branches: `fields = _annotation_fields_from_form()`

- **Reasoning:** Any future field addition requires two edits; one will inevitably be missed, causing silent divergence between create and update behaviour.
- **Expected Benefits:** Single point of change; eliminates divergence risk.
- **Trade-offs:** None.
- **Effort Estimate:** Small
- **Priority:** Must-fix

---

### Issue #6: Record Navigation Executes Up to 10 SQL Queries Per Detail Page Load

- **Severity:** High
- **Category:** Performance
- **Current Implementation:**

```python
# src/web_app.py lines 856–891
_, total, _ = _run_search(db, search_p, sort, limit=0, offset=0)    # 2 queries
first_results, _, _ = _run_search(db, search_p, sort, limit=1, offset=0)          # 2 queries
prev_results,  _, _ = _run_search(db, search_p, sort, limit=1, offset=pos - 1)    # 2 queries
next_results,  _, _ = _run_search(db, search_p, sort, limit=1, offset=pos + 1)    # 2 queries
last_results,  _, _ = _run_search(db, search_p, sort, limit=1, offset=total - 1)  # 2 queries
```

Each `_run_search` call issues 2 SQL queries (data + count). For the `all` record type this becomes a UNION query. A single detail page load with navigation context can execute **up to 10 SQL queries** just for prev/next links.

- **Proposed Solution:**

Fetch a window of 3 records (prev, current, next) in a single query using `OFFSET max(0, pos-1) LIMIT 3`, and derive first/last from the already-known total:

```python
# 1 count query + 1 window query = 2 total
_, total, _ = _run_search(db, search_p, sort, limit=0, offset=0)
window, _, _ = _run_search(db, search_p, sort, limit=3, offset=max(0, pos - 1))
# window[0] = prev (if pos > 0), window[1] = current, window[2] = next
# First/last: fetch lazily client-side via API if needed
```

- **Reasoning:** On a slow filter (complex multi-field query, large result set), this multiplies latency by 5x on every detail page view with search context.
- **Expected Benefits:** Up to 80% reduction in DB queries per detail page load with navigation.
- **Trade-offs:** Slightly more complex window-slicing logic; first/last links may require a separate lightweight fetch.
- **Effort Estimate:** Medium
- **Priority:** Should-fix

---

## Medium Priority Issues

### Issue #7: In-Memory Filter Cache is Not Thread-Safe

- **Severity:** Medium
- **Category:** Bug / Concurrency
- **Current Implementation:**

```python
# src/web_app.py lines 75, 337–343
_filter_options_cache = {}

def _set_cached_filter_payload(cache_key, payload):
    _filter_options_cache[cache_key] = (time.monotonic(), payload)
    while len(_filter_options_cache) > FILTER_OPTIONS_CACHE_MAX_ENTRIES:
        oldest_key = min(_filter_options_cache, key=lambda k: _filter_options_cache[k][0])
        _filter_options_cache.pop(oldest_key, None)
```

The eviction loop reads and mutates `_filter_options_cache` without a lock. Under a multi-threaded WSGI server (gunicorn with threads), concurrent writes can cause a `RuntimeError: dictionary changed size during iteration`.

- **Proposed Solution:**

```python
import threading
_filter_options_cache = {}
_filter_options_cache_lock = threading.Lock()

def _set_cached_filter_payload(cache_key, payload):
    with _filter_options_cache_lock:
        _filter_options_cache[cache_key] = (time.monotonic(), payload)
        while len(_filter_options_cache) > FILTER_OPTIONS_CACHE_MAX_ENTRIES:
            oldest_key = min(_filter_options_cache, key=lambda k: _filter_options_cache[k][0])
            _filter_options_cache.pop(oldest_key, None)

def _get_cached_filter_payload(cache_key):
    with _filter_options_cache_lock:
        cached = _filter_options_cache.get(cache_key)
        if not cached:
            return None
        cached_at, payload = cached
        if (time.monotonic() - cached_at) > FILTER_OPTIONS_CACHE_TTL_SECONDS:
            _filter_options_cache.pop(cache_key, None)
            return None
        return payload
```

- **Reasoning:** CPython's GIL protects individual dict operations but not compound read-modify-write sequences like the eviction loop.
- **Expected Benefits:** Eliminates race condition under concurrent load.
- **Trade-offs:** Negligible lock contention given the cache's small size.
- **Effort Estimate:** Small
- **Priority:** Should-fix

---

### Issue #8: `AnnotationManager` Opens a New DB Connection Per Method Call

- **Severity:** Medium
- **Category:** Performance / Architecture
- **Current Implementation:**

```python
# src/annotations.py lines 23–27
def _get_connection(self):
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    return conn
```

Every `get_annotation`, `get_images`, `create_annotation`, etc. opens a fresh SQLite connection. On a detail page load, `get_annotation` and `get_images` are called separately — two connections where one would suffice. This is also entirely separate from Flask's `g`-scoped `get_db()` connection, meaning a single request holds two open SQLite connections simultaneously.

- **Proposed Solution:**

Refactor `get_annotation_manager()` to pass the existing request-scoped connection:

```python
# src/web_app.py
def get_annotation_manager():
    if 'annotation_manager' not in g:
        g.annotation_manager = AnnotationManager(get_db())
    return g.annotation_manager
```

```python
# src/annotations.py
class AnnotationManager:
    def __init__(self, db):
        self._db = db  # Accept existing connection

    def _get_connection(self):
        return self._db  # No-op; use shared connection
```

- **Reasoning:** Opening connections repeatedly in a request cycle adds latency and wastes file descriptors.
- **Expected Benefits:** Halves connection overhead on detail pages; simplifies transaction boundaries.
- **Trade-offs:** `AnnotationManager` no longer owns its connection lifecycle; callers must ensure the connection stays open.
- **Effort Estimate:** Medium
- **Priority:** Should-fix

---

### Issue #9: `update_annotation` Accepts Arbitrary Field Names Without Validation

- **Severity:** Medium
- **Category:** Security / Bug
- **Current Implementation:**

```python
# src/annotations.py lines 115–123
set_clause = ', '.join([f"{field}=?" for field in fields.keys()])
query = f"""
    UPDATE record_annotations
    SET {set_clause}, modified_at=datetime('now'), modified_by=?
    WHERE annotation_id=?
"""
values = list(fields.values()) + [user_identifier, annotation_id]
conn.execute(query, values)
```

The `fields` dict keys are interpolated directly into the SQL string. While values are parameterised, **column names are not**. A caller passing `{'is_active': 0}` or `{'annotation_id': 999}` would silently corrupt metadata columns.

- **Proposed Solution:**

```python
VALID_ANNOTATION_FIELDS = frozenset({
    'additional_names', 'birth_date', 'birth_place_detail', 'family_info',
    'pre_war_occupation', 'enlistment_details', 'service_notes',
    'casualty_details', 'burial_memorial', 'medals_honors',
    'personal_effects', 'newspaper_mentions', 'family_stories',
    'research_notes', 'sources'
})

def update_annotation(self, annotation_id, user_identifier, fields, change_reason=None):
    safe_fields = {k: v for k, v in fields.items() if k in VALID_ANNOTATION_FIELDS}
    if not safe_fields:
        raise ValueError("No valid fields to update")
    ...
```

- **Reasoning:** Defence-in-depth: the data layer should not trust callers to pass only safe column names.
- **Expected Benefits:** Prevents accidental or malicious metadata field corruption.
- **Trade-offs:** None.
- **Effort Estimate:** Small
- **Priority:** Must-fix

---

### Issue #10: `_collect_distinct_text_values` Uses f-string Column Interpolation Without Internal Guard

- **Severity:** Medium
- **Category:** Security
- **Current Implementation:**

```python
# src/web_app.py lines 362–376
rows = db.execute(
    f"SELECT DISTINCT o.{field_name} FROM officers o "
    f"WHERE o.{field_name} IS NOT NULL AND o.{field_name} != '' AND {where_o} "
    f"ORDER BY o.{field_name} LIMIT ?",
    bound_o + [limit]
)
```

`field_name` is interpolated directly into the SQL string. It is validated against `FILTER_TEXT_SUGGEST_FIELDS` at the call site in `_collect_text_suggestions`, but `_collect_distinct_text_values` itself has no guard. The same pattern appears in `_collect_cascaded_surnames` and `_collect_distinct_ids`.

- **Proposed Solution:**

Add an allowlist assertion at the top of each function:

```python
_SAFE_TEXT_COLUMNS = frozenset(FILTER_TEXT_SUGGEST_FIELDS) | {
    'surname', 'regiment_id', 'battalion_id', 'rank_id'
}

def _collect_distinct_text_values(db, params, field_name, ...):
    assert field_name in _SAFE_TEXT_COLUMNS, f"Unsafe column name: {field_name!r}"
    ...
```

- **Reasoning:** Column names cannot be parameterised in SQLite; an explicit allowlist at the function boundary is the correct mitigation. Current validation is only at the call site.
- **Expected Benefits:** Prevents SQL injection if the function is ever called from a new code path without the upstream guard.
- **Trade-offs:** None.
- **Effort Estimate:** Small
- **Priority:** Should-fix

---

### Issue #11: `fuzzy_suggest` Runs Up to 22 Queries Per Request with No Caching

- **Severity:** Medium
- **Category:** Performance
- **Current Implementation:**

```python
# src/web_app.py lines 1314–1338
# Strategy 2: Character transposition
for i in range(len(q) - 1):
    swapped = q[:i] + q[i+1] + q[i] + q[i+2:]
    for tbl in tables:
        rows = db.execute(...)  # (len(q)-1) * len(tables) queries

# Strategy 3: Wildcard per character
for i in range(len(q)):
    pattern = q[:i] + '_' + q[i+1:] + '%'
    for tbl in tables:
        rows = db.execute(...)  # len(q) * len(tables) queries
```

For a 6-character query against 2 tables, strategies 2 and 3 together issue up to `(5 + 6) * 2 = 22` additional queries. These are unindexed `LIKE '%...'` patterns on tables with 700k rows. There is no caching.

- **Proposed Solution:**

1. Apply the same bounded TTL cache used for `/api/filter-options`.
2. Only trigger strategies 2 and 3 when `len(exact) == 0` (not `< 5`).
3. Long-term: pre-compute a trigram or soundex index for fuzzy matching.

- **Reasoning:** A user typing quickly can fire multiple fuzzy-suggest requests in rapid succession, each potentially issuing 20+ slow queries against large unindexed columns.
- **Expected Benefits:** Significant reduction in DB load for fuzzy search interactions.
- **Trade-offs:** Cache adds memory; trigram index adds schema complexity.
- **Effort Estimate:** Medium
- **Priority:** Should-fix

---

### Issue #12: `_with_group` in `fuzzy_suggest` is an N+1 Query Pattern

- **Severity:** Medium
- **Category:** Performance
- **Current Implementation:**

```python
# src/web_app.py lines 1344–1361
def _with_group(values, field_name):
    if field_name == 'birth_town':
        grouped = []
        for v in sorted(values):
            row = db.execute(
                "SELECT region FROM birth_town_region WHERE birth_town = ? LIMIT 1", (v,)
            ).fetchone()  # One query per value — N+1
            grouped.append({'value': v, 'group': row[0] if row else 'Other'})
        return grouped
```

If `fuzzy_suggest` returns 30 birth towns, this issues 30 individual queries to `birth_town_region`.

- **Proposed Solution:**

```python
def _with_group(values, field_name):
    if field_name == 'birth_town':
        sorted_vals = sorted(values)
        if not sorted_vals:
            return []
        ph = ','.join('?' * len(sorted_vals))
        region_map = {
            r[0]: r[1] for r in db.execute(
                f"SELECT birth_town, region FROM birth_town_region WHERE birth_town IN ({ph})",
                sorted_vals
            )
        }
        return [{'value': v, 'group': region_map.get(v, 'Other')} for v in sorted_vals]
    elif field_name == 'enlistment_loc':
        sorted_vals = sorted(values)
        if not sorted_vals:
            return []
        ph = ','.join('?' * len(sorted_vals))
        region_map = {
            r[0]: r[1] for r in db.execute(
                f"SELECT enlistment_loc, region FROM enlistment_region WHERE enlistment_loc IN ({ph})",
                sorted_vals
            )
        }
        return [{'value': v, 'group': region_map.get(v, 'Other')} for v in sorted_vals]
    return [{'value': v} for v in sorted(values)]
```

- **Reasoning:** Classic N+1 query problem; a single IN-clause query replaces N round-trips.
- **Expected Benefits:** Reduces group-lookup from O(N) queries to O(1).
- **Trade-offs:** None.
- **Effort Estimate:** Small
- **Priority:** Should-fix

---

### Issue #13: `get_row_count` in `DataExtractor` Exports the Entire Table to Count Rows

- **Severity:** Medium
- **Category:** Performance
- **Current Implementation:**

```python
# src/data_access.py lines 138–146
def get_row_count(self, table_name: str) -> int:
    result = self._run_mdb_command(
        ["mdb-export", str(self.mdb_path), table_name],
        timeout=600,
    )
    lines = result.stdout.strip().split("\n")
    return max(0, len(lines) - 1)
```

This exports the full table content (potentially 660k rows of soldier data) just to count lines. The method is also not called anywhere in the current codebase — it is dead code.

- **Proposed Solution:**

Remove the method, or if retained, add a prominent warning docstring:

```python
def get_row_count(self, table_name: str) -> int:
    """WARNING: Exports full table to count rows. O(N) in table size.
    Use only in offline migration/validation scripts, never in a web request."""
    ...
```

- **Reasoning:** Calling this on `SOLDIERS` (661k rows) would export ~50MB of CSV just to return an integer.
- **Expected Benefits:** Prevents accidental misuse; reduces confusion.
- **Trade-offs:** None.
- **Effort Estimate:** Small
- **Priority:** Should-fix

---

### Issue #14: `validate_export` Loads Entire CSV Files into Memory

- **Severity:** Medium
- **Category:** Performance / Memory
- **Current Implementation:**

```python
# src/data_access.py lines 266–268
reader = csv.reader(f)
columns = next(reader, [])
rows = list(reader)  # Loads all 660k soldier rows into memory at once
actual_rows = len(rows)
```

- **Proposed Solution:**

```python
reader = csv.reader(f)
columns = next(reader, [])
actual_rows = 0
sample_rows = []
for row in reader:
    actual_rows += 1
    if actual_rows <= 5:
        sample_rows.append(row)
```

Then use `sample_rows` for spot-check validation instead of `random.sample(rows, ...)`.

- **Reasoning:** `list(reader)` on the SOLDIERS table allocates a list of ~660k lists in memory. On a machine with limited RAM this can cause OOM or significant GC pressure.
- **Expected Benefits:** O(1) memory usage regardless of table size.
- **Trade-offs:** Spot check uses first 5 rows rather than a random sample; randomness can be restored with reservoir sampling if needed.
- **Effort Estimate:** Small
- **Priority:** Should-fix

---

### Issue #15: `UNIQUE(record_type, record_id, is_active)` Does Not Correctly Enforce One Active Annotation Per Record

- **Severity:** Medium
- **Category:** Bug / Data Integrity
- **Current Implementation:**

```sql
-- src/schema_amendments.sql line 41
UNIQUE(record_type, record_id, is_active)
```

This prevents two rows with the same `(record_type, record_id, is_active)` triple. Since `is_active` is `0` or `1`, the constraint also prevents having more than one soft-deleted annotation for the same record — which is the opposite of the intent. The intent is "at most one *active* annotation per record".

- **Proposed Solution:**

Remove the UNIQUE constraint from the table definition and use a partial index instead:

```sql
CREATE UNIQUE INDEX idx_one_active_annotation
    ON record_annotations(record_type, record_id)
    WHERE is_active = 1;
```

- **Reasoning:** A partial unique index on `WHERE is_active = 1` correctly enforces "at most one active annotation per record" while allowing multiple soft-deleted rows for audit history.
- **Expected Benefits:** Correct data integrity semantics; allows proper soft-delete history accumulation.
- **Trade-offs:** Requires a schema migration (drop constraint, create index).
- **Effort Estimate:** Small
- **Priority:** Should-fix

---

*Continued in Part 2: Low Priority Issues, Quick Wins, Long-term Improvements, Positive Findings, and Recommendations Summary.*
