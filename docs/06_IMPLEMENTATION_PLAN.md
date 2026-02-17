# Implementation Plan

## SDGW 1914-1919 Personnel Database Modernization

**Version:** 1.0  
**Date:** 16 February 2026  
**Status:** Ready for Execution  
**Audience:** Engineering Team

---

## 1. Executive Summary

This document outlines the step-by-step build plan to modernize access to 703,806 historical military personnel records (1914-1919). The initiative consists of three integrated phases:

1. **Phase A: Data Access** – Extract data from legacy `.mdb` file
2. **Phase B: Data Migration** – Load into modern SQLite database
3. **Phase C: Basic UI** – Build accessible web interface for searching

**Total Timeline:** 8 weeks (concurrent phases possible)  
**Team Size:** 3-4 engineers + 1 data steward  
**Target Launch:** End of Week 8

---

## 2. Project Structure

```text
sdgw-1914-1919/
├── README.md                              [Project overview]
├── docs/
│   ├── 01_DATA_ACCESS_PLAN.md            [This phase]
│   ├── 02_ACCESS_REPORT.md               [Current status]
│   ├── 03_PRD_A_DATA_ACCESS_LAYER.md     [Requirements]
│   ├── 04_PRD_B_DATA_MIGRATION.md        [Requirements]
│   ├── 05_PRD_C_BASIC_UI.md              [Requirements]
│   └── IMPLEMENTATION_PLAN.md            [This document]
├── data/
│   ├── sd_2011.mdb                       [Source database]
│   ├── sd_2011.mdb.backup/               [Backups]
│   ├── exports/                          [CSV exports]
│   └── sd_2011.db                        [SQLite target]
├── src/
│   ├── data_access.py                    [Phase A: Extraction module]
│   ├── data_migration.py                 [Phase B: Migration scripts]
│   ├── web_app.py                        [Phase C: Flask app]
│   ├── scripts/
│   │   ├── export_data.py                [Run export]
│   │   ├── backup.py                     [Create backup]
│   │   ├── validate_export.py            [Validate CSVs]
│   │   ├── migrate_personnel.py          [Load into SQLite]
│   │   ├── validate_migration.py         [Verify migration]
│   │   └── rollback.py                   [Restore from CSV]
│   └── templates/
│       ├── home.html                     [Home page]
│       ├── search_results.html           [Results list]
│       └── detail.html                   [Record detail]
├── tests/
│   ├── test_data_access.py               [Unit tests]
│   ├── test_migration.py                 [Integration tests]
│   └── test_ui.py                        [Acceptance tests]
├── requirements.txt                      [Python dependencies]
├── setup.py                              [Package setup]
└── CHANGELOG.md                          [Version history]
```

---

## 3. Phase A: Data Access Layer (Weeks 1-2)

### A.1 Objectives

- ✓ Verify database accessibility (COMPLETED – see Access Report)
- Extract all tables to CSV format
- Validate data integrity
- Document process for team

### A.2 Detailed Tasks

#### Task A.1: Implement DataExtractor Module

**Owner:** Engineer 1  
**Duration:** 1.5 days  
**Deliverable:** `src/data_access.py`

**Implementation Steps:**

1. Create `DataExtractor` class with methods:
   - `__init__(mdb_path, log_handler)`
   - `get_tables()` – returns list of 7 tables
   - `extract_table(table_name, output_csv)` – single table export
   - `export_all(output_dir)` – export all tables with retry logic
   - `validate_export(export_dir)` – checksum verification
   - `create_backup(backup_dir)` – create timestamped MDB backup

2. Implement error handling:
   - File not found → clear error message
   - mdbtools not installed → suggest: `brew install mdbtools`
   - Timeout on large table → retry with longer timeout
   - Insufficient disk space → warn user

3. Add logging:
   - Log file: `logs/data_access.log`
   - Include: timestamp, component, table, operation, result, duration
   - Rotation: daily; retention: 30 days

**Acceptance Criteria:**

- [ ] All 7 tables exported successfully
- [ ] Errors logged with stack traces
- [ ] CSV format valid (parseable by Python csv module)
- [ ] Performance: OFFICERS export < 30s, SOLDIERS < 5 min
- [ ] Code has docstrings and type hints
- [ ] Unit tests pass (80%+ coverage)

**Testing:**

```bash
pytest tests/test_data_access.py::TestDataExtractor
# Expected: 12/12 tests pass
```

---

#### Task A.2: Create Export Script

**Owner:** Engineer 1  
**Duration:** 0.5 days  
**Deliverable:** `src/scripts/export_data.py`

**Script Responsibilities:**

