# PRD D: Desktop Application

## Product Requirements Document – SDGW 1914-1919 Modernization

**Version:** 1.0
**Date:** 16 February 2026
**Status:** Draft
**Audience:** Engineering Team & Stakeholders

---

## 1. Document Purpose

This PRD defines the requirements for delivering the SDGW 1914-1919 personnel database as a **standalone desktop application** that is intuitive enough for a 70-year-old user, supports rich category filtering alongside ambiguous/fuzzy search, and can be developed on macOS while targeting deployment on Windows 11.

This document supersedes and extends the UI direction established in PRD C (Basic UI). PRD C's Flask prototype validated the data layer and search logic; this PRD carries that forward into a distributable desktop experience.

---

## 2. Business Context

### Problem

- The Phase C Flask prototype proves the search and data layer work, but it requires a running Python environment and browser — unsuitable for a non-technical end user on Windows.
- The primary audience (genealogy researchers, family members) skews heavily towards ages 60–80+. They need an interface that is **immediately understandable**, with large controls, forgiving input, and zero setup.
- The application will not be code-signed or distributed through a store. It must run on the target Windows 11 machine without administrator privileges or complex installation.

### Goals

- **Zero-friction launch:** Double-click to open; no installer, no browser, no terminal.
- **Senior-first design:** Every interaction designed for a 70-year-old who may have limited computer experience, reduced vision, and slower motor control.
- **Ambiguous search:** Users often don't know exact spellings, dates, or categories. The system must tolerate misspellings, partial input, and vague queries.
- **Rich filtering:** 703,806 records span many categories (rank, battalion, death location, birth town, dates). Filters must narrow results quickly without overwhelming the user.
- **Cross-platform development:** Built on macOS, tested and shipped on Windows 11. Architecture must support both without separate codebases.

### Constraints

- **No code signing or distribution channel.** App will be copied to the target machine directly (USB, network share, etc.).
- **No internet required at runtime.** All data is local (SQLite).
- **No admin rights on target machine.** Must run from a user-writable directory.
- **Development on macOS (Apple Silicon).** Windows 11 machine available for later compile/test phases.
- **Existing data layer is Python + SQLite.** Preserve investment in `data_migration.py`, `schema.sql`, and the 257 MB `sd_2011.db`.

---

## 3. Scope

### In Scope ✅

- Standalone desktop application with embedded UI (no browser required)
- Full search and filter functionality from Phase C, enhanced with fuzzy/ambiguous search
- Senior-accessible UI: large text, high contrast, minimal cognitive load
- Category filtering with progressive narrowing (cascading filters)
- Record detail view with print support
- Cross-platform build pipeline (develop on Mac, build for Windows 11)
- Bundled SQLite database — single folder deployment
- Keyboard and mouse navigation optimised for older users

### Out of Scope 🚫

- Web deployment or hosting (covered by PRD C prototype)
- Mobile or tablet apps
- Code signing, Windows Store distribution, or MSI installer
- Multi-user concurrent access
- Data editing or administration features
- Online updates or telemetry
- macOS end-user build (Mac is dev-only for now)

---

## 4. Architecture Decision

### 4.1 Framework Evaluation

| Framework | Language | Windows Binary | Mac Dev | SQLite | Senior UI | Bundle Size | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Electron + JS** | JavaScript | ✅ exe | ✅ | ✅ via better-sqlite3 | ✅ Full CSS control | ~150 MB | Large bundle |
| **Tauri + JS** | Rust + JS | ✅ exe | ✅ | ✅ native | ✅ Full CSS control | ~10 MB | ✅ Small, fast |
| **PyQt / PySide** | Python | ✅ via PyInstaller | ✅ | ✅ built-in | ⚠️ Native widgets | ~80 MB | Python reuse |
| **Tkinter** | Python | ✅ via PyInstaller | ✅ | ✅ built-in | ❌ Limited styling | ~50 MB | Poor UX control |
| **Flutter Desktop** | Dart | ✅ exe | ✅ | ✅ via sqflite | ✅ Custom UI | ~20 MB | New language |
| **CustomTkinter** | Python | ✅ via PyInstaller | ✅ | ✅ built-in | ⚠️ Better than Tk | ~60 MB | Moderate UX |

### 4.2 Recommended Approach: **Python Desktop with Web UI (PyWebView or Flask + webview wrapper)**

**Rationale:**

1. **Preserves existing investment.** Phase C's Flask app, Jinja templates, CSS, and SQLite queries all carry forward with zero rewrite.
2. **Full CSS/HTML control.** Allows the exact same senior-friendly styling (large fonts, high contrast, WCAG AAA) already designed in PRD C.
3. **Cross-platform.** `pywebview` renders via the OS native webview (Edge WebView2 on Windows 11, WebKit on macOS). Builds via PyInstaller for Windows .exe.
4. **Minimal new dependencies.** Add `pywebview` to existing Flask app; bundle with PyInstaller.
5. **No browser required.** The webview is embedded — user sees a native window, not a browser tab.
6. **Small learning curve.** Team already knows Python, Flask, HTML/CSS.

**Alternative considered:** Tauri is technically superior (smaller bundle, Rust backend) but requires rewriting the Python data/query layer in Rust and the team learning a new toolchain. Not justified given the constraints.

### 4.3 Architecture Diagram

```text
┌──────────────────────────────────────────────────────┐
│                    Desktop Window                      │
│              (pywebview native window)                 │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │           HTML / CSS / JavaScript                 │ │
│  │     (Senior-friendly UI — same as PRD C)          │ │
│  │     Large fonts, high contrast, big buttons       │ │
│  │     Fuzzy search bar, cascading filters           │ │
│  └──────────────────────┬───────────────────────────┘ │
│                         │ HTTP (localhost)              │
│  ┌──────────────────────▼───────────────────────────┐ │
│  │        Flask Backend (embedded)                    │ │
│  │  - Search API (exact + fuzzy + prefix)            │ │
│  │  - Filter API (cascading dropdown options)        │ │
│  │  - Detail API (full record)                       │ │
│  │  - Print formatting                               │ │
│  └──────────────────────┬───────────────────────────┘ │
│                         │ sqlite3                      │
│  ┌──────────────────────▼───────────────────────────┐ │
│  │           sd_2011.db (bundled)                     │ │
│  │           257 MB SQLite — 703,806 records          │ │
│  └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘

Distribution: Single folder with .exe + sd_2011.db
              No installer. No admin rights. No internet.
```

