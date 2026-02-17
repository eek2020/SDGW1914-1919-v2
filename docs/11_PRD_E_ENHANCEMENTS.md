# PRD E: Enhancement Backlog

## Product Requirements Document – SDGW 1914-1919 Modernization

**Version:** 1.0
**Date:** 17 February 2026
**Status:** Draft — Prioritized Backlog
**Audience:** Engineering Team & Stakeholders
**Source:** Parity Report (`10_PARITY_REPORT.md`) — gaps, regressions, and opportunities identified during legacy-to-modern system audit.

---

## 1. Document Purpose

This PRD consolidates all enhancement opportunities identified during the comprehensive system audit. Items are organized by priority and effort, with full acceptance criteria. This document covers features that:

- Close gaps between old and new systems
- Fix regressions from the legacy system
- Add new capabilities enabled by modern architecture
- Address technical debt and testing gaps

Items already covered by PRD D (Desktop Application) are cross-referenced but not duplicated.

---

## 2. Enhancement Registry

### Priority Definitions

| Priority | Meaning | Timeline |
| --- | --- | --- |
| **P0 — Critical** | Regression from legacy; must fix before any user testing | This sprint |
| **P1 — High** | Significant gap or risk; needed for MVP quality | Next sprint |
| **P2 — Medium** | Important improvement; needed before production | Within 4 weeks |
| **P3 — Low** | Nice-to-have; can defer to post-launch | Backlog |

### Summary Table

| ID | Enhancement | Priority | Effort | PRD D? |
| --- | --- | --- | --- | --- |
| ENH-01 | Human-readable death dates | P0 | 1 hour | No |
| ENH-02 | UI test suite (test_ui.py) | P1 | 4 hours | No |
| ENH-03 | Breadcrumb navigation | P2 | 2 hours | Yes (§6.2) |
| ENH-04 | Export results to CSV | P2 | 4 hours | Phase 2 |
| ENH-05 | Copy record to clipboard | P3 | 2 hours | No |
| ENH-06 | Saved record lists / bookmarks | P3 | 1 week | Phase 2 |
| ENH-07 | Formal accessibility audit | P2 | 2 hours | No |
| ENH-08 | Loading indicator | P3 | 1 hour | Yes (§P4) |
| ENH-09 | User guide documentation | P3 | 4 hours | Yes (§18 Q2) |
| ENH-10 | First/Last record nav in detail view | P3 | 1 hour | Yes (§9.3) |
| ENH-11 | PRD B schema alignment update | P2 | 1 hour | No |
| ENH-12 | PRD C implementation alignment update | P2 | 2 hours | No |
| ENH-13 | Missing files cleanup (INDEX.md refs) | P3 | 30 min | No |

---

## 3. Detailed Specifications

### ENH-01: Human-Readable Death Dates

**Priority:** P0 — Critical (regression from legacy system)

**Problem Statement:**

Death dates throughout the application display in ISO format ("1915-09-05") instead of a human-readable format. The old system showed "DD/MM/YY" (e.g., "05/09/15"). Neither format is ideal for the target audience (65+ years old), who expect conventional English date formatting.

This affects:

- Detail page (`detail.html`) — death_date field
- Search results cards (`search_results.html`) — card subtitle
- Search results table (`search_results.html`) — Death Date column

**User Story:**

> As a genealogy researcher aged 70+, I want death dates shown as "5 September 1915" so I can read them naturally without mentally parsing ISO format.

**Requirements:**

| # | Requirement | Acceptance Criteria |
| --- | --- | --- |
| R1 | Add Jinja2 template filter `humandate` to `web_app.py` | Filter registered, converts ISO date string to human format |
| R2 | Detail page shows full format: "5 September 1915" | `{{ record.death_date\|humandate }}` renders correctly |
| R3 | Results cards show abbreviated: "5 Sep 1915" | `{{ record.death_date\|humandate_short }}` renders correctly |
| R4 | Results table shows abbreviated: "5 Sep 1915" | Same as R3 |
| R5 | Null/empty dates render as empty (not "None") | `{{ None\|humandate }}` returns empty string |
| R6 | Invalid date strings render original text | `{{ "unknown"\|humandate }}` returns "unknown" |