1. Initialize DataExtractor with source MDB path
2. Create `data/exports/` directory
3. Export all tables to CSV
4. Validate exports (row counts, checksums)
5. Report summary to console + log file
6. Exit with status code (0 = success, 1 = failure)

**Example Usage:**

```bash
python src/scripts/export_data.py
# Output:
# [2026-02-16 10:30:22] INFO - Export started
# [2026-02-16 10:30:25] INFO - Exported SD_RANKS (547 rows)
# [2026-02-16 10:30:28] INFO - Exported SD_Battalions (721 rows)
# ... (more tables)
# [2026-02-16 10:35:00] INFO - All exports complete (6 success, 0 failed)
```

**Acceptance Criteria:**

- [ ] Script runs from project root
- [ ] Empty output directory verified
- [ ] All CSVs created in `data/exports/`
- [ ] Exit code 0 on success, 1 on error
- [ ] Can be run multiple times (overwrites previous exports)

---

#### Task A.3: Create Validation Script

**Owner:** Engineer 1  
**Duration:** 1 day  
**Deliverable:** `src/scripts/validate_export.py`

**Validation Tasks:**

1. Row count verification:

   ```text
   SD_RANKS: Expected 547, Got 547 ✓
   OFFICERS: Expected 41,846, Got 41,846 ✓
   SOLDIERS: Expected 661,960, Got 661,960 ✓
   ```

2. Checksum verification (CRC32 of CSV content)

3. Spot checks (5 random records per table):
   - Read CSV row
   - Verify all columns present
   - Verify no truncation (text length reasonable)
   - Verify encoding (UTF-8)

4. Generate validation report (HTML + console)

**Example Output:**

```text
VALIDATION REPORT
═══════════════════════════════════════════
Date: 2026-02-16 10:35:00
Status: PASS ✓

Tables Checked: 7
Rows Validated: 703,806
Errors Found: 0
Warnings: 0

Detailed Results:
─────────────────
✓ SD_RANKS (547 rows)
  Checksum: abc123def456
  Spot checks: 5/5 pass
  
✓ OFFICERS (41,846 rows)
  Checksum: xxx789yyy000
  Spot checks: 5/5 pass
  
✓ SOLDIERS (661,960 rows)
  Checksum: zzz111aaa222
  Spot checks: 5/5 pass
  
... (more tables)

CONCLUSION: All validations passed ✓
═══════════════════════════════════════════
```

**Acceptance Criteria:**

- [ ] Reads all CSVs from `data/exports/`
- [ ] Compares row counts with expected values
- [ ] Reports exact vs expected counts
- [ ] Flags discrepancies > 1 row
- [ ] Generates HTML report + console summary
- [ ] Email report option (Phase 2)

---

#### Task A.4: Create Backup Script

**Owner:** Engineer 2 (parallel)  
**Duration:** 0.5 days  
**Deliverable:** `src/scripts/backup.py`

**Functionality:**

1. Create backup of source `sd_2011.mdb`
2. Timestamp format: `sd_2011.mdb.backup.20260216_103022`
3. Store in `data/backups/`
4. Verify backup integrity (file size matches original)
5. Keep last 5 backups; delete older ones
6. Log backup operation

**Usage:**

```bash
python src/scripts/backup.py
# Output:
# Created backup: data/backups/sd_2011.mdb.backup.20260216_103022
# Verified: file size 156 MB ✓
```

**Acceptance Criteria:**

- [ ] Backup created with timestamp
- [ ] File size verified (matches original ±0 bytes)
- [ ] Old backups pruned (keep last 5)
- [ ] Script idempotent (can run multiple times safely)

---

#### Task A.5: Documentation & Testing

**Owner:** Engineer 2  
**Duration:** 1 day  
**Deliverable:** README + test suite

**Documentation:**

1. Create `README.md` with:
   - Project overview (1 paragraph)
   - Quick start (5 steps to set up)
   - Architecture diagram (Phase A, B, C overview)
   - Troubleshooting guide (10 common issues)
   - Links to PRDs (A, B, C)

2. Update docs with results:
   - Access Report (already in docs/02_ACCESS_REPORT.md)
   - Data summary (7 tables, 703,806 records)

**Testing:**

1. Create test suite: `tests/test_data_access.py`

   ```python
   class TestDataExtractor:
       def test_export_ranks(self): ...
       def test_export_officers(self): ...
       def test_export_soldiers(self): ...
       def test_validate_row_counts(self): ...
       def test_backup_creation(self): ...
       # ... 12 tests total
   ```

2. Run tests:

   ```bash
   pytest tests/test_data_access.py -v --cov=src/data_access
   # Expected: 12/12 pass, 85%+ coverage
   ```

**Acceptance Criteria:**