### 4.4 Build & Distribution Pipeline

```text
Development (macOS)                    Deployment (Windows 11)
─────────────────                      ──────────────────────
Python 3.11+ Flask app                 Copy folder to target machine
  ↓                                      ↓
Test locally via pywebview             Double-click SDGW.exe
  ↓                                      ↓
Transfer to Windows build machine      App launches in native window
  ↓                                      ↓
PyInstaller → SDGW.exe                 User searches records
  ↓
Bundle sd_2011.db alongside
  ↓
Test on Windows 11
  ↓
Copy folder to USB / network share
```

**Build commands (Windows machine):**

```bash
pip install pyinstaller pywebview flask
pyinstaller --onedir --windowed --name SDGW --add-data "data/sd_2011.db;data" src/desktop_app.py
```

**Output:** `dist/SDGW/` folder containing `SDGW.exe` + `data/sd_2011.db` + runtime files.

---

## 5. Senior-First Design Principles

### P1: Designed for a 70-Year-Old

Every design decision must pass this test: *"Would my 70-year-old parent be able to use this without help after 30 seconds?"*

| Principle | Implementation |
| :--- | :--- |
| **Large everything** | 20px+ body text, 40px+ headings, 48px+ button height |
| **High contrast** | WCAG AAA (7:1+) everywhere; no light gray on white |
| **One thing at a time** | Each screen has ONE primary action; never multiple competing CTAs |
| **No jargon** | "Find a Person" not "Search Records"; "Go Back" not "Navigate" |
| **Forgiving** | Typos tolerated; partial input accepted; no error dead-ends |
| **Consistent** | Same layout, same button positions, same flow on every screen |
| **Readable results** | Name + key details at a glance; no dense tables |
| **Obvious navigation** | "Back" always top-left; "Home" always available; breadcrumb trail |

### P2: Progressive Disclosure

Don't show all 10 filter categories at once. Instead:

1. **Start simple:** Show only the search bar and "Find" button.
2. **Offer more:** A clearly labeled "More Filters" section expands to reveal dropdowns.
3. **Smart defaults:** Filters start at "All" — user narrows only if they want to.
4. **Active filter badges:** Show what's currently filtering as removable pills/tags above results.

### P3: Ambiguous Search — "I'm Not Sure What I'm Looking For"

Many users will arrive with incomplete information:

- *"My grandfather's name was something like Mcdonnel or MacDonnell"*
- *"He was a private, I think, maybe in France?"*
- *"His number was 4-something-93"*

The system must handle all of these gracefully. See Section 7 for details.

### P4: Immediate Feedback

- **As-you-type results count:** "Showing 47 matches" updates live as user types.
- **No blank screens:** Always show something — even if it's "Type a name to start."
- **Loading indicator:** If a query takes > 200ms, show a spinner with "Searching…"
- **Never a dead end:** Every "no results" screen offers clear next steps.

---

## 6. Navigation & Information Architecture

### 6.1 Screen Flow

```text
┌────────────────────────┐
│      HOME / SEARCH      │ ← Single entry point
│  ┌──────────────────┐  │
│  │ Find a Person     │  │ ← Large search bar (name, number, or anything)
│  │ [________________]│  │
│  │  [FIND]           │  │
│  │                   │  │
│  │ ▸ More Filters    │  │ ← Expandable (rank, battalion, location, dates)
│  └──────────────────┘  │
│                         │
│  Quick Links:           │
│  • Browse All Battalions│
│  • Browse by Rank       │
│  • Help & Tips          │
└─────────┬───────────────┘
          │
          ▼
┌────────────────────────┐
│     SEARCH RESULTS      │
│  Found 47 people        │
│  Active filters: [×Pvt] │ ← Removable filter pills
│                         │
│  ┌─ SMITH, James ─────┐│
│  │ Private · 51st Bn   ││ ← Card for each result
│  │ Died 15 Sep 1915    ││
│  │ [View Full Record]  ││
│  └─────────────────────┘│
│  ┌─ SMITH, John ──────┐│
│  │ Corporal · 23rd Bn  ││
│  │ Survived the war    ││
│  │ [View Full Record]  ││
│  └─────────────────────┘│
│                         │
│  [← Back]  Page 1 of 3  │
│            [Next →]      │
└─────────┬───────────────┘
          │
          ▼
┌────────────────────────┐
│    RECORD DETAIL        │
│                         │
│  SMITH, James           │
│  ─────────────────────  │
│  Personal Information   │
│  Military Service       │
│  Casualty Information   │
│  Additional Notes       │
│                         │
│  [← Back]   [Print]     │
│                         │
│  Related Records:       │
│  • Others in 51st Bn    │
│  • Died same date       │
└─────────────────────────┘
```

### 6.2 Navigation Rules

1. **"Back" is always top-left.** Every screen except Home has a visible Back button in the same position.
2. **"Home" is always reachable.** Application title in header is always clickable to return Home.
3. **Breadcrumb trail:** `Home > Results (47) > Smith, James` — always visible, always clickable.
4. **Keyboard shortcuts:**
   - `Ctrl+F` or `F3`: Focus search bar from any screen
   - `Escape`: Go back one screen
   - `Ctrl+P`: Print current record
   - `Enter`: Activate focused button
   - `Tab`: Move between controls (with visible focus ring)
5. **No deep nesting.** Maximum 3 levels deep (Home → Results → Detail). Never deeper.

---

## 7. Search & Filtering

### 7.1 Unified Search Bar ("Find a Person")

The primary search input accepts **any text** and tries to match intelligently:

