# PRD B: Data Migration

## Product Requirements Document – SDGW 1914-1919 Modernization

**Version:** 1.0  
**Date:** 16 February 2026  
**Status:** Ready for Implementation  
**Audience:** Engineering Team & Stakeholders

---

## 1. Document Purpose

This PRD defines how we will migrate historical military personnel data from CSV exports (from legacy `.mdb` file) into a modern, queryable database system. This enables efficient search, filtering, and reporting without dependency on Microsoft Access tools.

---

## 2. Business Context

### Problem

- Current data exists only in CSV format (exported from legacy MDB)
- CSVs inefficient for: searching, filtering, reporting, data validation
- Need structured database for fast queries
- Must support 703,806 personnel records with historical accuracy

### Goals

- **Data Permanence:** Establish single source of truth in modern database
- **Query Capability:** Enable fast, complex queries for research/reporting
- **Data Integrity:** Validate all data during migration; detect issues
- **Scalability:** Design schema to support future enhancements (photos, documents, relationships)
- **Low Cost:** Use free/open-source database
- **Reliability:** Zero data loss; schema designed for data consistency

### Constraints

- **No data loss:** Every record must migrate cleanly
- **Backward compatibility:** New schema must map to all legacy columns
- **Performance:** Queries must return results in < 1 second for UI responsiveness
- **Accessibility:** Data must be queryable by non-technical stakeholders

---

## 3. Scope: What We're Building

### In Scope ✅

- Design normalized schema for 703,806 personnel records
- Create migration scripts (CSV → Database)
- Implement comprehensive data validation
- Handle schema mapping and type conversions
- Create database indexing strategy
- Implement referential integrity checks
- Build migration rollback capability

### Out of Scope 🚫

- User interface (see PRD C)
- Search/query optimization (Phase 2)
- Historical change tracking (audit tables) (Phase 3)
- Photo/document attachments (future enhancement)

---

## 4. Target Database Selection

### Comparison: SQLite vs PostgreSQL

| Dimension | SQLite | PostgreSQL | Winner |
| ----------- | -------- | ----------- | -------- |
| **Installation** | Built-in (no setup) | Requires server | SQLite |
| **Performance** | Fast for <100 GB | Fast for very large | PostgreSQL (tie) |
| **Concurrent Users** | Single-process | Multi-process | PostgreSQL |
| **Cost** | Free | Free | Tie |
| **Portability** | Single file | Requires database server | SQLite |
| **Complexity** | Minimal | Moderate | SQLite |

- **Scalability (700K+ records)** | Excellent | Excellent | Tie |

### Recommended Strategy: Two-Tier Approach

**Development & Prototype** → **SQLite**

- Advantages: Single file, zero setup, perfect for ~100K records
- File: `data/sd_2011.db` (tracked in Git)
- Ideal for: local development, testing, UI prototyping

**Future Production** → **PostgreSQL**

- When ready to host as web service
- Enables multi-user concurrent access
- Can be migrated from SQLite at step 2 with minimal effort (schema is identical)

**Current Milestone:** Build for SQLite; architecture agnostic

---

## 5. Data Model & Schema Design

### 5.1 Entity-Relationship Overview

```text
Personnel Records:
├── OFFICERS (41,846 records)
├── SOLDIERS (661,960 records)
└── Shared attributes: Name, Rank, Assignment, Death Info

Reference Data:
├── Ranks (547 unique)
├── Battalions (721 unique, SD)
├── Battalions_OD (480 unique, Other District)
├── Regiments (derived from associations)
└── Regimental Associations (REGBATS, OD_REGBATS)
```

### 5.2 Normalized Schema

#### Table 1: `ranks`

Reference data for military ranks

```sql
CREATE TABLE ranks (
    rank_id INTEGER PRIMARY KEY,
    rank_original TEXT NOT NULL UNIQUE,     -- e.g., "ARMR./PTE."
    rank_normalized TEXT NOT NULL UNIQUE,   -- e.g., "Armourer, Private"
    rank_group TEXT NOT NULL,               -- e.g., "Privates", "Officers"
    rank_code TEXT,                         -- Short code if applicable
    sort_order INTEGER                      -- Display order
);
```

**Data Source:** SD_RANKS table  
**Row Count:** 547  
**Validation:** No duplicates; all rank_group values documented

**Sample Data:**