- [ ] README clear and complete
- [ ] README has troubleshooting section
- [ ] All unit tests pass
- [ ] Coverage >= 80%
- [ ] Code follows PEP 8 style guide

---

### A.3 Phase A Timeline

| Week   | Mon              | Tue            | Wed             | Thu              | Fri      |
|--------|------------------|----------------|-----------------|------------------|----------|
| Week 1 | Task A.1 (start) | A.1 (cont)     | A.1 (finish)    | Task A.2         | Task A.3 |
| Week 2 | Task A.4         | A.5 Testing    | A.5 Docs        | Integration test | Sign-off |

**Milestone:** Phase A complete by end of Friday, Week 2

- All exports completed ✓
- All validations passed ✓
- Documentation complete ✓
- Stakeholder approval ✓

---

## 4. Phase B: Data Migration (Weeks 2-4)

### B.1 Objectives

- Create SQLite schema (normalized design)
- Load CSV data into database
- Validate migration (row counts, checksums, foreign keys)
- Prepare for Phase C (UI development)

### B.2 Detailed Tasks

#### Task B.1: Design & Create Schema

**Owner:** Engineer 3 + Data Steward  
**Duration:** 1 day  
**Deliverable:** `src/schema.sql`

**SQL Tasks:**

1. Create tables:
   - `ranks` (547 rows)
   - `battalions_sd` (721 rows)
   - `battalions_od` (480 rows)
   - `regiment_battalion_associations` (3,649 rows)
   - `officers` (41,846 rows)
   - `soldiers` (661,960 rows)

2. Add indexes (see PRD B, Section 9):
   - Foreign key indexes
   - Search indexes (surname, service_number)
   - Filter indexes (battalion, rank, death_date)

3. Add constraints:
   - PRIMARY KEY on all tables
   - UNIQUE on id fields
   - FOREIGN KEY constraints
   - NOT NULL on required fields

4. Create ERD diagram:

   ```text
   ranks ←── officers
          ←── soldiers
   
   battalions_sd ←── regiment_battalion_associations
   
   officers → rank (via rank_id)
   officers → battalion_sd (via battalion_id)
   
   soldiers → rank (via rank_id)
   soldiers → battalion_sd (via battalion_id)
   ```

**SQL Schema File:**

- Located: `src/schema.sql`
- Contains: CREATE TABLE + CREATE INDEX statements
- Version controlled in Git
- ~150 lines total

**Acceptance Criteria:**

- [ ] All table definitions present
- [ ] All columns match PRD B schema
- [ ] All indexes defined
- [ ] Foreign key constraints specified
- [ ] Schema validated by data steward
- [ ] ERD diagram reviewed and approved

---

#### Task B.2: Implement Data Loading Scripts

**Owner:** Engineer 3  
**Duration:** 2 days  
**Deliverable:** `src/data_migration.py` + scripts

**Implementation:**

1. Create `DataMigrator` class:

   ```python
   class DataMigrator:
       def load_ranks(self, csv_file: str) -> MigrationResult
       def load_battalions_sd(self, csv_file: str) -> MigrationResult
       def load_battalion_associations(self, csv_file: str) -> MigrationResult
       def load_officers(self, csv_file: str) -> MigrationResult
       def load_soldiers(self, csv_file: str, chunk_size: int) -> MigrationResult
   ```

2. Implement type conversions (see PRD B, Section 6.1):
   - Parse integer IDs
   - Convert dates (MM/DD/YY → YYYY-MM-DD)
   - Handle NULL values
   - Trim whitespace

3. Implement error handling:
   - Row parsing errors → log + skip
   - FK violations → assign default value + log
   - Duplicate keys → skip + log
   - Timeout → log + raise

4. Create migration pipeline:

   ```text
   CSV (0) → Parse → Validate → DB insert → Log
              ↓       ↓           ↓          ↓
             errors field-level FK-level row-level
   ```

**Chunked Loading (for SOLDIERS):**

```python
# Load 5,000 rows at a time for memory efficiency
for chunk in data_migrator.chunk_soldiers(csv_file, chunk_size=5000):
    data_migrator.load_chunk(chunk)
    # commit every 5,000 rows
```

**Acceptance Criteria:**

- [ ] All 7 tables load from CSV
- [ ] Type conversions correct
- [ ] Errors logged with row numbers
- [ ] No data loss (row count ≥ expected)
- [ ] Performance: all tables load in < 10 minutes
- [ ] Memory usage < 2 GB peak

---

#### Task B.3: Create Validation Suite

**Owner:** Engineer 3  
**Duration:** 1.5 days  
**Deliverable:** `src/scripts/validate_migration.py`

**Validation Tasks:**