**Implementation:**

```python
@app.template_filter('humandate')
def human_date(value):
    """Convert ISO date to '5 September 1915' format."""
    if not value:
        return ''
    try:
        dt = datetime.strptime(str(value), '%Y-%m-%d')
        return dt.strftime('%-d %B %Y')
    except (ValueError, TypeError):
        return str(value)

@app.template_filter('humandate_short')
def human_date_short(value):
    """Convert ISO date to '5 Sep 1915' format."""
    if not value:
        return ''
    try:
        dt = datetime.strptime(str(value), '%Y-%m-%d')
        return dt.strftime('%-d %b %Y')
    except (ValueError, TypeError):
        return str(value)
```

**Effort:** 1 hour
**Risk:** Low — purely presentational change; no data modification

---

### ENH-02: UI Test Suite

**Priority:** P1 — High (testing gap)

**Problem Statement:**

Zero UI-specific automated tests exist. `tests/test_web_app.py` has 43 tests covering Flask route responses, but no tests verify:

- Template HTML structure and content
- Pagination link correctness (all search params preserved)
- Filter pill rendering
- Record navigation links
- Sort control rendering
- Card vs table view HTML
- 404 page content
- Death date formatting (after ENH-01)
- Accessibility attributes (ARIA labels, skip-to-main)

**User Story:**

> As a developer, I want automated UI tests so that template changes don't silently break search results, pagination, or accessibility features.

**Requirements:**

| # | Requirement |
| --- | --- |
| R1 | Create `tests/test_ui.py` |
| R2 | ≥ 20 test functions |
| R3 | Cover home page form fields and structure |
| R4 | Cover search results — card view rendering |
| R5 | Cover search results — table view rendering |
| R6 | Cover search results — pagination links with search params |
| R7 | Cover search results — filter pills for active filters |
| R8 | Cover search results — sort dropdown |
| R9 | Cover detail page — field grouping |
| R10 | Cover detail page — related records links |
| R11 | Cover detail page — record navigation (prev/next) |
| R12 | Cover 404 page |
| R13 | Cover accessibility — skip-to-main link |
| R14 | Cover accessibility — ARIA landmarks |
| R15 | All tests pass with `python3 -m pytest tests/test_ui.py -v` |

**Implementation Notes:**

- Use Flask test client (`app.test_client()`)
- Parse HTML responses with BeautifulSoup (`pip install beautifulsoup4`)
- Assert on specific HTML elements, attributes, and text content
- Add `beautifulsoup4` to `requirements.txt`

**Effort:** 4 hours
**Risk:** Medium — requires test database with known data for deterministic assertions

---

### ENH-03: Breadcrumb Navigation

**Priority:** P2 — Medium

**Problem Statement:**

Users navigating from Home → Results → Detail have no visual trail showing their position. PRD C §P3 requires "consistent layout" and PRD D §6.2 specifies breadcrumbs (`Home > Results (47) > Smith, James`). Not yet implemented.

**User Story:**

> As an elderly user, I want to see where I am in the app (Home > Results > Record) so I don't feel lost or need to use the browser back button.

**Requirements:**

| # | Requirement |
| --- | --- |
| R1 | Breadcrumb bar visible on Results page: `Home > Results (X found)` |
| R2 | Breadcrumb bar visible on Detail page: `Home > Results (X) > SURNAME, First` |
| R3 | Each breadcrumb segment is a clickable link |
| R4 | Home link goes to `/` |
| R5 | Results link preserves search parameters |
| R6 | Font size ≥ 16px, contrast meets WCAG AAA |
| R7 | Breadcrumb uses semantic HTML (`<nav aria-label="Breadcrumb">`) |

