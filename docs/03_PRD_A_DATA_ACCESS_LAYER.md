# PRD A: Data Access Layer

## Product Requirements Document – SDGW 1914-1919 Modernization

**Version:** 1.0  
**Date:** 16 February 2026  
**Status:** Ready for Implementation  
**Audience:** Engineering Team & Stakeholders

---

## 1. Document Purpose

This PRD defines how the application will reliably read historical military personnel data (1914-1919) from the legacy Microsoft Access database and present it to other system components. This is the foundational "data gateway" upon which all downstream features (UI, search, reporting) depend.

---

## 2. Business Context

### Problem

- Legacy data locked in proprietary `.mdb` format
- System must read ~703,806 historical records reliably
- End users (researchers, historians, families) need modern, searchable interface
- No current way to access/search data efficiently

### Goals

- **Enable Data Mobility:** Extract data from legacy format safely
- **Ensure Reliability:** Consistent, reproducible data access
- **Support Migration:** Bridge to modern database (SQLite/PostgreSQL)
- **Enable Auditing:** Log all data access for governance compliance

### Constraints

- **macOS-based workflow** – No Microsoft Access
- **High data volume** – 703,806 records
- **Historical accuracy** – No data loss or corruption
- **Low cost** – Use open-source tools where possible

---

## 3. Scope: What We're Building

### In Scope ✅

- Thin abstraction layer to query the MDB file
- CSV export functionality for all tables
- Error handling and retry logic
- Logging of all data access operations
- Validation that exported data matches source
- Backup strategy for source database

### Out of Scope 🚫

