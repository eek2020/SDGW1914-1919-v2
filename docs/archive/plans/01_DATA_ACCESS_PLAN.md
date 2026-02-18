# Data Access Plan

## Legacy Database Modernization Project – SDGW 1914-1919

**Date:** 16 February 2026  
**Status:** Approved  
**Version:** 1.0

---

## Executive Summary

This document outlines the strategy for safely accessing and reading data from the Microsoft Access database (`sd_2011.mdb`). The database contains historical military personnel records (officers and soldiers) from 1914-1919, with rank information and battalion assignments.

**Key Finding:** Direct access is possible and verified using open-source, Mac-native tools. No paid software or complex drivers are required.

---

## Problem Statement

- **Database Format:** Microsoft Access `.mdb` file
- **Operating Environment:** macOS (no MS Access available)
- **Constraint:** Need to read, extract, and eventually migrate data
- **Risk:** .mdb files can be corrupted or contain incompatibilities with older software

---

## Options Evaluated

### Option 1: MDB Tools (Command Line) ✓ RECOMMENDED

| Criteria | Rating | Notes |
| :--- | :--- | :--- |
| Ease of Use | ★★★★★ | Simple `brew install mdbtools` |
| Cost | Free | Open-source (LGPL licensed) |
| Reliability | ★★★★★ | Field tested with this database |
| Portability | ★★★★★ | Works on macOS, Linux, and Windows |
| Performance | ★★★★ | Fast extraction and handles large tables |
| Scripting | ★★★★★ | Command-line interface ideal for automation |

**Status:** ✓ **Tested and working** against `sd_2011.mdb`

---

### Option 2: MDB Viewer (GUI Mac App)

| Criteria    | Rating | Notes                                       |
| :---------- | :----- | :------------------------------------------ |
| Ease of Use | ★★★★★  | Simple `brew install mdbtools`              |
| Cost        | Free   | Open-source (LGPL licensed)                 |
| Reliability | ★★★★★  | Field tested with this database             |
| Portability | ★★★★★  | Works on macOS, Linux, and Windows          |
| Performance | ★★★★   | Fast extraction and handles large tables    |
| Scripting   | ★★★★★  | Command-line interface ideal for automation |

**Status:** Not recommended for this project (not scriptable, costs money)

---

### Option 3: Convert to SQLite via mdbtools

| Criteria    | Rating | Notes                                 |
| :---------- | :----- | :------------------------------------ |
| Ease of Use | ★★★    | Requires intermediate conversion step |
| Cost        | Free   | SQLite + mdbtools both open-source    |
| Reliability | ★★★★   | Schema may need adjustment            |
| Portability | ★★★★★  | SQLite runs everywhere                |
| Performance | ★★★★★  | Optimized for queries                 |
| Scripting   | ★★★★   | Needs SQL knowledge                   |

**Status:** Secondary approach; use after initial data extraction

---

### Option 4: LibreOffice Base

| Criteria    | Rating | Notes                            |
| :---------- | :----- | :------------------------------- |
| Ease of Use | ★★★    | GUI can be clunky                |
| Cost        | Free   | Open-source                      |
| Reliability | ★★     | Poor MDB support on modern macOS |
| Portability | ★★★    | Cross-platform but heavy         |
| Performance | ★★     | Slow with large datasets         |
| Scripting   | ★      | Limited scripting capabilities   |

**Status:** Not recommended

---

## Chosen Approach

### Primary Path: **mdbtools (Command Line)**

**Installation:**

```bash
brew install mdbtools
```

**Version:** 1.0.1 (latest on Homebrew)

**Key Commands:**

```bash
# List tables
mdb-tables -1 database.mdb

# Export single table to CSV
mdb-export database.mdb TableName > TableName.csv

# View schema
mdb-schema database.mdb

# Export all tables
for table in $(mdb-tables -1 database.mdb); do
    mdb-export database.mdb "$table" > "${table}.csv"
done
```

**Why This Approach:**

1. ✓ Tested against actual database (see Access Report)
2. ✓ Open-source and free
3. ✓ Works on macOS without external dependencies beyond Homebrew
4. ✓ CLI-based (scriptable, automatable)
5. ✓ Produces standard CSV format (portable, opens anywhere)
6. ✓ No licensing concerns
7. ✓ Low maintenance burden

---

## Fallback Approach

### Secondary Path: **Python with mdbtools subprocess**

If command-line interface proves inconvenient, use Python to:

- Wrap mdbtools commands
- Parse CSV outputs programmatically
- Perform validation and transformation
- Log operations

**Advantages:**