1. Row count verification:

   ```python
   def verify_row_counts():
       expected = {
           'ranks': 547,
           'officers': 41846,
           'soldiers': 661960,
           # ...
       }
       actual = {table: db.row_count(table) for table in expected}
       assert actual == expected or within_tolerance(actual, expected)
   ```

2. Referential integrity check:

   ```sql
   -- Find orphaned FK references
   SELECT COUNT(*) FROM officers 
   WHERE battalion_id NOT IN (SELECT battalion_id FROM battalions_sd)
   -- Expected: 0 rows
   ```

3. Spot checks (5 records per table):
   - Read from DB
   - Re-read from CSV
   - Compare field-by-field
   - Log any discrepancies

4. Data completeness:

   ```sql
   -- Check for unexpected NULLs in required fields
   SELECT COUNT(*) FROM soldiers WHERE surname IS NULL
   -- Expected: 0 rows
   ```

5. Performance testing:

   ```python
   # Example: Query should complete in < 1 second
   query_time = time.time()
   results = db.query("SELECT * FROM officers WHERE battalion_id = 1")
   assert time.time() - query_time < 1.0  # < 1 second
   ```

**Validation Report Output:**

```text
MIGRATION VALIDATION REPORT
═══════════════════════════════════════════════════════

Migration Date: 2026-02-23 14:30:00
Database: data/sd_2011.db

STATUS: ✓ PASSED

Row Counts:
───────────
✓ ranks: 547 (expected 547)
✓ battalions_sd: 721 (expected 721)
✓ officers: 41,846 (expected 41,846)
✓ soldiers: 661,960
Total: 703,806 personnel records ✓

Referential Integrity:
──────────────────────
✓ All officers assigned to valid battalion
✓ All soldiers assigned to valid battalion
✓ All personnel assigned to valid rank
✓ No orphaned foreign keys

Spot Checks (5 records per table):
──────────────────────────────────
✓ Ranks table: 5/5 match
✓ Officers table: 5/5 match
✓ Soldiers table: 5/5 match
✓ Battalions: 5/5 match

Performance Tests:
──────────────────
✓ Single record lookup: 45ms
✓ Battalion query: 120ms
✓ Full soldier export: 890ms
Indices working correctly ✓

CONCLUSION: Migration validated ✓
═══════════════════════════════════════════════════════
```

**Acceptance Criteria:**

- [ ] All row counts within tolerance
- [ ] Zero orphaned foreign keys
- [ ] Spot check success rate 100%
- [ ] All queries complete < 1 second
- [ ] Report generated (console + HTML/CSV export)

---

#### Task B.4: Schema Versioning & Documentation

**Owner:** Engineer 2 + Data Steward  
**Duration:** 1 day  
**Deliverable:** schema documentation + version control

**Documentation Tasks:**

1. Create data dictionary: `docs/DATA_DICTIONARY.md`

   ```markdown
   ## Ranks Table
   - rank_id (INT, Primary Key): Unique identifier for rank
   - rank_original (TEXT): Original historical rank name (e.g., "ARMR./PTE.")
   - rank_normalized (TEXT): Standardized rank name for UI display
   - sort_order (INT): Display order for UI rank selection
   ... (details for each field)
   ```

2. Create migration documentation:
   - Step-by-step instructions
   - Expected runtimes
   - Troubleshooting guide

3. Version schema:
   - Tag in Git: `v1.0-schema-initial`
   - Release notes: "Initial schema for 703,806 personnel records"

4. Create ER diagram:
   - Visual representation of tables + relationships
   - Exported as PNG + source file (draw.io)

**Acceptance Criteria:**

- [ ] Data dictionary complete (all 6 tables documented)
- [ ] Each field has: type, nullable, examples, description
- [ ] ER diagram clear and accurate
- [ ] Schema versioned in Git
- [ ] Documentation accessible from README

---

### B.3 Phase B Timeline

| Week | Mon | Tue | Wed | Thu | Fri |
| ------ | ----- | ----- | ----- | ----- | ----- |
| Week 2 (overlap) | Task B.1 | Task B.2 (start) | B.2 (cont) | B.2 (finish) | — |
| Week 3 | Task B.3 (start) | B.3 (cont) | B.3 (finish) | Task B.4 | Integration test |
| Week 4 (start) | Final validation | Sign-off | — | — | — |

**Milestone:** Phase B complete by Tuesday, Week 4

- Schema created and validated ✓
- All data loaded successfully ✓
- Migration validation passed ✓
- Documentation complete ✓
- Stakeholder approval ✓

---

## 5. Phase C: Basic UI (Weeks 4-8)

### C.1 Objectives

- Build minimal, accessible web interface
- Support: search, browse, detail view
- Optimize for 65+ year old users
- Mobile-friendly (tablets)

### C.2 Detailed Tasks