**Effort:** 2 hours

---

### ENH-04: Export Results to CSV

**Priority:** P2 — Medium (legacy feature gap)

**Problem Statement:**

The old system had "Save Records" functionality. Researchers doing batch analysis need to save search results for offline use. Currently no export capability exists.

**User Story:**

> As a historian researching a battalion, I want to export my search results to a CSV file so I can analyze them in a spreadsheet.

**Requirements:**

| # | Requirement |
| --- | --- |
| R1 | "Export CSV" button visible on results page when results > 0 |
| R2 | New route `GET /export-csv` runs same search, returns all results as CSV |
| R3 | CSV includes headers: Surname, Christian Names, Type, Rank, Battalion, Service Number, Death Date, Death Location, Birth Town |
| R4 | CSV uses UTF-8 encoding with BOM for Excel compatibility |
| R5 | Maximum 10,000 rows per export (prevent memory issues) |
| R6 | If results > 10,000, show message: "Showing first 10,000 of X results" |
| R7 | File downloads as `sdgw_results_YYYYMMDD.csv` |
| R8 | Button disabled during download |

**Effort:** 4 hours
**Risk:** Low — read-only operation; no data modification

---

### ENH-05: Copy Record to Clipboard

**Priority:** P3 — Low (legacy feature: clipboard icon on detail view)

**Problem Statement:**

The old system had a clipboard icon on the detail view. Users want to quickly copy record data to paste into emails or documents.

**User Story:**

> As a family member, I want to copy a soldier's record details with one click so I can paste it into an email to share with relatives.

**Requirements:**

| # | Requirement |
| --- | --- |
| R1 | "Copy to Clipboard" button on detail page, near Print button |
| R2 | Copies formatted plain text summary |
| R3 | Format: Name, Rank, Battalion, Service Number, Death Date, Death Location, Birth Town — one field per line |
| R4 | Shows brief "Copied!" confirmation (2 seconds) |
| R5 | Falls back gracefully if clipboard API unavailable |

**Effort:** 2 hours

---

### ENH-06: Saved Record Lists / Bookmarks

**Priority:** P3 — Low (legacy feature: "User Lists")

**Problem Statement:**

The old system had "User Lists" — saved collections of records. Genealogy researchers build lists of related individuals over multiple sessions.

**User Story:**

> As a genealogy researcher, I want to bookmark records during my search session so I can return to them later without re-searching.

**Requirements:**

| # | Requirement |
| --- | --- |
| R1 | Star/bookmark icon on each result card and detail page |
| R2 | Click toggles bookmark state (filled/unfilled star) |
| R3 | Bookmarks stored in browser localStorage |
| R4 | "My Saved Records" page accessible from header navigation |
| R5 | Saved Records page shows list of bookmarked records with links |
| R6 | Can remove individual bookmarks |
| R7 | Can export bookmarks to CSV (reuse ENH-04 format) |
| R8 | Bookmarks persist across browser sessions |

**Effort:** 1 week
**Risk:** Medium — localStorage has ~5MB limit; sufficient for thousands of bookmarks

---

### ENH-07: Formal Accessibility Audit

**Priority:** P2 — Medium (PRD C AC4 requirement)

**Problem Statement:**

PRD C acceptance criteria require WAVE accessibility audit with 0 errors and Lighthouse score ≥ 95. CSS targets WCAG AAA compliance, but no formal audit has been performed.

**User Story:**

> As the product owner, I want verified accessibility compliance so I can be confident the app works for users with vision impairments.

**Requirements:**

| # | Requirement |
| --- | --- |
| R1 | Run WAVE on Home, Results, and Detail pages |
| R2 | Run Lighthouse accessibility audit on same pages |
| R3 | Fix all errors found |
| R4 | Document results in `docs/ACCESSIBILITY_AUDIT.md` |
| R5 | WAVE: 0 errors, 0 contrast errors |
| R6 | Lighthouse: Accessibility score ≥ 95 |

