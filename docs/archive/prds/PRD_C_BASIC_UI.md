# PRD C: Basic UI

## Product Requirements Document – SDGW 1914-1919 Modernization

**Version:** 1.2  
**Date:** 17 February 2026  
**Status:** COMPLETED  
**Audience:** Engineering Team & Stakeholders

---

> ## Completion Summary
>
> **Status:** COMPLETED — All core requirements delivered and verified.
> **Completion Date:** February 2026
>
> ### What Was Delivered
>
> - `src/web_app.py` — Flask application: search form, results page, detail view, autocomplete API, filter-options API, CSV export, annotation/image routes, 404 handler
> - `src/templates/home.html` — Search form with Tom Select dropdowns, surname autocomplete, dynamic filter narrowing, Basic/Advanced search mode toggle
> - `src/templates/search_results.html` — Paginated results with card/table toggle, sort controls, filter pills with removal, print support, CSV export
> - `src/templates/detail.html` — Full record view with related records, record-by-record navigation (First/Prev/Next/Last), copy to clipboard, breadcrumbs
> - `src/templates/settings.html` — User display preferences (theme, density, layout, font size)
> - `src/templates/about.html` — About page
> - `src/templates/annotation_form.html` — Annotation editing form
> - `src/templates/404.html` — Friendly error page
> - `src/static/style.css` — Responsive CSS with WCAG AAA contrast, 18px+ fonts, 44px touch targets, print styles, dark/light/system themes
> - `src/annotations.py` — AnnotationManager for user-contributed supplemental data and images
> - `src/schema_amendments.sql` — Annotation/image database schema (4 tables + 2 views)
> - `tests/test_web_app.py` — 43 tests, all passing
> - `tests/test_ui.py` — 38 UI structure/accessibility tests, all passing
>
> ### Deviations from PRD v1.0
>
> - **12 search fields** (PRD specified fewer): surname, christian names, initials, service number, rank, battalion, birth town, enlistment location, decoration, death location, death date range, record type
> - **20 results per page** (PRD said 10, implementation started at 50, reduced to 20 in Sprint 2)
> - **Tom Select CDN** dependency added for enhanced dropdowns (not in original tech stack)
> - **Card/table view toggle**, **5 sort options**, **removable filter pills**, **breadcrumbs**, **CSV export**, **copy to clipboard** all added beyond original scope
> - **Record-by-record navigation** with First/Prev/Next/Last in detail view
> - **API endpoints** added: `/api/surname-suggest`, `/api/filter-options`, `/api/fuzzy-suggest`, `/api/annotations/stats`
> - **Annotation and image upload system** added (backend complete, UI templates created)
> - **Settings page** with theme, density, layout, font size preferences
> - **Basic/Advanced search mode** toggle with cascading filter control
> - **Reference data tables** added: regiment names, theatre groups, region places, place keywords (`src/reference_data.sql`)
>
> ### Links to Implementation
>
> - `src/web_app.py` — Core application
> - `src/annotations.py` — Annotation system
> - `src/templates/` — All 7 HTML templates
> - `src/static/style.css` — Styling
> - `src/schema_amendments.sql`, `src/reference_data.sql` — Extended schema
> - `tests/test_web_app.py`, `tests/test_ui.py` — Test suites
> **v1.2 Changelog (17 Feb 2026):** Updated to match actual implementation. Key changes: 12 search fields (was 2), 50 results per page (was 10), Tom Select CDN dependency added, card/table view toggle, 5 sort options, filter pills, record-by-record navigation, breadcrumb navigation, CSV export, human-readable death dates, API endpoints documented, test suites documented. See ENH-12 in `11_PRD_E_ENHANCEMENTS.md`.

---

## 1. Document Purpose

This PRD defines the initial user interface for searching and viewing historical military records (1914-1919). The UI is intentionally minimal and designed for accessibility, particularly for older adults (65+) researching family history.

**Design Philosophy:** "Get out of the way. Let the data shine."

---

## 2. Business Context

### Problem

- ~703,806 historical records exist in database
- End users: researchers, historians, family members (many 60-80 years old)
- Current access: None (data locked in Access)
- Need: Simple way to find and view individual records

### Goals

- **Accessibility:** Large text, high contrast, minimal cognitive load
- **Discoverability:** Simple search without complex query syntax
- **Trust:** Show complete record information; no hidden data
- **Efficiency:** Find a record in 2-3 clicks
- **Forgiving:** Never punish user errors; offer suggestions

### Constraints

- **No signup/login:** Anyone can access public data
- **No advanced features yet:** Keep MVP simple; iterate later
- **Self-contained:** Flask app + SQLite database; no external services required
- **Performance:** Instant results (< 1 second)

---

## 3. Scope: What We're Building

### In Scope ✅

- Home page with large, clear interface
- Simple keyword search (by name, service number)
- List view of search results
- Detail view for individual records
- Basic filtering by battalion/rank
- "Back" navigation (no getting lost)
- Print-friendly record display