```text
rank_id | rank_original    | rank_normalized | rank_group       | sort_order
--------|------------------|-----------------|------------------|----------
1       | ARMR./PTE.       | Armourer, Private | Privates        | 1
2       | CAPT (TP)        | Captain (TP)    | Officers         | 15
```

---

#### Table 2: `battalions_sd`

Scottish Division battalion reference data

```sql
CREATE TABLE battalions_sd (
    battalion_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,              -- Full battalion name
    sort_order INTEGER DEFAULT 0
);
```

**Data Source:** SD_Battalions table  
**Row Count:** 721  

**Sample Data:**

```text
battalion_id | name                              | sort_order
-------------|-----------------------------------|----------
295          | 78th Training Reserve Battalion  | 0
```

---

#### Table 3: `battalions_od`

Other District battalion reference data

```sql
CREATE TABLE battalions_od (
    battalion_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,              -- Full battalion name
    sort_order INTEGER DEFAULT 0
);
```

**Data Source:** OD_Battalions table  
**Row Count:** 480  
**Note:** Separate from `battalions_sd` to maintain original organizational structure

---

#### Table 4: `regiment_battalion_associations` (REGBATS)

Maps regiments to battalions (one-to-many)

```sql
CREATE TABLE regiment_battalion_associations (
    association_id INTEGER PRIMARY KEY AUTOINCREMENT,
    regiment_id INTEGER NOT NULL,
    battalion_id INTEGER NOT NULL,
    sort_order INTEGER,
    association_type TEXT DEFAULT 'sd',      -- 'sd' or 'od'
    UNIQUE(regiment_id, battalion_id, association_type)
);

CREATE INDEX idx_regbat_regiment ON regiment_battalion_associations(regiment_id);
CREATE INDEX idx_regbat_battalion ON regiment_battalion_associations(battalion_id);
```

**Data Source:** REGBATS + OD_REGBATS tables  
**Row Count:** 1,987 + 1,662 = 3,649  

---

#### Table 5: `officers`

Commissioned officer records

```sql
CREATE TABLE officers (
    officer_id INTEGER PRIMARY KEY,
    surname TEXT NOT NULL,
    christian_names TEXT,                   -- "W C" or full names
    initials TEXT,
    regiment_id INTEGER,                    -- Foreign key to conceptual regiment table
    battalion_id INTEGER NOT NULL,          -- FK to battalion
    rank_id INTEGER,                        -- FK to ranks table
    rank_text TEXT,                         -- Denormalized for speed
    decoration TEXT,                        -- E.g., "DSO", "MC", etc.
    death_date DATE,                        -- ISO 8601 format
    death_location TEXT,
    additional_notes TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (battalion_id) REFERENCES battalions_sd(battalion_id),
    FOREIGN KEY (rank_id) REFERENCES ranks(rank_id)
);

-- Indexes for common queries
CREATE INDEX idx_officers_surname ON officers(surname);
CREATE INDEX idx_officers_battalion ON officers(battalion_id);
CREATE INDEX idx_officers_rank ON officers(rank_id);
CREATE INDEX idx_officers_death_date ON officers(death_date);
```

**Data Source:** OFFICERS table  
**Row Count:** 41,846  
**Key Mappings:**

- `O_ID` → `officer_id`
- `SURNAME` → `surname`
- `CHRST_NAME` → `christian_names`
- `BAT_ID` → `battalion_id`
- `RANK_ID` → `rank_id`
- `DEATH_DATE` (text) + `D_TRUEDATE` (datetime) → `death_date` (standardized)

**Data Consolidation Notes:**

- Combine DEATH_DATE + D_TRUEDATE into single DEATH_DATE (datetime)
- Use D_TRUEDATE as primary source if valid, else parse DEATH_DATE
- Handle null/empty dates as NULL

---

#### Table 6: `soldiers`

Enlisted soldier records