#### Task C.1: Setup Flask Web App

**Owner:** Engineer 4  
**Duration:** 1 day  
**Deliverable:** `src/web_app.py` + templates

**Setup:**

1. Create Flask app structure:

   ```python
   from flask import Flask, render_template, request, jsonify
   
   app = Flask(__name__)
   app.config['DATABASE'] = 'data/sd_2011.db'
   
   @app.route('/')
   def home():
       return render_template('home.html')
   
   @app.route('/search', methods=['POST'])
   def search():
       # Handle search request
       pass
   
   @app.route('/record/<int:record_id>')
   def detail(record_id):
       # Show full record
       pass
   ```

2. Add database connectivity:

   ```python
   import sqlite3
   
   def get_db():
       db = sqlite3.connect(app.config['DATABASE'])
       db.row_factory = sqlite3.Row
       return db
   ```

3. Create development server:

   ```bash
   # Run locally for testing
   FLASK_ENV=development python src/web_app.py
   # Server running on http://localhost:5000
   ```

**Acceptance Criteria:**

- [ ] Flask app initializes without errors
- [ ] Database connection works
- [ ] Development server runs on localhost:5000
- [ ] Routes respond with correct status codes

---

#### Task C.2: Build Home Page

**Owner:** Engineer 4  
**Duration:** 1.5 days  
**Deliverables:** `src/templates/home.html` + CSS

**Implementation:**

1. Create HTML structure:
   - Title: "SDGW 1914-1919 Personnel Discovery"
   - Subtitle: "Finding your ancestor in historical records"
   - Search box (surname + optional service number)
   - Browse by battalion dropdown
   - Help/instructions section
   - Footer with links

2. Style with CSS (responsive design):
   - 18px+ base font
   - 44x44px buttons
   - 7:1 color contrast (WCAG AAA)
   - Flexbox/Grid for layout
   - Mobile-first design

3. Form validation (frontend):
   - Surname required (non-empty)
   - Service number optional
   - Empty input shows error: "Please enter a surname"

**HTML Template (Simplified):**

```html
<body>
  <header>
    <h1>SDGW 1914-1919 Personnel Discovery</h1>
    <p>Finding your ancestor in historical records</p>
  </header>
  
  <main>
    <form method="POST" action="/search">
      <label for="surname">Surname:</label>
      <input type="text" id="surname" name="surname" required 
             placeholder="e.g., SMITH" size="30">
      
      <label for="service_number">Service Number (optional):</label>
      <input type="text" id="service_number" name="service_number" 
             placeholder="Leave blank if unknown" size="30">
      
      <button type="submit">SEARCH</button>
    </form>
    
    <!-- Browse by battalion -->
    <section>
      <h2>Or Browse by Battalion</h2>
      <select id="battalion">
        <option>Choose battalion...</option>
        <option>51st Battalion</option>
        ...
      </select>
      <button onclick="browse()">BROWSE</button>
    </section>
    
    <!-- Help section -->
    <section class="help">
      <h2>How to Find Your Ancestor</h2>
      <p>↯ specific instructions here ↯</p>
    </section>
  </main>
  
  <footer>
    <p>Privacy | Contact | Home</p>
  </footer>
</body>
```

**Acceptance Criteria:**

- [ ] Page renders without errors
- [ ] Search form functional
- [ ] Buttons 44x44px minimum
- [ ] Text 18px+ for readability
- [ ] Color contrast passes WCAG AAA audit
- [ ] Works on desktop, tablet, and mobile
- [ ] Keyboard navigation works (Tab, Enter)
- [ ] Screen reader compatible

---

#### Task C.3: Build Search Results Page

**Owner:** Engineer 4  
**Duration:** 1.5 days  
**Deliverables:** `src/templates/search_results.html` + backend

**Backend Implementation:**

```python
@app.route('/search', methods=['POST'])
def search():
    surname = request.form.get('surname', '').upper().strip()
    service_number = request.form.get('service_number', '').strip()
    
    db = get_db()
    
    # Search by service number (exact match, priority)
    if service_number:
        cursor = db.execute(
            'SELECT * FROM soldiers WHERE service_number = ?',
            (service_number,)
        )
        results = cursor.fetchall()
        if len(results) == 1:
            # Redirect to detail view
            return redirect(f'/record/{results[0]["soldier_id"]}')
    
    # Search by surname
    if surname:
        cursor = db.execute('''
            SELECT 'officer' as type, O_ID as id, SURNAME, 
                   CHRST_NAME, RANK, BAT_ID, DEATH_DATE 
            FROM officers WHERE surname LIKE ? ESCAPE '!'
            UNION ALL
            SELECT 'soldier', S_ID, SURNAME, CHRST_NAME, 
                   RANK, BAT_ID, DEATH_DATE 
            FROM soldiers WHERE surname LIKE ? ESCAPE '!'
            ORDER BY type DESC, RANK, SURNAME, CHRST_NAME
        ''', (f'%{surname}%', f'%{surname}%'))
        results = cursor.fetchall()
    
    # Render results page
    return render_template(
        'search_results.html',
        query=surname,
        results=results,
        count=len(results)
    )
```