**Effort:** 2 hours (audit) + variable (fixes)

---

### ENH-08: Loading Indicator

**Priority:** P3 — Low

**Problem Statement:**

No visual feedback during search submission. PRD D §P4 specifies: "If a query takes > 200ms, show a spinner with 'Searching…'"

**Requirements:**

| # | Requirement |
| --- | --- |
| R1 | On form submit, show "Searching..." overlay |
| R2 | Overlay disappears when results page loads |
| R3 | CSS-only spinner animation (no JS library) |
| R4 | Accessible: `role="status"` and `aria-live="polite"` |

**Effort:** 1 hour

---

### ENH-09: User Guide Documentation

**Priority:** P3 — Low

**Problem Statement:**

`docs/USER_GUIDE.md` is referenced in `INDEX.md` but never created. The old system had a dedicated help application (SDHELP.exe).

**Requirements:**

| # | Requirement |
| --- | --- |
| R1 | Create `docs/USER_GUIDE.md` |
| R2 | Written in plain language for 65+ audience |
| R3 | Cover: searching by name, number, filters |
| R4 | Cover: reading results, sorting, pagination |
| R5 | Cover: viewing and printing records |
| R6 | Cover: tips for finding ancestors |
| R7 | Cover: common problems and solutions |

**Effort:** 4 hours

---

### ENH-10: First/Last Record Navigation in Detail View

**Priority:** P3 — Low

**Problem Statement:**

Old system had `<< First Record` and `Last Record >>` buttons in the detail view. New system only has Previous/Next.

**Requirements:**

| # | Requirement |
| --- | --- |
| R1 | Add `« First` and `Last »` links to detail page navigation |
| R2 | First jumps to record index 0 in result set |
| R3 | Last jumps to final record index |
| R4 | Links disabled when already at first/last position |

**Effort:** 1 hour

---

### ENH-11: PRD B Schema Alignment Update

**Priority:** P2 — Medium (documentation debt)

**Problem Statement:**

PRD B schema documentation diverges from actual implementation:

- PRD says 6 tables; actual has 8 (added `surname_lookup`, split regiment_battalion into `_sd` and `_od`)
- PRD says `enlistment_location`; code uses `enlistment_loc`
- PRD says `additional_notes`; code uses `additional_text`
- PRD specifies `created_at`/`updated_at` columns; not implemented
- PRD says 7 indexes; actual has 27

**Requirements:**

| # | Requirement |
| --- | --- |
| R1 | Update PRD B §5.2 schema to match actual implementation |
| R2 | Document column name mapping (PRD name → actual name) |
| R3 | Note `created_at`/`updated_at` as not implemented (read-only data) |
| R4 | Update index count and list |
| R5 | Add `surname_lookup` table documentation |
| R6 | Update version to 1.1 with changelog |

**Effort:** 1 hour

---

### ENH-12: PRD C Implementation Alignment Update

**Priority:** P2 — Medium (documentation debt)

**Problem Statement:**

PRD C was written before implementation. Several features were added or changed during development that aren't reflected in the PRD:

- 12 search fields (PRD specified fewer)
- Tom Select / autocomplete dependency not documented
- 50 results per page (PRD says 10)
- Card/table toggle added
- 5 sort options added
- Filter pills added
- Record-by-record navigation added
- API endpoints (`/api/surname-suggest`, `/api/filter-options`) undocumented
- `test_web_app.py` exists with 43 tests (not in PRD deliverables)

**Requirements:**

| # | Requirement |
| --- | --- |
| R1 | Update PRD C §7.1 Home Page to reflect 12 search fields |
| R2 | Add Tom Select CDN to tech stack section |
| R3 | Update results per page from 10 to 50 (with rationale) |
| R4 | Document card/table view toggle |
| R5 | Document 5 sort options |
| R6 | Document filter pills |
| R7 | Document record-by-record navigation in detail view |
| R8 | Add API endpoints section |
| R9 | Add `test_web_app.py` to deliverables |
| R10 | Add death date format acceptance criterion |
| R11 | Update version to 1.2 with changelog |