### Out of Scope 🚫

- Advanced query builder
- Map view of locations
- Photo attachments or documents
- Relationship mapping (e.g., "who served with")
- Mobile app (web only for now)
- Admin interface for data management

---

## 4. Design Principles

### P1: Large Text & High Contrast

- **Body Text:** 18px minimum (not 12px)
- **Headings:** 32px minimum
- **Buttons:** 44px height minimum (touch-friendly)
- **Color Contrast:** WCAG AAA standard (7:1 contrast ratio)

### P2: Minimize Jargon

Replace military/technical terms with explanations:

- ❌ "REG_ID" → ✅ "Regiment Assignment"
- ❌ "TOW_ID" → ✅ "Town (ID)"
- ❌ "DEATH_DATE" → ✅ "Date of Death"
- ❌ "DC_ID" → ✅ "Status Code"

### P3: Consistent Layout

- Same navigation on every page
- Same visual hierarchy throughout
- Predictable button placement (back always top-left)
- Consistent spacing and alignment

### P4: Forgiving Interactions

- No accidental deletions or irreversible actions
- Offer "Did you mean?" suggestions
- Allow common misspellings (e.g., "Smithe" → "Smith")
- Show examples of what to search for

### P5: Complete Information

- Show all fields for a record
- No "See more" truncation
- Group related fields together
- Explain what each field means

---

## 5. Information Architecture

```text
Home Page (Entry Point)
├── Search for a person (surname + optional service number)
├── Browse by battalion (if known)
├── Instructions: "How to find my ancestor"
└── Sponsors/credits

Search Results
├── List of matching records (surname, rank, battalion, death status)
├── Click to view full record
└── Back to search

Detail View
├── Full person record (all fields)
├── Links to related records (same battalion, rank, etc.)
├── Print option
└── Back to search
```

---

## 6. User Workflows

### Workflow 1: Search by Surname (Most Common)

**User Goal:** Find a soldier/officer named "Smith"

**Steps:**

1. Open home page → sees large search box
2. Type "SMITH" (system accepts uppercase or lowercase)
3. Click "Search" (or press Enter)
4. System shows list: "14 people named SMITH found"
5. User clicks on one result: "SMITH, James (Corporal, 51st Battalion)"
6. Full record page opens
7. User clicks "Back" to search again or "Print" to save page

**Time to First Result:** 5 seconds  
**Cognitive Load:** Minimal (one action at a time)

---

### Workflow 2: Search by Service Number

**User Goal:** Find record via military service number

**Steps:**

1. Open home page
2. Enter service number (e.g., "123456") in optional field
3. Click "Search"
4. System shows exact match (if found)
5. Display record

**Time to First Result:** 3 seconds

---

### Workflow 3: Browse by Battalion

**User Goal:** "My grandfather was in the 51st Battalion; find all soldiers"

**Steps:**

1. Open home page
2. Scroll down to "Browse by Battalion"
3. Select "51st Battalion" from dropdown list
4. System shows ~200 person records from that battalion
5. User can scan list or click individual names
6. Each name links to full record

**Time to First Result:** 4 seconds

---

### Workflow 4: Interpret Casualty Status

**User Goal:** "Was my ancestor killed in the war?"

**Steps:**

1. Find record (via search workflow)
2. Look for "Date of Death" field
3. If filled: person was killed/died → show date and location
4. If blank: person survived war
5. Print record for family records

**Clarity Goal:** Should be obvious from record display; no ambiguity

---

## 7. UI Components

### 7.1 Home Page

**Layout:**

```text
┌─────────────────────────────────────────────────────┐
│  SDGW 1914-1919 Personnel Discovery                 │
│  Finding your ancestor in historical records        │
└─────────────────────────────────────────────────────┘

┌─ SEARCH FOR A PERSON ─────────────────────────────┐
│                                                    │
│  Surname:        ┌──────────────────────────────┐ │
│                  │ SMITH                        │ │
│                  └──────────────────────────────┘ │
│                                                    │
│  Service Number: ┌──────────────────────────────┐ │
│  (optional)      │ (leave blank if unknown)     │ │
│                  └──────────────────────────────┘ │
│                                                    │
│     ┌─────────────────────────┐                  │
│     │      SEARCH             │                  │
│     └─────────────────────────┘                  │
│                                                    │
│  💡 Tip: Search is not case-sensitive             │
│     Try searching for a surname you know          │
│                                                    │
└────────────────────────────────────────────────────┘

┌─ OR BROWSE BY BATTALION ──────────────────────────┐
│                                                    │
│  Select a Battalion:  ┌──────────────────────┐   │
│                       │ Choose battalion...  │▼  │
│                       └──────────────────────┘   │
│                                                    │
│       ┌─────────────┐                             │
│       │   BROWSE    │                             │
│       └─────────────┘                             │
│                                                    │
└────────────────────────────────────────────────────┘

┌─ HELP ────────────────────────────────────────────┐
│                                                    │
│  How to use this site:                             │
│  • Enter a surname or service number to search     │
│  • Results show every match in the database        │
│  • Click a name to see the full record             │
│  • Print the page to save information              │
│                                                    │
│  About this data:                                  │
│  These records contain 661,960 soldiers and        │
│  soldiers who served 1914-1919. Records include   │
│  birth location, enlistment details, rank, and    │
│  date of death (if applicable).                    │
│                                                    │
│  Not finding your ancestor?                        │
│  • Try alternate spellings (SMITH vs SMYTHE)      │
│  • Check if name is listed as "SMITH, John" not   │
│    "JOHN SMITH"                                    │
│  • Some records may have incomplete information   │
│                                                    │
└────────────────────────────────────────────────────┘

┌─ FOOTER ──────────────────────────────────────────┐
│  Privacy • Contact •Β Home          Page 1 of 1   │
└────────────────────────────────────────────────────┘
```