**Frontend Template:**

```html
<h2>Results: {{ count }} people named "{{ query }}"</h2>

<table>
  <tr>
    <th>Name</th>
    <th>Rank</th>
    <th>Battalion</th>
    <th>Status</th>
    <th>Action</th>
  </tr>
  
  {% for result in results %}
  <tr>
    <td>{{ result.SURNAME }}, {{ result.CHRST_NAME }}</td>
    <td>{{ result.RANK }}</td>
    <td>{{ result.BATTALION_NAME }}</td>
    <td>
      {% if result.DEATH_DATE %}
        Died {{ result.DEATH_DATE }}
      {% else %}
        Survived
      {% endif %}
    </td>
    <td>
      <a href="/record/{{ result.id }}" class="button">
        VIEW RECORD
      </a>
    </td>
  </tr>
  {% endfor %}
</table>
```

**Acceptance Criteria:**

- [ ] Search returns correct results (surname matching)
- [ ] Results sorted logically (rank, then name)
- [ ] Shows count: "14 people named SMITH"
- [ ] Each result clickable to detail view
- [ ] "Back to search" option available
- [ ] Pagination if > 20 results
- [ ] Performance: results displayed < 1 second

---

#### Task C.4: Build Detail View Page

**Owner:** Engineer 4  
**Duration:** 1 day  
**Deliverables:** `src/templates/detail.html` + backend

**Backend Implementation:**

```python
@app.route('/record/<int:officer_id>')
def detail_officer(officer_id):
    db = get_db()
    cursor = db.execute('''
        SELECT o.*, r.rank_group, b.name as battalion_name
        FROM officers o
        LEFT JOIN ranks r ON o.rank_id = r.rank_id
        LEFT JOIN battalions_sd b ON o.battalion_id = b.battalion_id
        WHERE o.officer_id = ?
    ''', (officer_id,))
    record = cursor.fetchone()
    
    if not record:
        return "Record not found", 404
    
    return render_template('detail.html', record=record, record_type='officer')

@app.route('/record/s/<int:soldier_id>')
def detail_soldier(soldier_id):
    db = get_db()
    cursor = db.execute('''
        SELECT s.*, r.rank_group, b.name as battalion_name
        FROM soldiers s
        LEFT JOIN ranks r ON s.rank_id = r.rank_id
        LEFT JOIN battalions_sd b ON s.battalion_id = b.battalion_id
        WHERE s.soldier_id = ?
    ''', (soldier_id,))
    record = cursor.fetchone()
    
    if not record:
        return "Record not found", 404
    
    return render_template('detail.html', record=record, record_type='soldier')
```

**Frontend Template:**

```html
<h1>{{ record.surname|upper }}, {{ record.christian_names }}</h1>

<section class="record-detail">
  <h2>Personal Information</h2>
  <dl>
    <dt>Name:</dt>
    <dd>{{ record.surname }}, {{ record.christian_names }}</dd>
    
    <dt>Initials:</dt>
    <dd>{{ record.initials }}</dd>
    
    {% if record_type == 'soldier' %}
    <dt>Service Number:</dt>
    <dd>{{ record.service_number }}</dd>
    {% endif %}
    
    <dt>Birth Town:</dt>
    <dd>{{ record.birth_town }}</dd>
  </dl>
  
  <h2>Military Service</h2>
  <dl>
    <dt>Rank:</dt>
    <dd>{{ record.rank_text }}</dd>
    
    <dt>Battalion:</dt>
    <dd>{{ record.battalion_name }}</dd>
    
    {% if record.decoration %}
    <dt>Decorations:</dt>
    <dd>{{ record.decoration }}</dd>
    {% endif %}
  </dl>
  
  <h2>Casualty Information</h2>
  <dl>
    {% if record.death_date %}
    <dt>Date of Death:</dt>
    <dd>{{ record.death_date }}</dd>
    
    <dt>Death Location:</dt>
    <dd>{{ record.death_location }}</dd>
    {% else %}
    <dt>Status:</dt>
    <dd>No death record (survived the war)</dd>
    {% endif %}
    
    {% if record.additional_notes %}
    <dt>Additional Notes:</dt>
    <dd>{{ record.additional_notes }}</dd>
    {% endif %}
  </dl>
</section>

<section class="actions">
  <button onclick="print()">PRINT THIS PAGE</button>
  <button onclick="history.back()">BACK TO RESULTS</button>
</section>
```