**Effort:** 2 hours

---

### ENH-13: Missing Files Cleanup

**Priority:** P3 — Low (documentation debt)

**Problem Statement:**

`INDEX.md` references several files that don't exist:

- `docs/USER_GUIDE.md`
- `docs/DATA_DICTIONARY.md`
- `docs/ADMIN_GUIDE.md`
- `Dockerfile`
- `setup.py`
- `CHANGELOG.md`

**Requirements:**

Either create stub files or remove references from INDEX.md.

**Effort:** 30 minutes

---

## 4. Dependency Graph

```text
ENH-01 (dates)  ──→  ENH-02 (UI tests — need correct dates to test)
                 └──→  ENH-12 (PRD C update — document date format)

ENH-03 (breadcrumbs) ──→ standalone

ENH-04 (CSV export) ──→ standalone
                    └──→ ENH-06 (bookmarks — reuse CSV export)

ENH-07 (a11y audit) ──→ ENH-01 (fix dates first)
                    └──→ ENH-03 (add breadcrumbs first)

ENH-11 (PRD B update) ──→ standalone
ENH-12 (PRD C update) ──→ ENH-01 (document date fix)
```

---

## 5. Recommended Execution Order

1. **ENH-01** — Human-readable dates (P0, 1 hr) — fixes the most visible regression
2. **ENH-02** — UI test suite (P1, 4 hrs) — prevents future regressions
3. **ENH-11** — PRD B alignment (P2, 1 hr) — quick documentation fix
4. **ENH-12** — PRD C alignment (P2, 2 hrs) — quick documentation fix
5. **ENH-03** — Breadcrumbs (P2, 2 hrs) — UX improvement
6. **ENH-07** — Accessibility audit (P2, 2 hrs) — compliance verification
7. **ENH-04** — CSV export (P2, 4 hrs) — feature parity with old system
8. **ENH-10** — First/Last record nav (P3, 1 hr) — quick win
9. **ENH-08** — Loading indicator (P3, 1 hr) — quick win
10. **ENH-05** — Copy to clipboard (P3, 2 hrs) — convenience
11. **ENH-13** — Missing files cleanup (P3, 30 min) — housekeeping
12. **ENH-09** — User guide (P3, 4 hrs) — documentation
13. **ENH-06** — Saved record lists (P3, 1 week) — largest effort, lowest priority

**Total estimated effort:** ~3.5 engineering days

---

## 6. Relationship to PRD D

Several enhancements overlap with PRD D (Desktop Application) scope:

| Enhancement | PRD D Coverage | Action |
| --- | --- | --- |
| ENH-01 (dates) | §9.3 specifies "human-readable format" | **Do now** — benefits Flask app immediately |
| ENH-03 (breadcrumbs) | §6.2 specifies breadcrumbs | **Do now** — benefits Flask app; carries into desktop |
| ENH-04 (CSV export) | §18 Q3 defers to Phase 2 | **Do now for web** — simple Flask route |
| ENH-06 (bookmarks) | Not explicitly in PRD D | Keep in backlog |
| ENH-08 (loading indicator) | §P4 specifies loading feedback | Can do with or before PRD D |
| ENH-09 (user guide) | §18 Q2 requires in-app help | Can do with PRD D |
| ENH-10 (First/Last nav) | §9.3 specifies full nav | Can do with PRD D |

---

## 7. Sign-Off

| Role | Name | Date | Status |
| --- | --- | --- | --- |
| Product Owner | TBD | 17 Feb 2026 | Pending |
| Tech Lead | TBD | 17 Feb 2026 | Pending |

---

**Document Version:** 1.0
**Created:** 17 February 2026
**Source:** System audit documented in `10_PARITY_REPORT.md`
**Next Review:** After ENH-01 and ENH-02 are complete