- Real-time database synchronization
- Schema modification of source database
- GUI for data exploration (see UI PRD C)
- Advanced SQL querying (that's migration phase)

---

## 4. Requirements

### 4.1 Functional Requirements

#### FR-1: Read All Tables

**Requirement:** System must successfully read and export all 7 tables from `sd_2011.mdb`

**Tables:**

- SD_RANKS (547 rows)
- SD_Battalions (721 rows)
- REGBATS (1,987 rows)
- OD_REGBATS (1,662 rows)
- OD_Battalions (480 rows)
- OFFICERS (41,846 rows)
- SOLDIERS (661,960 rows)

**Acceptance Criteria:**

- [ ] Each table successfully exported to CSV format
- [ ] Row counts match source database counts (±0 rows)
- [ ] All columns present in output
- [ ] No data truncation or loss
- [ ] UTF-8 encoding preserved

---

#### FR-2: Handle Large Datasets

**Requirement:** System must handle SOLDIERS table (661,960 rows) without failure

**Acceptance Criteria:**

- [ ] SOLDIERS export completes within 5 minutes
- [ ] Memory usage remains under 2 GB during export
- [ ] No process crashes or timeouts
- [ ] Option to export in chunks if needed

---

#### FR-3: Export to CSV Format

**Requirement:** Data must be exported in standard CSV format

**Format Specification:**

- Headers in first row
- Comma-separated fields
- Quote fields containing commas
- UTF-8 encoding
- Unix line endings (LF)

**Example:**

```text
O_ID,REGSORT,REG_ID,BAT_ID,SURNAME,CHRST_NAME,INITIALS,DECORATION,RANK,RANK_ID
1,79,1,392,"ADAMSON","W C","W C",,"CAPT (TP)",2
```

**Acceptance Criteria:**

- [ ] CSV parseable by Python `csv` module
- [ ] CSV importable to Excel/Numbers
- [ ] CSV loadable into SQLite/PostgreSQL

---

#### FR-4: Validate Exported Data

**Requirement:** System must verify that exported data matches source

**Validation Strategy:**

- Row count verification
- Column count verification
- Checksum verification (CRC32 of data)
- Spot-check: verify 5 random records from each table are identical in both source and export

**Acceptance Criteria:**

- [ ] Validation script completes without errors
- [ ] Reports pass/fail status for each table
- [ ] Identifies any discrepancies with detailed error messages

---

#### FR-5: Error Recovery

**Requirement:** System must handle extraction errors gracefully

**Scenarios:**

- Database file missing or inaccessible
- mdbtools binary not installed
- Insufficient disk space for CSV exports
- Table has unexpected schema changes
- Timeout during large table export

**Acceptance Criteria:**

- [ ] Each error produces clear, actionable message
- [ ] Automatic retry for transient errors (up to 3 attempts)
- [ ] Detailed error logging for debugging
- [ ] No silent failures

---

#### FR-6: Logging & Audit Trail

**Requirement:** All data access operations must be logged

**Log Format:**

```text
[TIMESTAMP] [LEVEL] [COMPONENT] [TABLE] [MESSAGE]
[2026-02-16 15:30:22] INFO  [DataAccess] [SD_RANKS]    Exported 547 rows to sd_ranks.csv
[2026-02-16 15:30:25] INFO  [DataAccess] [SD_RANKS]    Checksum verification: PASS
[2026-02-16 15:31:00] WARN  [DataAccess] [SOLDIERS]    Export timeout (45000 rows) - retrying with chunk size
[2026-02-16 15:31:45] INFO  [DataAccess] [SOLDIERS]    Exported 45213 rows to soldiers.csv
```

**Acceptance Criteria:**

- [ ] All operations logged with timestamp
- [ ] Log includes: component, table name, operation, result, duration, error details
- [ ] Logs rotated daily; 30-day retention
- [ ] Logs easily parseable for analysis

---

#### FR-7: Backup Before Export

**Requirement:** Create automated backup of source database before extraction

**Acceptance Criteria:**

- [ ] Backup created with timestamp: `sd_2011.mdb.backup.20260216_153022`
- [ ] Backup compared with original (checksum match)
- [ ] Backup stored in `data/backups/` directory
- [ ] Backup retention: keep last 5 backups

---

### 4.2 Non-Functional Requirements

#### NFR-1: Performance

- **Export Speed:** OFFICERS (41,846 rows) in < 30 seconds; SOLDIERS (661,960 rows) in < 5 minutes
- **Memory:** Peak memory usage < 2 GB
- **CPU:** Single-threaded for reliability; no unnecessary parallelization

#### NFR-2: Reliability

- **Availability:** Data access service available 99.9% of the time (planned maintenance: monthly, 1 hour)
- **Mean Time to Recovery (MTTR):** < 15 minutes for database access failures
- **Data Durability:** Zero data loss; all exports backed up to Git

#### NFR-3: Maintainability

- **Code Quality:** All code peer-reviewed before merge to main branch
- **Documentation:** README with step-by-step setup instructions (< 5 minutes to setup on new machine)
- **Testing:** 80%+ code coverage with unit tests

#### NFR-4: Portability

- **Platform:** Must work on macOS (ARM64), Linux (Ubuntu 20.04+), Windows (WSL2)
- **Dependencies:** Single dependency: `mdbtools` (installable via Homebrew/apt/chocolatey)
- **Python Version:** 3.9+

#### NFR-5: Security

- **Access Control:** Source database file is local; no authentication required
- **Data Protection:** All CSV exports stored in Git with `.gitignore` for sensitive backups
- **Audit Logging:** All access operations logged with timestamp and user info
- **No Secrets:** No credentials, API keys, or passwords in codebase

#### NFR-6: Scalability

- **Growth Path:** Support 10x data growth if needed (e.g., adding more regiments/units)
- **Concurrent Access:** Single-process access to MDB file (sequential consistency)

---

## 5. Technical Approach

### Technology Stack

| Component | Technology | Justification |
| ----------- | ----------- | --------------- |
| Data Source | mdbtools v1.0.1 | Open-source, field-tested, cross-platform |
| Primary Language | Python 3.11+ | Rich ecosystem for data handling; easy deployment |
| CSV Processing | Python `csv` module | Built-in; standard; fast |
| Logging | Python `logging` module | Built-in; standard; configurable |
| Testing | `pytest` | Industry standard; simple syntax |
| Version Control | Git | Existing workflow; enables data recovery |

### Architecture

```text
┌─────────────────────┐
│  Application Layer  │  (PRD C: UI, Search, Reporting)
│  (needs data)       │
└──────────┬──────────┘
           │ imports
           ▼
┌─────────────────────────────────────┐
│  Data Access Layer (This PRD)        │
│  ┌─────────────────────────────────┐ │
│  │ DataExtractor (Python module)   │ │
│  │ - extract(table_name)           │ │
│  │ - export_all()                  │ │
│  │ - validate()                    │ │
│  └─────────────────────────────────┘ │
└──────────┬──────────────────────────┘
           │ subprocess calls
           ▼
┌─────────────────────┐
│  mdbtools (binary)  │
│  - mdb-export       │
│  - mdb-schema       │
│  - mdb-tables       │
└──────────┬──────────┘
           │ reads
           ▼
┌─────────────────────┐
│  sd_2011.mdb        │
│  (source database)  │
└─────────────────────┘
```

### Module: `DataExtractor`

**File:** `src/data_access.py`

**Public API:**

```python
class DataExtractor:
    def __init__(self, mdb_path: str, log_handler=None):
        """Initialize extractor for given MDB file"""
        pass
    
    def get_tables(self) -> List[str]:
        """Return list of all tables in database"""
        pass
    
    def extract_table(self, table_name: str, output_csv: str) -> ExportResult:
        """Export single table to CSV; return result with metadata"""
        pass
    
    def export_all(self, output_dir: str) -> Dict[str, ExportResult]:
        """Export all tables; return results dictionary"""
        pass
    
    def validate_export(self, export_dir: str) -> ValidationReport:
        """Compare exported CSVs with source database"""
        pass
    
    def create_backup(self, backup_dir: str) -> BackupResult:
        """Create timestamped backup of source MDB"""
        pass
```

**Example Usage:**

```python
from src.data_access import DataExtractor

# Initialize
extractor = DataExtractor("data/sd_2011.mdb")

# Export all tables
results = extractor.export_all("data/exports/")
print(f"Exported {len(results)} tables")

# Validate
validation = extractor.validate_export("data/exports/")
if validation.all_pass:
    print("✓ All tables validated successfully")
else:
    print(f"✗ Validation failed: {validation.errors}")
```

---

## 6. Workflow & User Scenarios

### Scenario 1: Developer Sets Up Data Access Locally

**Actor:** Engineer on macOS  
**Steps:**

1. Clone repository
2. Run `brew install mdbtools`
3. Run `python src/scripts/export_data.py`
4. Verify CSVs in `data/exports/`
5. Commit CSVs to Git

**Expected Outcome:** All tables exported and validated in < 10 minutes

---

### Scenario 2: Data Is Modified; Need Re-Export

**Actor:** Data steward  
**Steps:**

1. Verify changes to source MDB
2. Create backup: `python src/scripts/backup.py`
3. Export: `python src/scripts/export_data.py`
4. Validate: `python src/scripts/validate_export.py`
5. Commit new CSVs and log entry

**Expected Outcome:** New data available for migration/UI

---

### Scenario 3: Validate Data Before Migration

**Actor:** QA engineer  
**Steps:**

1. Run validation script: `python src/scripts/validate_export.py`
2. Receive report on row counts, checksums, sample validations
3. Verify all checks pass
4. Approve data for migration phase

**Expected Outcome:** Confidence that source and export match

---

## 7. Success Criteria

### MVP (Minimum Viable Product)

- [ ] `DataExtractor` class fully functional
- [ ] All 7 tables export successfully to CSV
- [ ] Validation script confirms data integrity
- [ ] Logging captures all operations
- [ ] README documents setup and usage
- [ ] 5 example CSVs committed to repo (1 per table type)

### Alpha Release

- [ ] Unit tests: 80%+ coverage
- [ ] Error handling for all identified failure scenarios
- [ ] Performance validated: large tables export in < 5 minutes
- [ ] Tested on macOS, Linux, and Windows (WSL2)

### Production Release

- [ ] Code review complete (2+ reviewers)
- [ ] Integration tests with subsequent migration phase
- [ ] Documentation in user manual
- [ ] Monitoring/alerting configured
- [ ] Disaster recovery tested (restore from backup)

---

## 8. Acceptance Tests

### Test 1: Export All Tables

```bash
python src/scripts/export_data.py
# Expected: All 7 CSVs created in data/exports/
# All files contain > 0 rows + headers
```

### Test 2: Validate Checksums

```bash
python src/scripts/validate_export.py data/exports/
# Expected: PASS for all tables
# Row counts within ±0 of source
```

### Test 3: Large Table Performance

```bash
time python -c "from src.data_access import DataExtractor; \
    d = DataExtractor('data/sd_2011.mdb'); \
    d.extract_table('SOLDIERS', 'test_soldiers.csv')"
# Expected: < 300 seconds wall-clock time
# Memory: < 2 GB peak
```

### Test 4: Error Handling

```bash
python src/scripts/export_data.py --db-path /nonexistent/file.mdb
# Expected: Clear error message, exit code 1, detailed log entry
```

---

## 9. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
| ------ | -------- | ----------- | ----------- |
| mdbtools fails on large SOLDIERS table | High | Medium | Implement chunked export; increase timeout; test early |
| CSV encoding issues (special characters) | Medium | Low | Force UTF-8; validate character ranges |
| Insufficient disk space for exports | Medium | Low | Check disk space before export; warn if < 1 GB free |
| Source MDB file corruption | High | Low | Create backup before export; add integrity checks |
| Performance regression over time | Medium | Medium | Automated performance tests; benchmark baseline |

---

## 10. Rollout Plan

### Phase 1: Internal Testing (Week 1)

- [ ] Implement `DataExtractor` module
- [ ] Unit tests for all functions
- [ ] Run on development machine (macOS)
- [ ] Validate against actual database

### Phase 2: Cross-Platform Testing (Week 2)

- [ ] Test on Ubuntu Linux
- [ ] Test on Windows WSL2
- [ ] Document platform-specific issues
- [ ] Fix any compatibility gaps

### Phase 3: Stakeholder Review (Week 2-3)

- [ ] Review with data team
- [ ] Verify export data looks correct
- [ ] Get sign-off on validation approach
- [ ] Finalize documentation

### Phase 4: Production Deployment (Week 3)

- [ ] Merge to main branch
- [ ] Tag release v1.0
- [ ] Deploy extraction scripts to shared location
- [ ] Begin migration phase (PRD B)

---

## 11. Open Questions & Dependencies

1. **Q:** Should export process be manual or automated (scheduled daily)?  
   **A:** MVP = manual; automation can be added in Phase 2

2. **Q:** Who has access to run export process?  
   **A:** Any engineer on team; no special permissions needed

3. **Q:** How often will source database be updated?  
   **A:** Unknown; assume infrequent (monthly or less)

4. **Q:** Should we store CSVs in Git or external storage?  
   **A:** Git for version history; can be revisited post-launch

---

## 12. Appendices

### A. Glossary

- **MDB:** Microsoft Access database file format
- **CSV:** Comma-Separated Values (standard data export format)
- **mdbtools:** Open-source library for reading MDB files
- **MTTR:** Mean Time to Recovery (average time to fix failures)

### B. References

- [mdbtools Documentation](http://mdbtools.sourceforge.net)
- [Python CSV Module](https://docs.python.org/3/library/csv.html)
- [Python Logging](https://docs.python.org/3/library/logging.html)

### C. Sign-Off

| Role | Name | Date | Signature |
| ------ | ------ | ------ | ----------- |
| Product Owner | TBD | 16 Feb 2026 | TBD |
| Tech Lead | TBD | 16 Feb 2026 | TBD |
| QA Lead | TBD | 16 Feb 2026 | TBD |

---

**Document Version:** 1.0  
**Last Updated:** 16 February 2026  
**Next Review:** Week 2 of implementation