```sql
CREATE TABLE soldiers (
    soldier_id INTEGER PRIMARY KEY,
    service_number TEXT,                    -- Service number (may not be unique across regiments)
    surname TEXT NOT NULL,
    christian_names TEXT,
    initials TEXT,
    
    -- Military assignment
    regiment_id INTEGER,                    -- Conceptual regiment
    battalion_id INTEGER NOT NULL,          -- FK to battalion
    rank_id INTEGER,                        -- FK to ranks table
    rank_text TEXT,                         -- Denormalized for speed
    
    -- Birth & enlistment info
    birth_town TEXT,
    enlistment_location TEXT,               -- Location of enlistment
    enlistment_place TEXT,                  -- More specific place (if different from location)
    
    -- Casualty information
    death_date DATE,                        -- ISO 8601
    death_location TEXT,
    
    -- Additional info
    additional_notes TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (battalion_id) REFERENCES battalions_sd(battalion_id),
    FOREIGN KEY (rank_id) REFERENCES ranks(rank_id)
);

-- Indexes for common queries
CREATE INDEX idx_soldiers_surname ON soldiers(surname);
CREATE INDEX idx_soldiers_service_number ON soldiers(service_number);
CREATE INDEX idx_soldiers_battalion ON soldiers(battalion_id);
CREATE INDEX idx_soldiers_birth_town ON soldiers(birth_town);
CREATE INDEX idx_soldiers_death_date ON soldiers(death_date);
-- Full-text search via FTS5 virtual table (created separately)
-- CREATE VIRTUAL TABLE soldiers_fts USING fts5(surname, christian_names, birth_town, content='soldiers', content_rowid='soldier_id');
```

**Data Source:** SOLDIERS table  
**Row Count:** 661,960  
**Key Mappings:**

- `S_ID` → `soldier_id`
- `SURNAME` → `surname`
- `CHRST_NAME` → `christian_names`
- `NUMBER` → `service_number`
- `RANK_ID` → `rank_id`
- `DEATH_DATE` (text) + `D_TRUEDATE` (datetime) → `death_date`

**Data Consolidation Notes:**

- Combine ENLST_LOC + ENLST_PLC into enlistment_location (prefer ENLST_PLC if different)
- Remove TOW_ID_OLD; use TOW_ID only
- Consolidate rank fields: use RANK_ID, store RANK as text

---

### 5.3 Schema Design Principles

1. **Normalization:** Ranks and references are separate tables (no duplication)
2. **Denormalization:** Store `rank_text` in officers/soldiers for UI performance
3. **Type Consistency:** All IDs are INTEGER PRIMARY KEY; all foreign keys are INTEGER to match
4. **Dates:** Always stored as ISO 8601 DATE; no text dates
5. **Null Policy:** NULL allowed for optional fields; NOT NULL for required
6. **Indexing:** Indexes on foreign keys + frequently searched columns
7. **Audit Trail:** `created_at`, `updated_at` timestamps on all person records

---

## 6. Data Validation & Mapping Rules

### 6.1 Type Conversions

| Source (CSV) | Source Type | Target (Database) | Conversion Rule |
| --- | --- | --- | --- |
| `ID` (RANK) | Text/Number | rank_id (INT) | Parse as integer |
| `Name` (Battalion) | Text | name (TEXT) | Trim whitespace; preserve case |
| `SURNAME` | Text | surname (VARCHAR(100)) | Uppercase preserved; trim |
| `CHRST_NAME` | Text | christian_names (VARCHAR(100)) | Preserve original case |
| `DEATH_DATE` | Text (MM/DD/YY) | death_date (DATE ISO8601) | Parse "05/09/15" → 1915-09-05 |
| `D_TRUEDATE` | DateTime | death_date (DATE) | Parse ISO 8601 datetime; extract date portion |
| `REG_ID` / `BAT_ID` | Double/Float | regiment_id, battalion_id (INT) | Parse as integer |
| `RANK_ID` | Double | rank_id (INT) | Parse as integer |
| `BORN_TOWN` | Text | birth_town (VARCHAR(150)) | Trim; preserve original spelling |

### 6.2 Data Validation Rules

#### Validation Rule V1: No Duplicate Service Numbers (Soldiers)

```text
Rule: service_number must be UNIQUE within soldiers table
Action on violation: Log error; mark record as duplicate; skip or merge
Expected impact: < 0.1% of records
```

#### Validation Rule V2: Date Format Consistency

```text
Rule: All death_date values must parse to valid ISO 8601 DATE
Action on violation: Log parsing error; store as NULL; flag for review
Expected impact: < 1% of records
```

#### Validation Rule V3: Referential Integrity

```text
Rule: All battalion_id in officers/soldiers must exist in battalions_sd or battalions_od
Action on violation: Log error; assign to default battalion; flag for review
Expected impact: < 0.1% of records
```

#### Validation Rule V4: Rank Consistency

```text
Rule: All rank_id must exist in ranks lookup table
Action on violation: Log error; assign generic rank; flag for review
Expected impact: 0% (if migration script is correct)
```

#### Validation Rule V5: Non-Empty Critical Fields