| User Types | System Interprets As | Query Strategy |
| :--- | :--- | :--- |
| `Smith` | Surname | `surname LIKE 'SMITH%'` |
| `John Smith` | First + Surname | `surname LIKE 'SMITH%' AND christian_names LIKE '%JOHN%'` |
| `4493` | Service number | `service_number = '4493'` |
| `MacDonnell` | Surname (exact first, then fuzzy) | Exact → Soundex/phonetic → Levenshtein |
| `Smyth` | Surname (fuzzy) | Phonetic match to SMITH, SMYTHE, etc. |
| `51st` | Battalion name fragment | `battalions_sd.name LIKE '%51st%'` |
| `France` | Death location | `death_location LIKE '%France%'` |

## Implementation: Ambiguous Search Algorithm

```text
1. Trim and normalize input (uppercase, strip extra spaces)
2. If input is purely numeric → try service_number exact match
3. If input contains a space → split into [possible_first, possible_surname]
4. Try exact surname prefix match: surname LIKE 'INPUT%'
5. If < 5 results → try fuzzy/phonetic matching:
   a. Soundex match (built-in SQLite extension or Python soundex)
   b. Levenshtein distance ≤ 2 (for short names) or ≤ 3 (for longer)
   c. Common substitution patterns: Mac/Mc, -son/-sen, -ey/-ie, Th/T
6. If still < 5 results → try contains match: surname LIKE '%INPUT%'
7. If still 0 results → try across other fields (battalion name, location)
8. Always return results with relevance score; show best matches first
```

**"Did you mean?" Suggestions:**

When exact search yields 0 results but fuzzy finds matches, show:

```text
No exact match for "MacDonnel".
Did you mean:
  • MACDONNELL (23 records)
  • MCDONNEL (5 records)
  • MACDONALD (412 records)
```

### 7.2 Category Filters (Progressive Disclosure)

Filters are hidden by default behind **"More Filters"** — expanding reveals:

| Filter | Control Type | Values | Notes |
| :--- | :--- | :--- | :--- |
| **Record Type** | Toggle buttons | All · Officers · Soldiers | Always visible below search bar |
| **Christian Name(s)** | Text input | Free text | Matches old system's dedicated first-name field; supports partial matching |
| **Rank Group** | Large buttons | Privates · NCOs · Warrant Officers · Officers | 4 values — show as tappable cards |
| **Rank** | Searchable dropdown | 114 normalized names | Grouped by rank_group |
| **Battalion** | Searchable dropdown (grouped) | 721 battalion names | Type-ahead filtering; grouped by regiment/corps type where possible (see Appendix F.2) |
| **Death Location** | Searchable dropdown | 137 locations | e.g., "France & Flanders" — equivalent to old system's "Theatre of War" |
| **Birth Town** | Text input with autocomplete | 85K unique values | Suggest as user types; future: geographic hierarchy (Country → County) |
| **Enlistment Location** | Text input with autocomplete | 25K unique values | Not in old system but available in SDGW data |
| **Death Date** | Date range (from / to) | 1914–1919 | Simple year selector or date picker |

**Cascading filter behavior** (carried forward from Phase C):

- When user selects a battalion, rank dropdown narrows to ranks present in that battalion.
- When user types a surname, dropdowns narrow to categories that have matching records.
- Active filters shown as removable pills: `[× Private] [× 51st Bn]`

### 7.3 Search Performance Targets

| Scenario | Target | Current (Phase C validated) |
| :--- | :--- | :--- |
| Exact surname | < 100ms | 0.2ms ✅ |
| Surname prefix (LIKE) | < 200ms | 19.9ms ✅ |
| Fuzzy / phonetic | < 500ms | New — requires implementation |
| Multi-filter combination | < 300ms | 62.1ms ✅ |
| Filter cascade update | < 500ms | ~200ms ✅ |
| Full-text ambiguous search | < 1s | New — requires implementation |

---

## 8. UI Specifications

### 8.1 Typography

```text
Font Family:  "Segoe UI" (Windows), -apple-system (Mac dev)
              Both are OS-native, optimized for readability

Sizes:
  Page title:           36px bold
  Section heading:      28px bold
  Card title (name):    24px bold
  Body / labels:        20px regular
  Input fields:         20px regular
  Button text:          22px bold
  Help / secondary:     18px regular
  Breadcrumb:           16px regular

Line height:            1.6× (all sizes)
Letter spacing:         +0.3px on headings
```

### 8.2 Color Palette

```text
Primary Background:     #FFFFFF (white)
Secondary Background:   #F5F5F0 (warm off-white — easier on older eyes than pure white)
Card Background:        #FFFFFF
Card Border:            #D0D0D0

Text Primary:           #1A1A1A (near-black — softer than #000)
Text Secondary:         #4A4A4A (dark gray)
Text Muted:             #6B6B6B (used sparingly, never for critical info)

Primary Action:         #005A9C (strong blue — universally understood as "clickable")
Primary Action Hover:   #004578
Primary Action Text:    #FFFFFF

Secondary Action:       #E8E8E8 (light gray background)
Secondary Action Text:  #1A1A1A

Success / Found:        #2E7D32 (dark green)
Warning / No Results:   #C62828 (dark red — used sparingly)
Active Filter Pill:     #E3F2FD (light blue bg) + #005A9C (blue text)

Focus Ring:             #005A9C, 3px solid (highly visible)

Contrast Ratios (all WCAG AAA):
  #1A1A1A on #FFFFFF:   16.6:1 ✓
  #1A1A1A on #F5F5F0:   14.8:1 ✓
  #005A9C on #FFFFFF:    7.1:1 ✓
  #FFFFFF on #005A9C:    7.1:1 ✓
```

### 8.3 Interactive Elements

| Element | Min Size | Style | Notes |
| :--- | :--- | :--- | :--- |
| **Primary button** | 48px height, 160px width | Filled blue, white text, rounded 8px | "Find", "View Record" |
| **Secondary button** | 44px height, 120px width | Gray outline, dark text | "Back", "Clear", "Print" |
| **Text input** | 48px height | Large text, clear border, 8px radius | Visible label above, placeholder inside |
| **Dropdown** | 48px height | Same as input, with chevron | Type-to-search enabled |
| **Filter pill** | 36px height | Light blue bg, blue text, × button | Active filter indicator |
| **Result card** | Min 80px height | White card, subtle shadow, 8px radius | Clickable; hover highlights |
| **Toggle button group** | 44px height per option | Selected = blue fill; others = gray outline | "All / Officers / Soldiers" |
| **Pagination** | 44px height buttons | "← Previous" and "Next →" | Always labeled with text, not just arrows |
| **Focus ring** | 3px solid blue | On ALL interactive elements | Must be visible against both white and gray |