**Acceptance Criteria:**

- [ ] All record fields displayed (no hidden or truncated data)
- [ ] Fields grouped logically
- [ ] Print button creates printer-friendly version
- [ ] Back button returns to search results
- [ ] 100% field population (no NULL values shown as empty)
- [ ] Performance: page loads < 500ms

---

#### Task C.5: Accessibility & Testing

**Owner:** Engineer 4  
**Duration:** 1 day  
**Deliverables:** Accessibility audit + test suite

**Accessibility Tasks:**

1. Run WAVE audit (Web Accessibility Evaluation Tool):

   ```text
   Expected: 0 errors, 0 contrast errors
   ```

2. Keyboard navigation test:
   - Tab through all interactive elements
   - Tab order follows visual flow
   - Esc key returns to home
   - Enter key submits forms

3. Screen reader test (NVDA):
   - All images have alt text
   - Form labels associated
   - Page structure semantic (`<h1>`, `<p>`, `<button>`)
   - No keyboard traps

4. Mobile viewport test:
   - iPad portrait (768x1024): fully readable, buttons touchable
   - iPhone landscape (812x375): no horizontal scroll
   - Text scales appropriately

**Testing Suite:**

```python
# tests/test_ui.py
class TestHome:
    def test_home_page_loads(self): ...
    def test_search_form_present(self): ...
    def test_button_size_minimum(self): ...
    def test_font_size_minimum(self): ...

class TestSearch:
    def test_search_by_surname(self): ...
    def test_search_by_service_number(self): ...
    def test_results_pagination(self): ...

class TestDetail:
    def test_officer_detail_loads(self): ...
    def test_soldier_detail_loads(self): ...
    def test_print_functionality(self): ...
```

Run tests:

```bash
pytest tests/test_ui.py -v
# Expected: 20+ tests pass, 95%+ accessibility score
```

**Acceptance Criteria:**

- [ ] WAVE audit: 0 errors + 0 contrast errors
- [ ] Lighthouse accessibility score: 95+
- [ ] Keyboard navigation works throughout
- [ ] Screen reader compatible (NVDA test passed)
- [ ] Mobile test: works on iPad + iPhone
- [ ] All tests pass (20+)

---

#### Task C.6: Documentation & Deployment

**Owner:** Engineer 2  
**Duration:** 1 day  
**Deliverables:** User guide + deployment instructions

**Documentation:**

1. Create user guide: `docs/USER_GUIDE.md`
   - How to search
   - How to read a record
   - How to print
   - FAQ (not finding ancestors, etc.)
   - Screenshot examples

2. Create admin guide: `docs/ADMIN_GUIDE.md`
   - How to run locally
   - How to deploy
   - Configuration options
   - Troubleshooting

3. Create deployment guide:
   - Docker setup (optional)
   - Production checklist
   - Performance monitoring
   - Backup procedures

## Deployment Option 1: Local (Development)

```bash
# Single machine setup
FLASK_ENV=development python src/web_app.py
# Open http://localhost:5000
```