```text
Rule: surname NOT NULL and LENGTH > 0 for all person records
Action on violation: Log error; skip record; flag for review
Expected impact: 0% (historical data should be complete)
```

### 6.3 Data Validation Checks

#### Check 1: Row Count Verification

```text
Expected Row Counts:
- ranks table: 547 rows (from SD_RANKS)
- battalions_sd table: 721 rows (from SD_Battalions)
- battalions_od table: 480 rows (from OD_Battalions)
- officers table: 41,846 rows (from OFFICERS CSV)
- soldiers table: 661,960 rows (from SOLDIERS CSV)
Total: ~703,806 person records

Acceptance Criteria:
- ✓ officers count within ±0 of source
- ✓ soldiers count within ±0 of source
- ✓ No duplicates in person tables
```

#### Check 2: Checksum Verification

```text
Method: CRC32 checksum on CSV vs database export
Compare: SELECT * FROM officers ORDER BY officer_id
Export to CSV and compute CRC32 of both files
Expected: CRC32 values match within ±5 rows (to account for NULL formatting differences)

Acceptance Criteria:
- ✓ CRC32 matches for all tables
- ✓ If differences, use spot check (see Check 3)
```

#### Check 3: Spot Check (Random Sampling)

```text
Method: Manually verify 5 random records from each table
For each record:
- Verify all fields match CSV source
- Verify no truncation or corruption
- Verify dates parsed correctly
- Verify foreign key references resolve
- Check for encoding issues (special characters)

Tool: SQL query to join with saved CSV
Expected: 100% match rate
```

#### Check 4: Referential Integrity Check

```text
SQL Queries:
-- Find orphaned battalion assignments
SELECT COUNT(*) FROM officers WHERE battalion_id NOT IN 
    (SELECT battalion_id FROM battalions_sd)
-- Expected: 0 rows

-- Find orphaned rank assignments
SELECT COUNT(*) FROM officers WHERE rank_id NOT NULL AND rank_id NOT IN 
    (SELECT rank_id FROM ranks)
-- Expected: 0 rows
```

---

## 7. Migration Strategy

### 7.1 Migration Phases

#### Phase 1: Preparation (Week 1)

1. Export all tables to CSV from source MDB (see PRD A)
2. Validate CSV integrity and checksums
3. Create SQLite database file and schema
4. Set up logging and error handling
5. Create rollback scripts

#### Phase 2: Schema Creation (Week 1)

1. Create ranks reference table
2. Create battalion reference tables
3. Create regiment_battalion_associations table
4. Create officers table
5. Create soldiers table
6. Create indexes
7. Verify schema with test queries

#### Phase 3: Data Loading (Week 2)

1. Load ranks from SD_RANKS CSV
2. Load battalions from SD_Battalions + OD_Battalions CSVs
3. Load associations from REGBATS + OD_REGBATS CSVs
4. Load officers from OFFICERS CSV
5. Load soldiers from SOLDIERS CSV (chunked if necessary)
6. Log all operations and row counts

#### Phase 4: Validation (Week 2)

1. Run validation checks (row counts, checksums, spot checks)
2. Verify referential integrity
3. Verify lookup table completeness
4. Performance test: run sample queries
5. Get stakeholder sign-off

#### Phase 5: Rollback Testing (Week 2-3)

1. Create database snapshot
2. Practice rollback to CSV sources
3. Document rollback procedure
4. Train team on recovery process

#### Phase 6: Production Deployment (Week 3)

1. Tag schema version: `v1.0-initial`
2. Commit database to Git (or archival location)
3. Run final validation
4. Begin Phase A: UI development (PRD C)

---

### 7.2 Migration Scripts

#### Script 1: `migrate_ranks.py`

Load rank reference data

```python
def migrate_ranks(csv_file: str, db_path: str) -> MigrationResult:
    """
    Load ranks from SD_RANKS.csv into ranks table
    
    Inputs:
    - csv_file: Path to SD_RANKS.csv
    - db_path: Path to target SQLite database
    
    Returns:
    - MigrationResult(rows_loaded, errors, warnings)
    """
```

#### Script 2: `migrate_personnel.py`

Load officer and soldier records

```python
def migrate_officers(csv_file: str, db_path: str) -> MigrationResult:
    """Load officers from OFFICERS.csv into officers table"""

def migrate_soldiers(csv_file: str, db_path: str, chunk_size: int = 5000) -> MigrationResult:
    """Load soldiers from SOLDIERS.csv into soldiers table (chunked)"""
```