### 8.4 Spacing & Layout

```text
Page margins:           32px horizontal, 24px vertical
Section spacing:        32px between major sections
Card spacing:           16px between result cards
Form field spacing:     20px between fields
Button padding:         16px horizontal, 12px vertical
Container max-width:    960px (centered)
```

---

## 9. Detailed Screen Specifications

### 9.1 Home / Search Screen

```text
┌──────────────────────────────────────────────────────────────┐
│  Soldiers Died in the Great War 1914-1919                     │
│  ─────────────────────────────────────────                     │
│  Home                                                         │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Find a Person                                                │
│  ┌────────────────────────────────────────────┐  ┌────────┐ │
│  │ Type a name, number, or anything you know  │  │  FIND  │ │
│  └────────────────────────────────────────────┘  └────────┘ │
│                                                               │
│  ┌──────────┐  ┌───────────┐  ┌───────────┐                 │
│  │   All    │  │ Officers  │  │ Soldiers  │                  │
│  └──────────┘  └───────────┘  └───────────┘                 │
│                                                               │
│  ▸ More Filters (rank, battalion, location, dates)            │
│                                                               │
│  ─────────────────────────────────────────                     │
│                                                               │
│  Quick Start                                                  │
│  • Browse All Battalions                                      │
│  • Browse by Rank Group                                       │
│                                                               │
│  ─────────────────────────────────────────                     │
│                                                               │
│  Tips                                                         │
│  • Type any part of a surname — exact spelling not required   │
│  • Service numbers are for soldiers only                      │
│  • Use "More Filters" to narrow by battalion or rank          │
│  • This database contains 703,806 records from 1914-1919      │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**Key behaviors:**

- Search bar auto-focuses on launch.
- Pressing Enter or clicking Find triggers search.
- "More Filters" expands smoothly to reveal filter controls.
- Quick Start links open pre-filtered result views.

### 9.2 Search Results Screen

```text
┌──────────────────────────────────────────────────────────────┐
│  Soldiers Died in the Great War 1914-1919                     │
│  ─────────────────────────────────────────                     │
│  Home > Results                                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  [← Back]                                                     │
│                                                               │
│  47 people found for "Smith"                                  │
│  Active filters: [× Private]  [× France & Flanders]          │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  SMITH, James                                         │    │
│  │  Private · 51st Highland Division Cyclist Company     │    │
│  │  Born: Edinburgh · Died: 15 September 1915, France    │    │
│  │                                    [View Full Record] │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  SMITH, John William                                  │    │
│  │  Corporal · 23rd Battalion Royal Fusiliers            │    │
│  │  Born: London · Survived the war                      │    │
│  │                                    [View Full Record] │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  [← Previous]          Page 1 of 3          [Next →]         │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**Key behaviors:**