**Font Sizes:**

- Title: 36px
- Subtitle: 20px
- Labels: 18px
- Input fields: 18px
- Button text: 22px
- Help text: 16px
- Link: 16px

**Colors:**

- Background: White (#FFFFFF)
- Text: Dark gray (#222222)
- Headings: Dark blue (#003366)
- Buttons: Bright green (#006B3F)
- Links: Underlined blue (#0066CC)
- Help boxes: Light gray background (#F0F0F0)

---

### 7.2 Search Results Page

**Layout:**

```text
┌─────────────────────────────────────────────────────┐
│ ◄ BACK           Results: 14 people named "SMITH" │
└─────────────────────────────────────────────────────┘

Search again? ┌──────────────────────┐  ┌────────┐
              │ SMITH                │  │ SEARCH │
              └──────────────────────┘  └────────┘

┌─ RESULTS (Sorted by rank, then first name) ────────┐
│                                                     │
│ 1. SMITH, James             Captain  51st Battalion│
│    Died 15 September 1915                          │
│    ┌──────────────────────────────┐               │
│    │  VIEW FULL RECORD            │               │
│    └──────────────────────────────┘               │
│                                                     │
│ 2. SMITH, William             Private  51st Battalion
│    No death record (survived war)                   │
│    ┌──────────────────────────────┐               │
│    │  VIEW FULL RECORD            │               │
│    └──────────────────────────────┘               │
│                                                     │
│ 3. SMITH, Robert            Sergeant  23rd Battalion
│    Died 3 April 1917                               │
│    ┌──────────────────────────────┐               │
│    │  VIEW FULL RECORD            │               │
│    └──────────────────────────────┘               │
│                                                     │
│  [showing results 1-3 of 14]                       │
│  ┌──────┐         ┌──────┐         ┌──────┐       │
│  │ <<   │         │ 1 2 3│         │   >> │       │
│  └──────┘         └──────┘         └──────┘       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Features:**

- Results sorted by name A-Z by default (5 sort options: Name A-Z/Z-A, Death Date earliest/latest, Rank)
- Each result shows: name, type, rank, battalion, death date (human-readable), death location
- One-click access to full record with position tracking (pos= parameter)
- Pagination at 50 results per page with First/Previous/Next/Last navigation
- Card view (default) and Table view toggle (saved in sessionStorage)
- Filter pills showing active search criteria
- Breadcrumb navigation: Home > Results (count)
- CSV export button (max 10,000 rows)
- Print list button (prints table view)
- Easy "back" to modify search

> **v1.2 Note:** PRD v1.0 specified 10 results per page. Actual implementation uses 50 per page — better for researchers scanning large result sets. Sort control and card/table toggle were added based on old system analysis (Appendix E).

**Typography:**

- Result cards: 20px name, 18px details
- Pagination: 16px

---

### 7.3 Detail View (Full Record)

**Layout:**

```text
┌─────────────────────────────────────────────────────┐
│ ◄ BACK                      Print  │  Save as PDF   │
└─────────────────────────────────────────────────────┘

┌─ OFFICER RECORD ──────────────────────────────────┐
│                                                    │
│  Name: SMITH, James                               │
│  Christian Names: James William                   │
│  Service Number: —                                │
│  Initials: J.W.                                   │
│                                                    │
│  MILITARY SERVICE                                 │
│  Rank: Captain                                    │
│  Battalion: 51st Battalion, Scottish Division     │
│  Decorations: MC (Military Cross)                 │
│  Rank Group: Commissioned Officer                │
│                                                    │
│  PERSONAL INFORMATION                             │
│  Birth Town: Edinburgh                            │
│  Enlistment Location: London                      │
│                                                    │
│  CASUALTY INFORMATION                             │
│  Death Date: 15 September 1915                    │
│  Death Location: Gallipoli, Turkey                │
│  Additional Notes: Killed in action               │
│                                                    │
│  RECORD METADATA                                  │
│  Record ID: 1                                     │
│  Last Updated: 16 February 2026                   │
│                                                    │
└─────────────────────────────────────────────────────┘

┌─ EXPLORE RELATED RECORDS ────────────────────────┐
│                                                   │
│  Other officers from 51st Battalion:             │
│  • JONES, Thomas (Lieutenant)                    │
│  • WILLIAMS, Henry (Major)                       │
│  • HARRIS, Charles (Captain)                     │
│  [... showing 3 of 45 officers]                  │
│                                                   │
│  Other soldiers killed on 15 September 1915:    │
│  • BROWN, John (Private)                         │
│  • TAYLOR, George (Corporal)                     │
│  [... showing 2 of 87 casualties]                │
│                                                   │
│  Soldiers from Edinburgh (birthplace):           │
│  • CLARK, Frank (Private)                        │
│  • SCOTT, Robert (Private)                       │
│  [... showing 2 of 234 from Edinburgh]           │
│                                                   │
└────────────────────────────────────────────────────┘

┌─ FOOTER ──────────────────────────────────────────┐
│  Privacy • Contact • Home            Back to top  │
└────────────────────────────────────────────────────┘
```

**Field Grouping Strategy:**

- **Personal Info:** Name, initials, birth info
- **Military Service:** Rank, battalion, assignment
- **Casualty Status:** Death date, location, notes
- **Record Info:** ID, data quality notes

**Related Records Section:**

- Shows links to similar soldiers (same battalion, same death date, same birthplace)
- Helps users: "Any of these might be my uncle"
- Limited to 3-5 suggestions per category (not overwhelming)

---

## 8. Search Functionality

### Search Algorithm: Surname

```text
User Input: "smith"
1. Normalize input: uppercase, trim whitespace → "SMITH"
2. Exact match search: surname = "SMITH"
   → Returns 14 results
3. Sort by: rank (descending), then first name (ascending)
4. Display results
```

**Acceptance Criteria:**

- [ ] Case-insensitive (SMITH = smith = Smith)
- [ ] Whitespace trimmed
- [ ] Results sorted logically
- [ ] Shows count: "14 people named SMITH"

---

### Search Algorithm: Service Number

```text
User Input: "123456"
1. Normalize: trim whitespace
2. Exact match: service_number = "123456"
3. If match found: go directly to detail view
4. If no match: show "Not found. Try searching by name."
```

**Acceptance Criteria:**

- [ ] Numeric service numbers supported
- [ ] Alphanumeric service numbers supported
- [ ] Exact match (no partial matches)
- [ ] Clear message if not found

---

### Search Algorithm: Partial Name

```text
User Input: "smi" (user is unsure of complete surname)
1. Normalize: uppercase → "SMI"
2. Partial match: surname LIKE "SMI%"
   → Could return: SMITH, SMYTHE, SMILEY, etc.
3. Show first 10 results; offer pagination
4. Message: "Tap a name to see full record"
```

**Future Enhancement (Phase 2):**

- Fuzzy matching: "SMYTHE" matches "SMITH"
- Phonetic matching: "DAVIS" matches "DAVIES"

---

## 9. Filtering & Browsing

### Filter 1: Browse by Battalion

```text
User selects: "51st Battalion"
↓
System shows: All 200 officers and soldiers from 51st Battalion
(Officers first, sorted by rank; then soldiers, sorted by surname)
↓
User sees:
- Officers: Captain SMITH James, Lieutenant JONES Thomas, ...
- Soldiers: Private BROWN John, Private CLARK Frank, ...
```

**Data Source:** Battalion query from database (see PRD B)  
**Performance:** < 500ms response time

---

### Filter 2: Browse by Rank

```text
User selects: "Private"
↓
System shows: All 12,000 soldiers with rank = Private
(Sorted by surname)
↓
User sees paginated results: "Private BAKER Robert", "Private BROWN John", ...
```

**Performance:** < 1 second for paginated display

---

## 10. Accessibility & Usability

### A. Visual Accessibility

- **Font:** Sans-serif (Arial, Helvetica, or system default)
- **Line Height:** 1.6x font size (more readable for older eyes)
- **Focus Indicators:** Clear outline (2px) around interactive elements
- **Color Not Only Indicator:** Use text + color (not just red/green)

### B. Keyboard Navigation

- Tab moves between elements
- Enter activates buttons
- Esc returns to home page from any view
- No keyboard traps

### C. Screen Reader Support

- All images have alt text (e.g., "Rank badge: Captain")
- Button labels clear and descriptive
- Form fields labeled
- Page structure uses semantic HTML (`<h1>`, `<p>`, `<button>`)

### D. Mobile Responsiveness

- Works on tablets (iPad, Android tablets)
- Touch targets 44px minimum
- Landscape and portrait orientations
- Text scales appropriately

### E. Internationalization (Future)

- Strings can be translated
- No hardcoded English in code

---

## 11. Technical Stack

| Component | Technology | Rationale |
| ----------- | ----------- | ----------- |
| **Frontend** | HTML5 + CSS3 | Semantic, accessible, no JavaScript required for core function |
| **Styling** | CSS Grid + Flexbox | Modern, responsive layout; WCAG AAA (7:1 contrast) |
| **Dropdowns** | Tom Select (CDN) | Searchable dropdowns for 721 battalions, 114 ranks, 137 death locations |
| **Interactivity** | Vanilla JavaScript (minimal) | View toggle, sort, autocomplete — progressive enhancement |
| **Backend** | Python Flask 3.0+ | Server-side search + Jinja2 template rendering |
| **Database** | SQLite (sd_2011.db) | 257 MB, 27 indexes, < 100ms queries |
| **Testing** | pytest + BeautifulSoup4 | 81 tests (43 route + 38 UI structure) |
| **Deployment** | `python3 src/web_app.py` | Runs at `http://127.0.0.1:5000`; no container needed for dev |

> **v1.2 Note:** Tom Select loaded via CDN for searchable dropdowns with type-ahead filtering. `beautifulsoup4` added to `requirements.txt` for HTML-parsing UI tests.

---

## 12. User Workflows & Scenarios

### Scenario 1: 75-year-old researching family history

- Opens app
- Searches for "WILSON"
- Gets 23 results
- Clicks on "WILSON, Robert (Private)"
- Sees full record: birth in 1895, died 1916
- Prints page
- Satisfaction: Found information; saved to paper for scrapbook

### Scenario 2: Historian doing batch analysis

- Browses "51st Battalion" group
- Sees all 200 soldiers
- Can script queries (Phase 2 feature) to export names
- Uses CSV for further analysis in Excel

### Scenario 3: User doesn't find expected result

- Searches for "SMITH"
- Gets 14 results but expected "SMITH, John" is not here
- Sees help text: "Try alternative spellings: SMYTHE, SMYTH"
- Re-searches for "SMYTHE"
- Finds person
- Satisfied:got hint that helped

---

## 13. MVP Features (Phase 1)

### Features Included ✅

- [x] Home page with 12-field search form (surname, first name, service number, rank, battalion, birth town, enlistment location, decoration, death location, death date range, record type)
- [x] Surname autocomplete via `surname_lookup` table (50,323 surnames)
- [x] Dynamic filter narrowing (dropdowns update based on active filters)
- [x] Search by surname (prefix match)
- [x] Search by service number (exact match, soldiers only)
- [x] Paginated results (50 per page, First/Previous/Next/Last)
- [x] 5 sort options (Name A-Z/Z-A, Death Date earliest/latest, Rank)
- [x] Card and Table view toggle (saved in sessionStorage)
- [x] Filter pills showing active search criteria
- [x] Detail view with grouped sections (Personal, Military, Casualty, Record)
- [x] Human-readable death dates ("5 September 1915" on detail, "5 Sep 1915" in results)
- [x] Record-by-record Previous/Next navigation within search results
- [x] Related records (same battalion, same death date, same birthplace)
- [x] Breadcrumb navigation (Home > Results > Record Name)
- [x] CSV export (max 10,000 rows, UTF-8 BOM for Excel)
- [x] Print support (individual records and results list)
- [x] Back navigation (preserves search context and page)
- [x] WCAG AAA accessibility (skip-to-main, ARIA landmarks, 7:1 contrast, keyboard navigable)
- [x] Responsive design (tablet-friendly)
- [x] Friendly 404 error page
- [x] Help/instructions section on home page

### Features for Phase 2 (Later) 🚫

- [ ] Fuzzy/phonetic name matching (see PRD D Phase D3)
- [ ] Advanced query builder
- [ ] Map view of locations
- [ ] Timeline view of casualties
- [ ] Saved record lists / bookmarks (see ENH-06)
- [ ] Copy record to clipboard (see ENH-05)
- [ ] Hierarchical regiment/battalion grouping
- [ ] Geographic hierarchy for birth/residence
- [ ] User accounts / saved searches

### API Endpoints (v1.2 — new section)

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/` | GET | Home page with search form |
| `/search` | GET | Search results (accepts all 12 filter params + sort + page) |
| `/record/<type>/<id>` | GET | Detail view for officer or soldier |
| `/export-csv` | GET | CSV download of current search results (max 10,000 rows) |
| `/api/surname-suggest` | GET | Surname autocomplete (prefix match, LIMIT 50) |
| `/api/filter-options` | GET | Dynamic dropdown options based on current filters |

---

## 14. Acceptance Criteria

### AC1: Home Page

- [ ] Home page loads in < 2 seconds
- [ ] Search box has placeholder text: "Surname (e.g., SMITH)"
- [ ] Service number field is marked optional
- [ ] Buttons are at least 44px tall and high-contrast
- [ ] Help section is visible without scrolling (on desktop)

### AC2: Search Results

- [x] Results displayed within 1 second
- [x] Each result shows: surname, type, rank, battalion, death date (human-readable), death location
- [x] "New Search" button returns to home page
- [x] Pagination works at 50 results per page with First/Previous/Next/Last
- [x] Message shows count: "X records found"
- [x] 5 sort options available
- [x] Card/table view toggle
- [x] Filter pills for active search criteria
- [x] Breadcrumb navigation: Home > Results (count)
- [x] CSV export button
- [x] Search params preserved in all pagination links

### AC3: Detail View

- [x] All fields from database are visible (no truncation)
- [x] Fields are grouped logically (Personal, Military, Casualty, Record)
- [x] Related records suggested (same battalion, same death date, same birthplace)
- [x] Print button opens print preview
- [x] "Back to Results" button returns to results (preserving search context and page)
- [x] Death date displayed as "5 September 1915" (human-readable)
- [x] Record-by-record Previous/Next navigation within search results
- [x] Breadcrumb: Home > Results (count) > Record Name

### AC4: Accessibility

- [ ] Page passes WAVE accessibility audit (0 errors, 0 contrast errors)
- [ ] Keyboard tab order is logical
- [ ] Focus indicators visible (2px outline)
- [ ] Works with screen reader (tested with NVDA)
- [ ] Mobile viewport test: readable on iPad portrait

### AC5: Usability

- [ ] User can find a record in < 1 minute (first time user)
- [ ] Error messages are clear and actionable
- [ ] No "404 Not Found" pages; instead get "No results" with suggestions
- [ ] Help text explains where to find ancestor info

---

## 15. Success Metrics

### Quantitative

- **Page Load Time:** < 2 seconds
- **Search Response:** < 1 second
- **Detail Page Load:** < 500 ms
- **Accessibility Score:** 95+ (Lighthouse)
- **Mobile Responsiveness:** 100% (Lighthouse)

### Qualitative

- **Ease of Use:** 80%+ of first-time users find a record without help
- **Clarity:** 90%+ of users say record information is "clear"
- **Satisfaction:** Users feel confident data is accurate

---

## 16. Rollout & Iteration Plan

### Phase 1: MVP Launch (Week 4)

- [ ] Core search + detail functions working
- [ ] Tested on macOS, Windows, iPad
- [ ] Accessibility audit passed
- [ ] Documentation complete
- [ ] Stakeholder sign-off

### Phase 2: Usability Feedback (Week 5-6)

- [ ] Gather user feedback from 5-10 testers
- [ ] Iterate design based on feedback
- [ ] Performance optimizations
- [ ] Add features based on requests (fuzzy matching, export)

### Phase 3: Production (Week 7)

- [ ] Final testing
- [ ] Deploy to production server
- [ ] Monitor performance
- [ ] Plan Phase 2 features

---

## 17. Open Questions

1. **Q:** Should each record show the original MDB data (IDs) or only user-friendly names?  
   **A:** User-friendly names only; hide technical IDs behind "Show technical details" link.

2. **Q:** What happens if a surname has 10,000+ results?  
   **A:** Paginate; show 20 per page; offer "refine search"option.

3. **Q:** Should there be a "random record" feature for browsing?  
   **A:** No for MVP; can add in Phase 2 as "featured ancestor of the week".

4. **Q:** Mobile app vs web?  
   **A:** Web only for MVP (works on tablets); iOS/Android app in Phase 3.

---

## 18. Appendices

### A. Sample Record (OFFICER)

```text
Name: ADAMSON, W C
Initials: W C
Rank: Captain (TP)
Battalion: 1st Battalion
Decoration: (none recorded)
Death Date: 05/09/15 (September 5, 1915)
Death Location: France
Additional Notes: Killed in action
```

### B. Sample Record (SOLDIER)

```text
Name: BROWN, John
Service Number: 123456
Initials: J
Rank: Private
Battalion: 51st Battalion
Birth Town: Birmingham
Enlistment Location: London
Death Date: 15/05/16 (May 15, 1916)
Death Location: Somme
Additional Notes: Killed in battle
```

### C. Color Palette

```text
Primary Colors:
- White:       #FFFFFF
- Dark Gray:   #222222
- Dark Blue:   #003366
- Dark Green:#006B3F

Accent Colors:
- Light Gray:  #F0F0F0
- Link Blue:   #0066CC
- Warning Red: #CC0000 (for errors, used sparingly)

Contrast Ratios (All meet WCAG AAA):
- Dark Gray on White:   17.4:1 ✓
- Dark Blue on White:    8.6:1 ✓
- Dark Green on White:   7.2:1 ✓
- Dark Gray on Lt Gray:  5.2:1 ✓ (used for help text only)
```

### D. Typography

```text
Font Family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial
Line Height: 1.6x font size
Letter Spacing: +0.5px for headings

Font Sizes:
- h1 (Title):      36px bold
- h2 (Subtitle):   20px bold
- h3 (Section):    24px bold
- p (Body):        18px regular
- label (Input):   18px regular
- button (CTA):    22px bold, 44px height
- small (Help):    16px regular
```

---

## 19. Sign-Off

| Role | Name | Date | Status |
| ------ | ------ | ------ | -------- |
| Product Owner | TBD | 16 Feb 2026 | Pending |
| UX/Design Lead | TBD | 16 Feb 2026 | Pending |
| Accessibility Reviewer | TBD | 16 Feb 2026 | Pending |
| Tech Lead | TBD | 16 Feb 2026 | Pending |

---

---

## 20. Appendix E: Old System UI Analysis

**Source:** 13 screenshots from the "Army Roll of Honour" (1939-1945) desktop application, a sibling product from Naval & Military Press. Screenshots stored in `old_system/screens/Screenshot-112.png` through `Screenshot-124.png`. The menu screen that precedes these screens is not available.

This appendix documents UI patterns from the old system that should inform the new SDGW 1914-1919 application. The old system was a CD-ROM-based Access application with a red military-themed interface.

### E.1 Old System Search Form (Screenshots 112-119)

The old system's main search screen has the following features:

**Search Fields (all visible on one screen):**

| Field | Control Type | Notes |
| --- | --- | --- |
| Branch of Army | Dropdown | With "At 1/8/39" and "At Death" temporal selectors |
| Regiment, Corps, etc. | Hierarchical dropdown | Two levels: branch type → specific regiment (see E.2) |
| Surname | Free text | Primary search field |
| Christian Name(s) | Free text | Separate from surname |
| Initials | Free text | Short field |
| Number | Free text | Service/regimental number |
| Rank | Dropdown with groups | Rank groups then specific ranks (see E.3) |
| Residence | Popup with geographic hierarchy | Country → County/City (see E.5) |
| Theatre of War | Dropdown | Campaign/geographic areas |
| Died Date(s) | Free text | Date of death |

**Boolean Query Logic:** Radio buttons for NOT, AND, OR. Default is AND. This allowed combining search fields with different logical operators.

**Action Buttons:** Search, Main Menu, User Lists, Help, Order your CD-ROM, Clear Page.

**Gap Identified for New App:**

- PRD C's home page only has Surname and Service Number fields. The old system exposed many more search fields upfront. The new app should adopt progressive disclosure (PRD D approach) but ensure Christian Names, Initials, Theatre of War, and Residence are available as filter fields — not just surname and service number.
- A **"Clear All" / Reset** button should be added to the search form to reset all fields and filters.

### E.2 Hierarchical Regiment Selection (Screenshots 113-115)

The old system used a **two-level cascading dropdown** for regiment selection:

**Level 1 — Branch/Corps Type (Screenshot 113):**

- Household Cavalry
- Yeomanry
- Royal Armoured Corps
- Royal Artillery
- Royal Corps of Signals
- Royal Air Corps
- Royal Engineers
- Women's Services
- Pioneer Corps

**Level 2 — Specific Regiment (Screenshots 114-115):**
After selecting a branch type, the user saw specific regiments within that grouping, e.g.:

- 17/21 Lancers RAC
- 1st Dragon Guards RAC
- 2nd The Royal Dragoons RAC
- Seaforth Highlanders
- Sherwood Foresters
- Small Arms School Corps
- South Lancashire Regt
- Special Air Service Regt
- (721 total in SDGW data)

**Gap Identified for New App:**

- PRD C has a flat "Browse by Battalion" dropdown. With 721 battalion values, a flat list is unwieldy. The new app should group battalions by regiment/corps type (similar to the old system's hierarchical approach) or at minimum provide type-ahead search within the dropdown.

### E.3 Rank Hierarchy (Screenshot 117)

The old system grouped ranks into categories before showing specific ranks:

**Rank Groups:**

- Soldier Ranks (all)
- Military Officer(s)
- Warrant Officer(s)
- Non-commissioned Officer(s)

**Specific Ranks (within Private/Soldiers):**

- Private (Soldiers), Number, Guardian, Musician, Officer, Piper, Trooper

**Alignment with New App:** PRD D already captures this well with rank_group as toggle buttons (4 values) and rank as a searchable dropdown (114 values). No change needed.

### E.4 Theatre of War (Screenshot 116)

The old system offered a dropdown for Theatre of War with values such as:

- Ceylon
- Continent of America
- East Africa (includes Abyssinia)
- (and others not fully visible)

**Gap Identified for New App:**

- Neither PRD C nor PRD D explicitly includes "Theatre of War" as a filter option, despite the SDGW database having a `death_location` field with 137 distinct values. This should be added to the filter set.

### E.5 Geographic Hierarchy for Birth & Residence (Screenshots 118-119)

Both "Places of Birth" and "Places of Residence" used the same geographic hierarchy pattern:

**Top Level:**

- All locations
- England, Scotland, Ireland, Wales

**County/City Level (within each country):**

- e.g., Anglesey Isle of, Brecknockshire, Caernarvonshire, Southampton, Southport, Staffordshire, Suffolk, Surrey, Sussex

**Overseas Categories:**

- Not known on Roll
- Colonies and Protectorates
- Europe
- Africa
- America
- Asia/Oceania
- Canada

**Gap Identified for New App:**

- PRD C does not include birth town or residence as searchable fields. PRD D includes Birth Town as text input with autocomplete (85K unique values). The old system's geographic grouping (Country → County) would significantly improve usability for these fields. Consider adding a two-level location selector alongside the free text autocomplete.

### E.6 Search Results — List View (Screenshot 120)

The old system results screen had:

**Display:**

- Query description at top: "Query option: 'AND', Regiment at death is Royal Scots Fusiliers"
- Sort order display: "Sort Order: Surname, Christian Name(s)"
- Tabular layout with columns: Surname, Christian Names, Number, Rank
- Record count: "1 of 1025"

**Navigation:**

- `<< First Record` | `< Previous Record` | `Next Record >` | `Last Record >>`

**Action Buttons (left side):**

- Sort — change sort order
- Record View — switch to individual record form view
- Browse View — alternative browsing mode
- Print Results — print the list

**Action Buttons (right side):**

- Search Criteria — view/modify current search
- New Search — start fresh
- Save Results — save current result set
- Main Menu — return to main menu

**Gaps Identified for New App:**

1. **Table View Option:** PRD C/D only describe card-based results. The old system's table view is more information-dense and better for scanning large result sets. The new app should offer a **toggle between card view and table view** for results.
2. **Sort Control:** Old system had explicit sort options. New app should allow sorting by surname, rank, date of death, etc.
3. **First/Last Record Navigation:** PRD C/D have Previous/Next pagination but not First/Last shortcuts. Add these for large result sets.
4. **Search Criteria Display:** The old system showed the active query at the top of results. PRD D has filter pills, which serves the same purpose. Ensure the full query description is visible.
5. **Save Results:** Old system could save result sets. Defer to Phase 2 but note as a feature users may expect.
6. **Print List:** Old system could print the results list, not just individual records. Add this capability.

### E.7 Record Detail / Browse View (Screenshots 121-124)

The old system's individual record view showed:

**Fields displayed (in form layout):**

- Branch at death (e.g., "Infantry")
- Regiment, Corps etc (e.g., "The Royal Scots Fusiliers")
- Branch at 1/8/39 (initial branch assignment)
- Regiment, Corps at 1/8/39 (initial regiment assignment)
- Surname
- Christian Name(s)
- Rank
- Number (service number)
- Residence
- Theatre of War

**Critical Feature — Record-by-Record Navigation:**
The old system allowed browsing through results **one record at a time** from the detail view:

- "1 of 1025" with Previous Record / Next Record buttons
- User could flip through records without returning to the list view
- This is a **significant usability feature** for researchers scanning through results

**Gap Identified for New App:**

- PRD C and D require the user to go back to the results list to select the next record. The old system's in-record navigation (Previous/Next within results) should be adopted. This is especially valuable for researchers examining all soldiers in a battalion or with a particular surname. Add `← Previous Record` and `Next Record →` buttons to the detail view, with a counter showing "Record X of Y."

### E.8 Summary of Recommended Changes from Old System Analysis

**Must-Have (carry into MVP):**

1. **Christian Name(s) as a dedicated search/filter field** — not just embedded in unified search
2. **Record-by-record navigation in detail view** — Previous/Next within result set
3. **Clear All / Reset button** on search form
4. **Theatre of War / Death Location as a filter** option
5. **Table view option** for search results (toggle between cards and table)
6. **Sort control** on search results (by name, rank, date)
7. **First/Last navigation** in pagination
8. **Print list** capability (not just individual records)

**Should-Have (Phase 2):**

1. **Hierarchical regiment/battalion grouping** — group 721 battalions by regiment type
2. **Geographic hierarchy for birth/residence** — Country → County selector
3. **Save Results** functionality
4. **Initials as a searchable field**
5. **User Lists** — saved lists of records of interest

---

**Document Version:** 1.2
**Last Updated:** 17 February 2026
**Change Log:**

- v1.2 (17 Feb 2026): Aligned with actual implementation (ENH-12). Updated tech stack, search fields (12), results per page (50), added sort/toggle/pills/breadcrumbs/CSV export/human dates/API endpoints/test suites to feature list. Updated acceptance criteria.
- v1.1 (17 Feb 2026): Added Appendix E — Old System UI Analysis from Army Roll of Honour screenshots
- v1.0 (16 Feb 2026): Initial document

**Next Review:** After PRD D implementation begins