#### Script 3: `validate_migration.py`

Comprehensive validation suite

```python
def validate_row_counts(db_path: str, source_counts: Dict[str, int]) -> ValidationReport:
    """Verify row counts match source CSVs"""

def validate_checksums(db_path: str, csv_dir: str) -> ValidationReport:
    """CRC32 checksum verification"""

def validate_referential_integrity(db_path: str) -> ValidationReport:
    """Check foreign key references"""

def validate_spot_checks(db_path: str, sample_size: int = 5) -> ValidationReport:
    """Random sample validation of individual records"""
```

#### Script 4: `rollback_migration.py`

Restore from backup

```python
def rollback_to_csv(db_path: str, csv_dir: str) -> RollbackResult:
    """Restore from CSV exports; rebuild if needed"""
```

---

## 8. Rollback Strategy

### Rollback Trigger Points

| Scenario | Trigger | Action |
| ---------- | --------- | -------- |
| **Validation fails** | Validation report shows > 5 failures | Halt migration; investigate; fix scripts; retry |
| **Performance issue** | Query response > 1 second | Optimize indexes; profile queries; retry |
| **Data loss detected** | Row count mismatch > 1% | Restore from CSV; re-check source data |
| **Stakeholder rejection** | Stakeholder fails to sign off | Document feedback; address in Phase 2; re-validate |

### Rollback Procedure

```bash
# Step 1: Stop all processes accessing database
# Step 2: Backup current database (timestamp it)
cp sd_2011.db sd_2011.db.rollback.20260220_143000

# Step 3: Delete database file
rm sd_2011.db

# Step 4: Re-export CSVs from source MDB (if needed)
python src/scripts/export_data.py

# Step 5: Recreate database from scratch
python src/scripts/migrate_personnel.py

# Step 6: Validate again
python src/scripts/validate_migration.py

# Step 7: If successful, document issue and restart
# If failed, investigate and repeat process
```

---

## 9. Performance & Indexing Strategy

### Query Performance Targets

| Query Type | Expected Time | Notes |
| --- | --- | --- |
| Single record lookup by surname | < 100 ms | Index on surname |
| Range query (death dates) | < 500 ms | Index on death_date |
| Unit/battalion query (e.g., all soldiers in battalion X) | < 200 ms | Index on battalion_id |
| Full-text search (name contains), 50K+ records | < 2 second | Full-text index or prefix search |
| Complex join (officers by regiment → battalion → rank) | < 1 second | Composite indexes |

### Index Strategy

```sql
-- Primary Indexes (Foreign Keys & Lookup)
CREATE INDEX idx_officers_battalion ON officers(battalion_id);
CREATE INDEX idx_soldiers_battalion ON soldiers(battalion_id);
CREATE INDEX idx_officers_rank ON officers(rank_id);
CREATE INDEX idx_soldiers_rank ON soldiers(rank_id);

-- Secondary Indexes (Search)
CREATE INDEX idx_officers_surname ON officers(surname);
CREATE INDEX idx_soldiers_surname ON soldiers(surname);
CREATE INDEX idx_soldiers_service_number ON soldiers(service_number);

-- Tertiary Indexes (Filtering)
CREATE INDEX idx_officers_death_date ON officers(death_date);
CREATE INDEX idx_soldiers_death_date ON soldiers(death_date);
CREATE INDEX idx_soldiers_birth_town ON soldiers(birth_town);

-- Composite Indexes (Common Multi-Column Queries)
CREATE INDEX idx_officers_battalion_rank ON officers(battalion_id, rank_id);
CREATE INDEX idx_soldiers_battalion_death ON soldiers(battalion_id, death_date);
```

### Query Examples

```sql
-- Example 1: Find all officers named "ADAMSON"
SELECT * FROM officers WHERE surname = 'ADAMSON' ORDER BY christian_names;
-- Supported by: idx_officers_surname

-- Example 2: Find all soldiers from "Birmingham"
SELECT * FROM soldiers WHERE birth_town = 'Birmingham' ORDER BY surname;
-- Supported by: idx_soldiers_birth_town

-- Example 3: Find casualties (death_date is not null)
SELECT * FROM soldiers WHERE death_date IS NOT NULL AND battalion_id = 1;
-- Supported by: idx_soldiers_battalion_death

-- Example 4: List all ranks with officer count
SELECT r.rank_normalized, COUNT(*) as officer_count 
FROM officers o 
JOIN ranks r ON o.rank_id = r.rank_id 
GROUP BY o.rank_id 
ORDER BY r.sort_order;
-- Supported by: indexes on rank_id
```