- Default view is cards (one person per card). A **Table View toggle** is available for users who prefer a denser, scannable layout (columns: Surname, Christian Names, Number, Rank, Battalion, Death Date). This mirrors the old system's tabular results view.
- Each card shows: **Name** (bold, large), rank, battalion, birth town, death status.
- "Survived the war" displayed in green when no death date.
- Died: shown with date and location if available.
- Filter pills are above results and clickable to remove.
- Pagination uses large labeled buttons: `<< First` | `← Previous` | `Next →` | `Last >>`. First/Last shortcuts added for large result sets (inspired by old system's navigation pattern).
- Results per page: 20 (not 50 — less scrolling, less overwhelm).
- **Sort control:** Users can sort results by Surname (default), Rank, Date of Death, or Battalion. The current sort order is displayed above results.
- **Clear All button:** Resets all search fields and filters, returning to a blank search state.
- **Print List:** Users can print the current results page (not just individual records).

### 9.3 Record Detail Screen

```text
┌──────────────────────────────────────────────────────────────┐
│  Soldiers Died in the Great War 1914-1919                     │
│  ─────────────────────────────────────────                     │
│  Home > Results (47) > Smith, James                           │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  [← Back to Results]                           [Print]        │
│                                                               │
│  SMITH, James                                                 │
│  ═══════════════════════════════════════                       │
│                                                               │
│  PERSONAL INFORMATION                                         │
│  ────────────────────                                         │
│  Surname:              SMITH                                  │
│  First Name(s):        JAMES                                  │
│  Initials:             J                                      │
│  Birth Town:           EDINBURGH                              │
│                                                               │
│  MILITARY SERVICE                                             │
│  ────────────────                                             │
│  Rank:                 Private                                │
│  Rank Group:           Privates                               │
│  Service Number:       4493                                   │
│  Battalion:            51st Highland Division Cyclist Company  │
│                                                               │
│  CASUALTY INFORMATION                                         │
│  ────────────────────                                         │
│  Date of Death:        15 September 1915                      │
│  Death Location:       France & Flanders                      │
│  Additional Notes:     Killed in action                       │
│                                                               │
│  ─────────────────────────────────────────                     │
│                                                               │
│  Explore Related Records                                      │
│  • 12 others in 51st Highland Division Cyclist Company        │
│  • 87 others who died on 15 September 1915                    │
│  • 234 others born in Edinburgh                               │
│                                                               │
│  [← Back to Results]                           [Print]        │
│                                                               │
│  ─────────────────────────────────────────                     │
│  [← Previous Record]   Record 7 of 1025    [Next Record →]   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**Key behaviors:**

- Clear section grouping with horizontal rules.
- All available fields displayed — no "show more."
- Missing fields simply omitted (not shown as "N/A" or empty).
- Related records are clickable links that open new searches.
- Print button triggers OS print dialog (pywebview supports `window.print()`).
- Back button returns to results, preserving scroll position and page.
- Date of Death rendered in human-readable format (not ISO).
- **Record-by-record navigation (from old system):** `← Previous Record` and `Next Record →` buttons at the bottom of the detail view, with a counter showing "Record 7 of 1025". This allows users to browse through an entire result set one record at a time without returning to the list — a critical workflow for researchers scanning all soldiers in a battalion or with a particular surname. The old system used this pattern extensively (see Appendix F.7).

---

## 10. Fuzzy / Ambiguous Search Implementation

### 10.1 Strategy: Multi-Pass Search

The search system uses progressively wider matching to ensure users always find results:

## Pass 1 — Exact Prefix (fastest)

```sql
SELECT * FROM soldiers WHERE surname LIKE 'MACDONNELL%'
UNION ALL
SELECT * FROM officers WHERE surname LIKE 'MACDONNELL%'
```

## Pass 2 — Soundex / Phonetic (if Pass 1 < threshold)

```python
# Pre-compute Soundex codes in a lookup column (one-time migration)
# surname_soundex TEXT — added to soldiers and officers tables
# Index: idx_soldiers_soundex, idx_officers_soundex

SELECT * FROM soldiers WHERE surname_soundex = soundex('MACDONNELL')
```

Soundex groups phonetically similar names:

- MACDONNELL, MCDONNEL, MACDONELL → same Soundex code
- SMITH, SMYTH, SMYTHE → same Soundex code

## Pass 3 — Contains (if Pass 2 still sparse)

```sql
SELECT * FROM soldiers WHERE surname LIKE '%DONNELL%'
```

## Pass 4 — Cross-field (last resort)

Search battalion names, death locations, birth towns for the query term.

### 10.2 Phonetic Matching: Implementation Options

| Approach | Pros | Cons | Recommendation |
| :--- | :--- | :--- | :--- |
| **Soundex column** | Fast (indexed lookup), simple | English-biased; coarse | ✅ Use as primary phonetic |
| **Metaphone** | Better than Soundex for names | Requires Python library | Use as supplement |
| **Levenshtein (edit distance)** | Catches typos | Slow on 700K rows without pre-filtering | Use only on narrowed sets |
| **SQLite FTS5** | Built-in full-text search | Doesn't do phonetic | Good for multi-word queries |

**Recommended implementation:**

1. Add `surname_soundex` column to `soldiers` and `officers` tables (one-time migration).
2. Index the column.
3. Primary search: exact prefix → Soundex lookup → contains fallback.
4. For multi-word input: use FTS5 virtual table across surname + christian_names.
5. Levenshtein used only on the result set of a phonetic match to rank results.

### 10.3 Schema Additions

```sql
-- Add Soundex column for fuzzy surname matching
ALTER TABLE soldiers ADD COLUMN surname_soundex TEXT;
ALTER TABLE officers ADD COLUMN surname_soundex TEXT;

-- Populate (run once via migration script)
-- Python: sqlite3 doesn't have soundex built-in;
-- compute in Python and UPDATE in batches

-- Index for fast phonetic lookups
CREATE INDEX idx_soldiers_soundex ON soldiers(surname_soundex);
CREATE INDEX idx_officers_soundex ON officers(surname_soundex);

-- Optional: FTS5 virtual table for multi-word search
CREATE VIRTUAL TABLE IF NOT EXISTS personnel_fts USING fts5(
    surname,
    christian_names,
    birth_town,
    death_location,
    battalion_name,
    content='',   -- external content mode
    tokenize='unicode61'
);
```

---

## 11. Accessibility Requirements

### 11.1 Visual

- **Minimum font size:** 20px for body, 16px absolute minimum for any text.
- **Contrast ratio:** WCAG AAA (7:1) for all text. No exceptions.
- **No information conveyed by color alone.** Always pair with text or icon.
- **Focus indicators:** 3px solid blue ring on all interactive elements.
- **No tiny click targets.** Minimum 44×44px for all interactive elements (48px preferred).

### 11.2 Motor / Input

- **Large click targets:** Buttons, cards, and links all have generous padding.
- **No hover-only interactions.** Everything works with click/tap.
- **No drag-and-drop.** Not appropriate for this audience.
- **No double-click.** Single click for everything.
- **Keyboard fully navigable.** Tab order is logical; Enter activates; Escape goes back.
- **No time limits.** No session timeouts, no auto-dismissing notifications.

### 11.3 Cognitive

- **Simple language.** No technical jargon, no abbreviations without explanation.
- **Consistent layout.** Same position for navigation, content, and actions on every page.
- **Visible state.** Active filters shown as pills. Current page shown in breadcrumb.
- **Error recovery.** "No results" always suggests alternatives. Never a blank or confusing screen.
- **Minimal choices.** At most 3 primary actions visible at once.

### 11.4 Screen Reader (Future Enhancement)

- Semantic HTML: `<header>`, `<main>`, `<nav>`, `<article>`, `<h1>`–`<h3>`.
- ARIA labels on all interactive elements.
- Live regions for dynamic result counts.
- Skip-to-content link.

---

## 12. Cross-Platform Build Strategy

### 12.1 Development Environment (macOS)

```text
macOS (Apple Silicon)
├── Python 3.11+ (via Homebrew)
├── Flask + pywebview (pip install)
├── SQLite (built into Python)
├── sd_2011.db (local copy)
└── Run: python3 src/desktop_app.py
    → Opens native macOS window via WebKit
```

All development and testing of UI, search logic, and data queries happens on Mac. The Flask app and templates are identical across platforms.

### 12.2 Windows Build (Target Machine)

```text
Windows 11
├── Python 3.11+ (installed from python.org or portable)
├── PyInstaller (pip install)
├── pywebview[cef] or pywebview (uses Edge WebView2, pre-installed on Win11)
├── Build: pyinstaller --onedir --windowed SDGW
└── Output: dist/SDGW/ folder (~300 MB with database)
```

### 12.3 Deployment Checklist

- [ ] Verify Windows 11 target has Edge WebView2 runtime (pre-installed on all Win11 machines)
- [ ] Build .exe via PyInstaller on Windows machine
- [ ] Test on clean Windows 11 user account (no admin rights)
- [ ] Verify `sd_2011.db` is accessible from bundled location
- [ ] Test all search types (exact, fuzzy, filter combinations)
- [ ] Verify print functionality
- [ ] Verify window resizing and minimum size (1024×768)
- [ ] Copy `dist/SDGW/` folder to USB or network share
- [ ] Create shortcut on target machine desktop pointing to `SDGW.exe`

### 12.4 SmartScreen Warning Mitigation

Since the app is unsigned, Windows SmartScreen will show a warning on first launch. Mitigation:

1. **User education:** Include a `README.txt` in the folder explaining: *"Windows may show a warning because this application is not from the Microsoft Store. Click 'More info' then 'Run anyway' to proceed. This is safe."*
2. **Future option:** If distribution widens, consider purchasing a code signing certificate (~$200/year).

---

## 13. New File: `src/desktop_app.py`

Entry point for the desktop application:

```python
#!/usr/bin/env python3
"""
Desktop application launcher for SDGW 1914-1919.
Wraps the Flask web app in a native window via pywebview.
"""
import threading
import webview
from web_app import app

def start_flask():
    app.run(host='127.0.0.1', port=5000, use_reloader=False)

if __name__ == '__main__':
    # Start Flask in background thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    # Open native window pointing to Flask
    webview.create_window(
        title='Soldiers Died in the Great War 1914-1919',
        url='http://127.0.0.1:5000',
        width=1024,
        height=768,
        min_size=(800, 600),
        resizable=True,
        text_select=True
    )
    webview.start()
```

**Dependencies to add to `requirements.txt`:**

```text
pywebview>=5.0
pyinstaller>=6.0  # build-time only
```

---

## 14. Acceptance Criteria

### AC1: Application Launch

- [ ] Double-clicking `SDGW.exe` opens a native window within 5 seconds
- [ ] Window title is "Soldiers Died in the Great War 1914-1919"
- [ ] Home screen is displayed with search bar focused
- [ ] No terminal/console window visible
- [ ] No internet connection required

### AC2: Senior Usability

- [ ] Body text is 20px minimum
- [ ] All buttons are 44px+ height
- [ ] Color contrast meets WCAG AAA (7:1) — verified with contrast checker
- [ ] A first-time user (age 65+) can find a record within 60 seconds
- [ ] No jargon visible on Home or Results screens
- [ ] "Back" button visible and functional on every screen except Home
- [ ] Breadcrumb trail shows current location

### AC3: Search — Exact

- [ ] Typing "SMITH" and clicking Find returns results in < 1 second
- [ ] Results show name, rank, battalion, death status per card
- [ ] Service number search returns exact match

### AC4: Search — Ambiguous / Fuzzy

- [ ] Typing "MacDonnel" returns MACDONNELL, MCDONNEL, and similar variants
- [ ] Typing "Smyth" returns SMITH, SMYTH, SMYTHE
- [ ] Typing "4493" searches service numbers
- [ ] "No exact match" screen offers "Did you mean?" suggestions
- [ ] Fuzzy search completes in < 1 second

### AC5: Filtering

- [ ] "More Filters" expands to show rank, battalion, location, dates
- [ ] Selecting a filter narrows results and updates count
- [ ] Active filters shown as removable pills
- [ ] Removing a pill broadens results back
- [ ] Cascading filters: selecting a battalion narrows rank dropdown to relevant ranks

### AC6: Record Detail

- [ ] All record fields displayed (no truncation)
- [ ] Fields grouped by category (Personal, Military, Casualty)
- [ ] Related records section shows links to same battalion / death date / birth town
- [ ] Print button opens system print dialog
- [ ] Date of Death shown in human-readable format

### AC7: Cross-Platform

- [ ] Application runs on macOS during development (via `python3 src/desktop_app.py`)
- [ ] Application builds as Windows .exe via PyInstaller on Windows 11 machine
- [ ] Windows build runs without admin rights
- [ ] Windows build runs without internet
- [ ] SmartScreen warning documented with user instructions

### AC8: Performance

- [ ] Application launch to usable Home screen: < 5 seconds
- [ ] Exact search response: < 500ms
- [ ] Fuzzy search response: < 1 second
- [ ] Filter cascade update: < 500ms
- [ ] Page navigation (results): < 300ms

---

## 15. Implementation Phases

### Phase D1: Desktop Shell (1 week)

- [ ] Add `pywebview` dependency
- [ ] Create `src/desktop_app.py` launcher
- [ ] Verify Flask app runs inside native window on macOS
- [ ] Verify window controls (resize, minimize, close)
- [ ] Test print functionality via `window.print()`

### Phase D2: Senior UX Overhaul (2 weeks)

- [ ] Redesign Home screen per Section 9.1 (unified search bar, progressive filters)
- [ ] Redesign Results screen per Section 9.2 (cards, filter pills, pagination)
- [ ] Redesign Detail screen per Section 9.3 (grouped sections, related records)
- [ ] Update CSS for 20px+ fonts, 48px buttons, WCAG AAA colors
- [ ] Add breadcrumb navigation
- [ ] Add keyboard shortcuts (Ctrl+F, Escape, Ctrl+P)
- [ ] Accessibility audit (contrast, focus rings, keyboard nav)

### Phase D3: Fuzzy Search (1 week)

- [ ] Add `surname_soundex` column to soldiers and officers tables
- [ ] Write migration script to populate Soundex codes
- [ ] Implement multi-pass search algorithm (exact → Soundex → contains)
- [ ] Add "Did you mean?" suggestion UI
- [ ] Performance test fuzzy search on full 703K dataset
- [ ] Add FTS5 virtual table for multi-word queries (optional)

### Phase D4: Windows Build & Test (1 week)

- [ ] Install Python + PyInstaller on Windows 11 machine
- [ ] Build SDGW.exe via PyInstaller
- [ ] Test all acceptance criteria on Windows 11
- [ ] Verify no admin rights required
- [ ] Verify database bundling and path resolution
- [ ] Create README.txt for SmartScreen warning
- [ ] Test on fresh Windows user account
- [ ] Package final distribution folder

---

## 16. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
| :--- | :--- | :--- | :--- |
| PyInstaller exe flagged as malware by antivirus | High | Medium | Test with Windows Defender; add exclusion instructions to README; consider code signing later |
| pywebview rendering differences between Mac/Windows | Medium | Low | Use standard HTML/CSS; test early on Windows; avoid platform-specific APIs |
| 257 MB database makes bundle large (~300+ MB) | Low | Certain | Acceptable for USB/network distribution; could compress if needed |
| Soundex too coarse (groups unrelated names) | Medium | Medium | Supplement with Metaphone; show relevance scores; let user refine |
| Older user confused by SmartScreen warning | High | High | Include printed instructions with delivery; walk user through first launch |
| PyInstaller build breaks on Python version mismatch | Medium | Low | Pin Python version (3.11.x) on both Mac and Windows |
| Window resizing breaks layout | Low | Low | CSS responsive design; set minimum window size 800×600 |

---

## 17. Success Metrics

### Quantitative

- **Launch time:** < 5 seconds to usable screen
- **Search speed:** < 1 second for any query type
- **Fuzzy match accuracy:** Top-5 results include correct name ≥ 90% of the time
- **Build size:** < 400 MB total (exe + database)
- **Accessibility:** WCAG AAA on all screens

### Qualitative

- **First-use success:** A 70-year-old can find a record without external help
- **Confidence:** User trusts the results are complete ("I've found everyone named Smith")
- **Satisfaction:** User can print or note the record they were looking for
- **Comfort:** User never feels lost, confused, or stuck

---

## 18. Open Questions

1. **Q:** Should the app support full-screen / maximized mode?
   **A:** Yes — window should be resizable and support maximize. Default to 1024×768.

2. **Q:** Should we bundle a help / user guide inside the app?
   **A:** Yes — an in-app Help page accessible from the header. Keep it to one screen of tips.

3. **Q:** Should results be exportable to CSV?
   **A:** Phase 2 feature. Not in initial release.

4. **Q:** Should the app remember last search on relaunch?
   **A:** No for MVP. Keep it simple — always start fresh at Home.

5. **Q:** Should we support dark mode?
   **A:** No. Light mode with warm off-white (#F5F5F0) background is easier for older eyes. Dark mode can be added later.

---

## 19. Relationship to Prior PRDs

| PRD | Status | Relationship |
| :--- | :--- | :--- |
| **A: Data Access Layer** | ✅ Complete | Foundation — extraction scripts still used for re-exports |
| **B: Data Migration** | ✅ Complete | Foundation — schema.sql and sd_2011.db carry forward unchanged |
| **C: Basic UI** | ✅ Complete (prototype) | **Extended by this PRD.** Flask app, templates, and CSS evolve into desktop shell. Search logic reused. |
| **D: Desktop Application** | 📋 This document | Builds on all prior phases; delivers the end-user product |

---

## 20. Sign-Off

| Role | Name | Date | Status |
| :--- | :--- | :--- | :--- |
| Product Owner | TBD | 16 Feb 2026 | Pending |
| UX / Accessibility | TBD | 16 Feb 2026 | Pending |
| Tech Lead | TBD | 16 Feb 2026 | Pending |

---

---

## Appendix F: Old System UI Analysis

**Source:** 13 screenshots from the "Army Roll of Honour" (1939-1945) desktop application, a sibling WW2 product from Naval & Military Press using the same publisher's database software. Screenshots stored in `old_system/screens/Screenshot-112.png` through `Screenshot-124.png`. The main menu screen that precedes these screens is not available.

This appendix documents UI patterns from the old system and maps them to decisions made in this PRD. The old system was a CD-ROM-based application with a red military-themed interface running on Windows.

### F.1 Old System Search Form (Screenshots 112-119)

The old system presented all search fields on a single form screen:

| Field | Control Type | SDGW Equivalent | Adopted in PRD D? |
| --- | --- | --- | --- |
| Branch of Army | Dropdown (with temporal selector) | Not directly mapped — SDGW doesn't have branch field | N/A |
| Regiment, Corps, etc. | Hierarchical dropdown (2 levels) | `battalion` (721 values) | Yes — searchable dropdown, grouped (Section 7.2) |
| Surname | Free text | `surname` | Yes — unified search bar (Section 7.1) |
| Christian Name(s) | Free text | `christian_names` | **Added** — dedicated filter field (Section 7.2) |
| Initials | Free text | `initials` | Deferred to Phase 2 |
| Number | Free text | `service_number` | Yes — unified search bar handles numeric input |
| Rank | Dropdown with groups | `rank` + `rank_group` | Yes — toggle buttons + searchable dropdown |
| Residence | Popup with geographic hierarchy | `enlistment_loc` (closest match) | Yes — text input with autocomplete |
| Theatre of War | Dropdown | `death_location` (137 values) | **Added** — searchable dropdown (Section 7.2) |
| Died Date(s) | Free text | `death_date` (ISO 8601) | Yes — date range picker |

**Boolean Query Logic:** The old system had NOT/AND/OR radio buttons for combining fields. The new app uses implicit AND for all filters — simpler for the target audience and sufficient for the use cases.

**Clear Page Button:** The old system had a "Clear Page" button to reset all fields. **Adopted** — added "Clear All" to the results screen (Section 9.2).

### F.2 Hierarchical Regiment Selection (Screenshots 113-115)

The old system used a two-level cascade for regiment selection:

**Level 1 — Branch/Corps Type:**
Household Cavalry, Yeomanry, Royal Armoured Corps, Royal Artillery, Royal Corps of Signals, Royal Air Corps, Royal Engineers, Women's Services, Pioneer Corps

**Level 2 — Specific Regiment (within selected branch):**
e.g., 17/21 Lancers RAC, 1st Dragon Guards RAC, Seaforth Highlanders, Sherwood Foresters, Special Air Service Regt, etc.

**Adopted:** The SDGW battalion dropdown (721 values) should be grouped by regiment/corps type where the data allows. The `battalions_sd` table may already contain grouping information. If not, this grouping can be derived from battalion name patterns. At minimum, the type-ahead search within the dropdown (already specified in Section 7.2) mitigates the flat-list problem.

### F.3 Rank Hierarchy (Screenshot 117)

The old system grouped ranks as: Soldier Ranks (all), Military Officers, Warrant Officers, Non-commissioned Officers, then specific ranks within each group (Private, Guardian, Musician, Piper, Trooper, etc.).

**Adopted:** PRD D Section 7.2 already captures this with `rank_group` as toggle buttons (4 values) and `rank` as a searchable dropdown (114 values). No change needed — good alignment with old system.

### F.4 Theatre of War (Screenshot 116)

The old system offered a dropdown for Theatre of War with values including: Ceylon, Continent of America, East Africa (includes Abyssinia), and others.

**Adopted:** SDGW's `death_location` field (137 distinct values) serves the same purpose. Added as a searchable dropdown filter in Section 7.2.

### F.5 Geographic Hierarchy for Birth & Residence (Screenshots 118-119)

Both "Places of Birth" and "Places of Residence" in the old system used a hierarchical selector:

- **Top level:** All locations, England, Scotland, Ireland, Wales
- **County/City level:** e.g., Anglesey, Brecknockshire, Staffordshire, Surrey
- **Overseas:** Not known on Roll, Colonies and Protectorates, Europe, Africa, America, Asia/Oceania, Canada

**Deferred to Phase 2:** SDGW has `birth_town` (85K values) and `enlistment_loc` (25K values) as free text with autocomplete. Adding geographic hierarchy (Country → County grouping) would improve usability but requires data enrichment to classify the 85K birth town values into geographic categories. Noted as a Phase 2 enhancement.

### F.6 Search Results — List View (Screenshot 120)

The old system results screen featured:

- **Query description** at top: "Query option: 'AND', Regiment at death is Royal Scots Fusiliers"
- **Sort order display:** "Sort Order: Surname, Christian Name(s)"
- **Tabular layout** with columns: Surname, Christian Names, Number, Rank
- **Record count and navigation:** `<< First Record` | `< Previous Record` | record X of Y | `Next Record >` | `Last Record >>`
- **View mode buttons:** Sort, Record View, Browse View, Print Results
- **Action buttons:** Search Criteria, New Search, Save Results, Main Menu

**Adopted:**

1. **Table View toggle** — added to Section 9.2. Users can switch between card view (default, senior-friendly) and table view (denser, for power users scanning large sets).
2. **Sort control** — added to Section 9.2. Sort by Surname, Rank, Date of Death, or Battalion.
3. **First/Last navigation** — added to Section 9.2 pagination. `<< First` | `← Previous` | `Next →` | `Last >>`.
4. **Print List** — added to Section 9.2. Print the current results page.
5. **Active query display** — already covered by filter pills in Section 9.2.

**Deferred:** Save Results functionality — Phase 2.

### F.7 Record Detail / Browse View (Screenshots 121-124)

The old system's individual record view displayed fields in a form layout and included **record-by-record navigation within the result set**:

- Counter: "1 of 1025" / "7 of 1025" / "62 of 1025"
- Navigation: `<< First Record` | `< Previous Record` | `Next Record >` | `Last Record >>`
- User could flip through all 1025 results one at a time from the detail view

**Fields displayed:**

- Branch at death (e.g., "Infantry")
- Regiment, Corps etc (e.g., "The Royal Scots Fusiliers")
- Branch at 1/8/39 (initial assignment)
- Regiment, Corps at 1/8/39 (initial regiment)
- Surname, Christian Name(s), Rank, Number, Residence, Theatre of War

**Adopted:**

1. **Record-by-record navigation** — added to Section 9.3 detail view. `← Previous Record` | Record X of Y | `Next Record →`. This is a critical workflow for researchers who want to scan through all soldiers in a battalion or all matches for a surname without repeatedly going back to the results list.
2. **Temporal data display** — where SDGW data includes both initial and final assignments (e.g., regiment at enlistment vs regiment at death), both should be shown in the detail view under the Military Service section.

### F.8 Features Not Carried Forward

| Old System Feature | Reason for Exclusion |
| --- | --- |
| NOT/OR boolean operators | Implicit AND is simpler and sufficient for target audience |
| CD-ROM ordering | Not applicable to new distribution model |
| User Lists | Deferred to Phase 2 — potential "Saved Records" feature |
| Red military-themed visual design | New app uses accessible, high-contrast neutral palette (WCAG AAA) |
| "At 1/8/39" temporal selector on search form | SDGW data structure doesn't have this temporal distinction in the same way |

### F.9 Summary: Changes Made to PRD D from Old System Analysis

| Section | Change | Source Screenshot(s) |
| --- | --- | --- |
| 7.2 Category Filters | Added Christian Name(s) as dedicated filter field | 112 |
| 7.2 Category Filters | Added Death Location (Theatre of War) as filter | 116 |
| 7.2 Category Filters | Added Enlistment Location as filter | 112 (Residence) |
| 7.2 Category Filters | Noted battalion grouping by regiment type | 113-115 |
| 9.2 Results Screen | Added Table View toggle alongside card view | 120 |
| 9.2 Results Screen | Added Sort control (surname, rank, death date, battalion) | 120 |
| 9.2 Results Screen | Added First/Last to pagination navigation | 120 |
| 9.2 Results Screen | Added Clear All / Reset button | 112 |
| 9.2 Results Screen | Added Print List capability | 120 |
| 9.3 Detail Screen | Added record-by-record navigation (Previous/Next within results) | 121-124 |
| 9.3 Detail Screen | Added record position counter ("Record X of Y") | 121-124 |

---

**Document Version:** 1.1
**Last Updated:** 17 February 2026
**Change Log:**

- v1.1 (17 Feb 2026): Added Appendix F — Old System UI Analysis; updated Sections 7.2, 9.2, 9.3 with features identified from Army Roll of Honour screenshots
- v1.0 (16 Feb 2026): Initial document

**Next Review:** Upon completion of Phase D1 (Desktop Shell)