- More programmatic control
- Easier error handling
- Built-in validation
- Can be integrated into larger pipelines

**Example:**

```python
import subprocess

result = subprocess.run(
    ["mdb-export", "data/sd_2011.mdb", "OFFICERS"],
    capture_output=True,
    text=True,
    timeout=60
)
csv_data = result.stdout
```

---

## Error Handling Strategy

| Error Scenario    | Detection                     | Response                                                      |
| :---------------- | :---------------------------- | :------------------------------------------------------------ |
| Database corrupt  | `mdb-export` fails with error | Attempt recovery: restore from backup, verify MDB integrity   |
| Permission denied | File access error             | Check file permissions with `ls -la`                          |
| Table too large   | Process timeout               | Export in chunks by adding WHERE clauses (future enhancement) |
| Encoding issues   | Garbled text in CSV           | Verify UTF-8 encoding; convert if necessary                   |
| Missing mdbtools  | Command not found             | Install via `brew install mdbtools`                           |

---

## Logging Approach

All data extraction operations must be logged to `logs/data_access.log`:

```text
[2026-02-16 15:30:22] INFO - Starting database export
[2026-02-16 15:30:25] INFO - Exported table SD_RANKS (547 rows)
[2026-02-16 15:30:28] INFO - Exported table SD_Battalions (721 rows)
[2026-02-16 15:31:45] WARN - SOLDIERS table timed out after 60s (large table)
[2026-02-16 15:31:46] INFO - Completed with 1 warning
```

---

## Backup Strategy

**Current Database Protection:**

1. Source file location: `/Users/erichook-marshall/Downloads/SDGW 1914-1919/data/sd_2011.mdb`
2. Create backup before any modification:

   ```bash
   cp data/sd_2011.mdb data/sd_2011.mdb.backup.$(date +%Y%m%d_%H%M%S)
   ```

3. Automated backup on monthly schedule (post-deployment)

**CSV Export Protection:**

- Keep all exported CSVs in version control (Git)
- Tag major releases: `v1.0-initial-extract`, `v2.0-validated`, etc.

---

## Security Considerations

1. **No Sensitive Credentials:** MDB file is local; no database authentication required
2. **Data Classification:** Military historical data (1914-1919); not classified but treat respectfully
3. **Access Control:** Restrict access to repository to team members only
4. **Backup Encryption:** Future backups should be encrypted if stored offsite
5. **Audit Trail:** Log all data exports for compliance (see Logging Approach)

---

## Test Plan

### Smoke Tests (Pre-Migration)

```bash
# Test 1: Verify mdbtools is installed
mdb-tables -1 data/sd_2011.mdb | wc -l
# Expected Output: 7 tables

# Test 2: Export each table and verify not empty
for table in $(mdb-tables -1 data/sd_2011.mdb); do
    lines=$(mdb-export data/sd_2011.mdb "$table" | wc -l)
    [ $lines -gt 0 ] && echo "✓ $table"
done

# Test 3: Verify column counts match schema
mdb-schema data/sd_2011.mdb | grep "CREATE TABLE"
# Cross-reference with schema in docs
```

### Validation Tests (Post-Export)

- Row counts match expectations
- No NULL values in primary keys
- Date fields are parseable
- No truncated text (CSV truncation check)

---

## Success Criteria

- [x] mdbtools installed and functional
- [x] All 7 tables accessible
- [x] Schema documented
- [x] Sample data extracted
- [x] No corruption detected
- [ ] Full dataset exported to CSV (next phase)
- [ ] Row counts validated (next phase)
- [ ] Data loaded into target database (next phase)

---

## Next Steps

1. **Execute:** Export all tables to CSV format (see PRD B)
2. **Validate:** Run checksums and row count validation
3. **Plan:** Finalize target database choice (SQLite vs PostgreSQL)
4. **Design:** Create schema transformation rules
5. **Build:** Develop UI (see PRD C)

---

## Appendices

### A. mdbtools Documentation

- Homepage: <http://mdbtools.sourceforge.net>
- License: LGPL v2.0
- Installed Version: 1.0.1
- Installation Date: 16 February 2026

### B. Database File Metadata

- `Location:` `/Users/erichook-marshall/Downloads/SDGW 1914-1919/data/sd_2011.mdb`
- `Size:` ~150 MB (approximate)
- `Format:` Microsoft Access 2000-2003 (.mdb)
- `Platform:` Cross-platform compatible
- `Last Modified:` Unknown (to be determined)

---

**Approved by:** Engineering Team  
**Review Date:** 16 February 2026  
**Next Review:** Upon completion of data migration phase