---

## 10. Acceptance Criteria

### Acceptance Criteria: Schema Design

- [ ] All 7 source tables mapped to normalized schema
- [ ] No data loss in mapping
- [ ] Schema validated by data steward
- [ ] Schema documented with ER diagram

### Acceptance Criteria: Data Loading

- [ ] officers table: 41,846 ± 0 rows
- [ ] soldiers table: 661,960 rows (exact count verified)
- [ ] ranks table: 547 ± 0 rows
- [ ] All referential integrity constraints satisfied
- [ ] No NULL primary keys

### Acceptance Criteria: Validation

- [ ] All row counts match sources (±0 rows)
- [ ] Checksum verification PASS for all tables
- [ ] Spot check (5 records/table): 100% match with CSV
- [ ] All validation queries return 0 errors
- [ ] Performance testing: all queries < 1 second

### Acceptance Criteria: Rollback

- [ ] Rollback procedure documented
- [ ] Rollback tested from backup
- [ ] Recovery time < 30 minutes
- [ ] Data integrity verified post-rollback

### Acceptance Criteria: Documentation

- [ ] Schema diagram (ER diagram) created
- [ ] Migration procedure documented
- [ ] Validation procedure documented
- [ ] Query examples provided
- [ ] README updated with database info

---

## 11. Success Metrics

### Quantitative Metrics

- **Data Migration:** 100% of 703,806 records successfully migrated
- **Validation:** 0 errors in validation checks
- **Performance:** All queries complete in < 1 second
- **Completeness:** 0 missing values in required fields (surname, service_number, rank_id)

### Qualitative Metrics

- **Data Quality:** Stakeholder confidence in data accuracy
- **Usability:** Schema supports all planned UI queries efficiently
- **Maintainability:** Schema is understandable and easy to extend

---

## 12. Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
| --- | --- | --- | --- |
| Data loss during migration | Critical | Low | Run validation checks; test rollback |
| Performance degradation | High | Medium | Benchmark queries; add indexes as needed |
| Schema design misses requirements | High | Medium | Get stakeholder review early; iterate |
| CSV source corruption | High | Low | Work from PRD A backups; validate pre-migration |
| Date parsing errors | Medium | Medium | Unit test date parsing; log all failures |

---

## 13. Timeline & Milestones

| Milestone | Target Date | Deliverables |
| ----------- | --- | --- |
| **M1: Schema Design** | Week 1, Day 2 | ERD diagram; schema DDL approved |
| **M2: Migration Scripts** | Week 1, Day 4 | All scripts complete and unit tested |
| **M3: Initial Load** | Week 2, Day 1 | All data loaded; no errors |
| **M4: Validation Complete** | Week 2, Day 2 | All checks pass; signed off |
| **M5: Rollback Tested** | Week 2, Day 3 | Recovery tested and documented |
| **M6: Production Ready** | Week 2, Day 4 | Database tagged v1.0; committed to repo |

---

## 14. Open Questions

1. **Q:** Should soldiers table be partitioned by battalion for faster queries?  
   **A:** No; keep monolithic for simplicity; revisit if performance issues arise.

2. **Q:** Should we archive historical schema changes?  
   **A:** Yes; tag each major schema version in Git.

3. **Q:** What's the policy for data corrections post-migration?  
   **A:** TBD by data steward; could include audit table tracking changes.

4. **Q:** Should we support regimental hierarchies (Regiment → Battalion → Company)?  
   **A:** Not for MVP; schema designed to support this in future versions.

---

## 15. Appendices

### A. Glossary

- **ETL:** Extract, Transform, Load
- **ERD:** Entity-Relationship Diagram
- **ACID:** Atomicity, Consistency, Isolation, Durability
- **FK:** Foreign Key

### B. References

- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [SQL Best Practices](https://use-the-index-luke.com/)
- [Normalization Resources](https://www.guru99.com/database-normalization.html)

### C. Sign-Off

| Role | Name | Date | Status |
| ------ | ------ | ------ | -------- |
| Product Owner | TBD | 16 Feb 2026 | Pending |
| Data Steward | TBD | 16 Feb 2026 | Pending |
| Tech Lead | TBD | 16 Feb 2026 | Pending |

---

**Document Version:** 1.0  
**Last Updated:** 16 February 2026  
**Next Review:** Week 2 of implementation