## Deployment Option 2: Docker (Production-ready)

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ .
COPY data/sd_2011.db .
CMD ["gunicorn", "-b 0.0.0.0:5000", "web_app:app"]
```

**Acceptance Criteria:**

- [ ] User guide complete with screenshots
- [ ] Admin guide covers setup + troubleshooting
- [ ] Deployment tested (local + Docker)
- [ ] Documentation reviewed by data steward
- [ ] All stakeholders can understand deployment process

---

### C.3 Phase C Timeline

| Week | Mon | Tue | Wed | Thu | Fri |
| ------ | ----- | ----- | ----- | ----- | ----- |
| Week 4 | Task C.1 | Task C.2 | C.2 (cont) | Task C.3 | — |
| Week 5 | Task C.4 | C.4 (cont) | Task C.5 | C.5 (cont) | — |
| Week 6 | Task C.6 | Integration test | UAT prep | — | — |
| Week 7 | UAT (User Acceptance Testing) | — | — | — | — |
| Week 8 | Feedback integration | Final testing | Deployment prep | Launch | Monitoring |

**Milestone:** Phase C complete by Friday, Week 8

- All pages built and functional ✓
- Accessibility audit passed ✓
- User guide complete ✓
- Stakeholder UAT passed ✓
- Live deployment ✓

---

## 6. Risk Management

### Risk Register

| # | Risk | Impact | Likelihood | Mitigation | Owner |
| --- | ------ | -------- | ----------- | ----------- | ------- |
| R1 | SOLDIERS table export timeout | High | Medium | Chunked export; longer timeout | Eng 1 |
| R2 | Performance degradation with 703,806 records | High | Medium | Index optimization; query profiling | Eng 3 |
| R3 | Schema design misses requirements | High | Low | Early stakeholder review; iterate | Eng 3 + DS |
| R4 | CSV data corruption during migration | High | Low | Validation checks; rollback plan | Eng 3 |
| R5 | Accessibility issues discovered post-launch | Medium | Medium | Early WAVE audit; iterative testing | Eng 4 |
| R6 | Team bandwidth/delays | Medium | Medium | Parallel phase execution; cross-training | PM |
| R7 | Stakeholder expectations unmet | Medium | Low | Clear PRD communication; UAT | PO |

### Contingency Plans

**If Phase A Export Times Out:**

- Use chunked export (split SOLDIERS by battalion)
- Increase subprocess timeout to 300 seconds
- Consider PostgreSQL instead of SQLite

**If Phase B Migration Fails:**

- Restore from CSV backup (Phase A)
- Re-run migration with debugging enabled
- Investigate schema changes needed

**If Phase C Performance Issues:**

- Add missing indexes
- Profile slow queries with EXPLAIN PLAN
- Cache frequently accessed results
- Consider pagination improvements

---

## 7. Acceptance & Sign-Off

### Acceptance Criteria Summary

#### Phase A: Data Access (Complete)

- [x] All 7 tables accessible from MDB
- [x] Access Report documented
- [x] No corruption detected
- [x] Fallback approach identified

#### Phase B: Data Migration

- [ ] SQLite schema created + validated
- [ ] All 703,806 records loaded
- [ ] Migration validation passed (0 errors)
- [ ] Data dictionary complete
- [ ] Documentation signed off

#### Phase C: Basic UI

- [ ] All pages functional (home, search, detail)
- [ ] Accessibility audit passed (0 errors)
- [ ] User guide complete
- [ ] Stakeholder UAT passed
- [ ] Live deployment successful

### Sign-Off Process

1. **Phase A Sign-Off:** Engineer 1, Data Steward
   - Date: End of Week 2
   - Approval: _______________

2. **Phase B Sign-Off:** Engineer 3, Tech Lead
   - Date: End of Week 4
   - Approval: _______________

3. **Phase C Sign-Off:** Engineer 4, Product Owner
   - Date: End of Week 8
   - Approval: _______________

---

## 8. Success Metrics (Final)

### Quantitative Metrics

- **Data Extraction:** 100% of 703,806 records exported
- **Data Migration:** 100% of records loaded; 0 data loss
- **Performance:** All queries < 1 second
- **Accessibility:** WCAG AAA compliance (7:1 contrast minimum)
- **Uptime:** 99.9% availability post-launch
- **Tests:** 95%+ code coverage; all tests passing

### Qualitative Metrics

- **Usability:** First-time user finds ancestor in < 2 minutes
- **Accuracy:** Stakeholder confidence in data (post-verification)
- **Maintainability:** Team can support system independently
- **Documentation:** Clear, complete, easy to follow

---

## 9. Post-Launch Monitoring & Support

### Week 1 Post-Launch

- Monitor for errors/crashes
- Track user feedback
- Performance monitoring (query times, uptime)
- Bug fix turnaround: < 24 hours

### Phase 2 (Future)

- [ ] Fuzzy name matching
- [ ] Advanced query builder
- [ ] Export to CSV
- [ ] Map view of locations
- [ ] Timeline visualization
- [ ] API for research community

---

## 10. Appendices

### A. Team Roles

- **Engineer 1:** Data Access (Phase A)
- **Engineer 2:** Documentation & Support (Phases A, B, C)
- **Engineer 3:** Data Migration (Phase B)
- **Engineer 4:** UI Development (Phase C)
- **Data Steward:** Data governance, validation, sign-off
- **Product Owner:** Stakeholder liaison, requirements clarification
- **Tech Lead:** Architecture, code review, deployment

### B. Technology Stack Summary

| Component | Technology | Version |
| ----------- | ----------- | --------- |
| Data source | Microsoft Access | .mdb format |
| Data extraction | mdbtools | 1.0.1 |
| Database | SQLite | 3.40+ |
| Backend | Python Flask | 3.0+ |
| Frontend | HTML5 + CSS3 | Dynamic templates |
| Testing | pytest | 7.0+ |

### C. Budget Estimate (Team Time)

- Phase A: 10 engineer-days
- Phase B: 14 engineer-days
- Phase C: 16 engineer-days
- **Total:** 40 engineer-days (~8 weeks for 1 team of 4-5)

---

**Document Version:** 1.0  
**Last Updated:** 16 February 2026  
**Next Review:** Weekly team sync + milestone sign-offs
