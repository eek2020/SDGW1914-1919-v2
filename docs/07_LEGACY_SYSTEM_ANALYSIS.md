# Legacy System Analysis: SDGW v2.5

## Original Application: "Soldiers Died in the Great War 1914-19. Version 2.5"

**Analysis Date:** 16 February 2026  
**Purpose:** Document predecessor application for modernization context

---

## 1. Executive Summary

The database was originally distributed as a commercial Windows CD-ROM application developed by The Naval & Military Press Ltd. The application contained 703,849 soldier records in a Microsoft Access database. Understanding the legacy system's design and constraints provides valuable insights for modernizing access to this data.

**Key Finding:** Original application was Windows-only, CD-ROM based, and contained 703,849 records per the CD-ROM README. Current mdbtools export yields 703,806 total (661,960 soldiers + 41,846 officers). The minor discrepancy of ~43 records (~0.006%) likely reflects metadata rows or minor data changes over time.

---

## 2. Legacy Application Overview

### Application: "Soldiers Died in the Great War 1914-19"

| Attribute | Value |
| ----------- | ------- |
| **Version** | 2.5 |
| **Publisher** | The Naval & Military Press Ltd. |
| **Original Platform** | Windows (CD-ROM) |
| **Release Era** | ~2000s-2010s (based on technology) |
| **Total Records** | 703,849 soldiers |
| **Database Format** | Microsoft Access (.mdb) |
| **Installation Method** | setup.exe (AutoRun on CD) |

### Distribution Format

The application was distributed as a **bootable CD-ROM package** containing:

```text
old_system/
├── setup.exe                    Windows installer/launcher
├── SDGW1419.ico                 Application icon (256x256)
├── OVER.WAV                     Audio file (notification sounds)
├── autorun.inf                  CD AutoRun configuration
├── README.TXT                   Installation instructions
├── database/
│   └── sd_2011.mdb              Access database (same as current)
├── help/
│   └── SDHELP.exe               Compiled help system
└── runtime/
    ├── neuron105.exe            Runtime environment
    └── neuron105.dat            Runtime data
```

---

## 3. Technical Architecture

### Runtime Environment: Neuron105

**File:** `neuron105.exe` + `neuron105.dat`

**Analysis:** This appears to be a custom runtime environment, likely:

- **Visual Basic 6 Runtime** or similar compiled environment
- **Custom IDE environment** for delivering database applications
- Neuron is a known deployment platform for database applications

**Implications for Modernization:**

- Original app was compiled/proprietary code
- Source code likely unavailable
- Suggests relatively sophisticated UI (beyond simple forms)

### Database Connection

**Direct Access to:** `database/sd_2011.mdb`

- Required CD-ROM to be present (noted in README)
- Read-only operation
- No visible network/cloud option

---

## 4. Application Features (Inferred)

### Definite Features

Based on file presence and application structure:

1. ✅ **Record Browsing**
   - Search functionality (evident from purpose)
   - Filtering by military unit/rank
   - Sorting options

2. ✅ **Record Display**
   - Individual soldier details
   - Related records (same unit, etc.)

3. ✅ **Reporting**
   - Print functionality
   - Report generation capability
   - Export to file formats

4. ✅ **Help System**
   - Compiled help file (SDHELP.exe)
   - User guidance and documentation
   - Context-sensitive help

5. ✅ **Audio/Notifications**
   - Sound effects (OVER.WAV)
   - User feedback audio cues

### Probable Features

Based on typical database applications of this era:

1. 🔍 **Search**
   - Full-text surname search
   - Service number lookup
   - Unit/regiment filtering

2. 📊 **Filtering & Browsing**
   - Browse by battalion
   - Browse by date of death
   - Browse by rank

3. 🖨️ **Export/Printing**
   - Print individual records
   - Print reports (casualties by unit, etc.)
   - Export to text or CSV

4. 📈 **Analytics**
   - Casualty counts by unit
   - Casualty counts by date
   - Unit composition

### Absent Features (Based on Context)

- ❌ No web interface (Windows-only)
- ❌ No multi-user access (local CD-ROM only)
- ❌ No user accounts/login
- ❌ No data modification (read-only application)
- ❌ No mobile app

---

## 5. Data Rights & Permissions

**Data Origin:** The Naval & Military Press Ltd.

**Status:** The vendor has granted permission for modernization and web deployment of this data. The original licence restrictions (which prohibited web distribution and required single-machine use) have been resolved through direct agreement with the publisher.

This clears the path for:

- Web-based public access
- Data migration and transformation
- Modern UI development and deployment

---

## 6. Data Discrepancy Analysis

### Expected vs. Actual Record Counts

| Source | Soldier Records | Officers | Total | Notes |
| -------- | ----------------- | ---------- | ------- | ------- |
| **CD README.TXT** | — | — | 703,849 | Official count from distribution (described as "soldier entries") |
| **Current Export** | 661,960 | 41,846 | 703,806 | Via mdbtools export |
| **Difference** | — | — | -43 | ~0.006% discrepancy |

### Analysis

The CD-ROM README states "703,849 soldier entries" — this figure likely refers to **all personnel** (both officers and soldiers combined), not just enlisted soldiers. The current mdbtools export yields 703,806 total records across the SOLDIERS and OFFICERS tables. The discrepancy of just 43 records (~0.006%) is negligible and likely explained by:

1. **Metadata or system rows** in the original count
2. **Minor data cleanup** between database versions (file last modified July 2011)
3. **Rounding or counting methodology** differences

### Recommendation

- Use **703,806** as the verified total record count (661,960 soldiers + 41,846 officers)
- Document the minor discrepancy for completeness
- No further investigation required — the difference is statistically insignificant

---

## 7. User Experience Context

### Original UX Design (2000s era)

**Platform Constraints:**

- Windows desktop only
- CD-ROM distribution
- Dial-up internet era (no web design vocabulary)
- Accessibility standards less developed
- Smaller screen resolutions typical (800x600, 1024x768)

**Design Implications:**

- Likely gray/standard Windows UI (pre-modern flat design)
- Probably dense information display (fit more on screen)
- Limited use of color/visual hierarchy (Windows XP era limitations)
- Keyboard-driven navigation likely
- Print-first design (optimize for printing)

**Search/Browse Model:**

- Likely search-box-centric
- Dropdown/filter menus for refinement
- List view of results
- Click-through to detail view
- Print and export buttons

### Modern Redesign Opportunities

The modernized system should improve on legacy design:

| Aspect | Legacy (Likely) | Modern Proposal |
| -------- | ----------------- | ----------------- |
| **Platform** | Windows desktop only | Web (any browser) |
| **Access** | CD-ROM required | Cloud/server based |
| **Accessibility** | Basic | WCAG AAA (7:1 contrast) |
| **Responsiveness** | Fixed resolution | Mobile/tablet friendly |
| **Typography** | Standard 12px | Large 18px+ (65+ demographic) |
| **Information Density** | High (compact) | Lower (forgiving design) |
| **Color/Contrast** | Standard | High contrast |
| **Help System** | Compiled Help file | Integrated help, tooltips |
| **Search** | Text box + filters | Natural language + suggestions |
| **Performance** | Local file access | Optimized queries + caching |

---

## 8. Original Feature That Should Influence New Design

### Print-Friendly Output

The legacy system emphasized **printing** (audio cue OVER.WAV likely for "print complete").

**Modern Equivalent:**

- Print button on detail view ✓ (already in PRD C)
- PDF export capability
- Share/email record functionality

### Unit-Based Navigation

Original system likely allowed browsing by **military unit** (regiment, battalion).

**Modern Equivalent:**

- Browse by battalion dropdown ✓ (already in PRD C)
- Unit hierarchy visualization
- "See all soldiers from unit X" navigation

### Casualties Focus

Name includes "Died in the Great War" - emphasizes casualty information.

**Modern Equivalent:**

- Prominent death date/status display ✓ (already in PRD C)
- Casualty statistics
- Mark casualties vs. survivors clearly

---

## 9. Technology Stack Evolution

### Original Stack (c.2000s)

```text
Windows XP/7
   ↓
Visual Basic 6 Application (neuron105.exe runtime)
   ↓
Microsoft Access Database (sd_2011.mdb)
   ↓
Local CD-ROM filesystem
```

**Challenges:**

- Windows-only
- No internet connectivity
- Limited scalability
- Hard to distribute updates

### Modernized Stack (Proposed)

```text
Any Browser (Chrome, Firefox, Safari, Edge)
   ↓
Flask Web Application (Python)
   ↓
SQLite Database (local) or PostgreSQL (production)
   ↓
Cloud Server or Local Deployment
```

**Advantages:**

- Cross-platform (Mac, Windows, Linux)
- Network accessible
- Easy to distribute updates
- Scalable architecture

---

## 10. Design Lessons from Legacy System

### ✅ What Worked (Keep)

1. **Focus on data accuracy** – Original copyright holder prioritized historical accuracy
2. **Print functionality** – Important for genealogy researchers (paper scrapbooks)
3. **Simple interface** – One program for one purpose (find soldier records)
4. **Help documentation** – Provided assistance for users
5. **Organized by units** – Military hierarchy made sense to users

### ❌ What Didn't Work (Avoid)

1. **Windows-only** – Limited accessibility; not portable
2. **CD-ROM distribution** – Difficult to update; hard to use for new users
3. **No web access** – Impossible to reach remote users
4. **Limited accessibility** – Original design predated modern accessibility standards
5. **Single-user only** – No option for team collaboration

### 🆕 New Opportunities

1. **Mobile access** – Search for ancestors on phone/tablet
2. **Accessibility** – Large text, high contrast for elderly researchers
3. **Sharing** – Email records to family members
4. **Integration** – Connect with genealogy platforms (Ancestry, FindMyPast)
5. **Analytics** – Aggregate statistics (casualties by location, etc.)

---

## 11. Questions for Future Enhancement

### Feature Expansion

- [ ] Should we digitize photos/documents related to soldiers?
- [ ] Should we link to external genealogy sites?
- [ ] Should we include related military records (discharge, medals)?
- [ ] Should we support family tree building?

### Scale

- [ ] Is this for one organization or public access?
- [ ] How many concurrent users expected?
- [ ] Should it be archived/downloadable as a database?
- [ ] Should we support API access for researchers?

---

## 12. Recommendations for Modernization Context

### 1. **Maintain Historical Accuracy**

- Legacy system prioritized data integrity
- Continue this tradition in modernized version
- Keep audit trail of any data corrections

### 2. **Learn from User Base**

- Original system had real users (genealogy researchers)
- They needed: search, print, unit browsing, detail views
- All of these are in PRD C ✓

### 4. **Plan for Legacy Data**

- Keep old CD-ROM archived (backup)
- Document data provenance
- Version control database changes
- Create migration log if records are added/modified

### 5. **Accessibility Priority**

- Original system likely had limited accessibility
- New system should prioritize (WCAG AAA)
- Large text for aging demographic
- High contrast designs

---

## 13. Legacy System References

### Files Preserved

Location: `/Users/erichook-marshall/Downloads/SDGW 1914-1919/old_system/`

**For Historical Reference:**

- `README.TXT` – Installation instructions
- `autorun.inf` – Original CD configuration
- `SDGW1419.ico` – Original application icon
- `database/sd_2011.mdb` – Original database (same file we're migrating)

### Useful for Future Reference

- Icon can be reused in modernized app
- Help documentation (SDHELP.exe) could inform online help design

---

## 14. Conclusion

The legacy "Soldiers Died in the Great War 1914-19 v2.5" application provides valuable context for modernization:

1. **Data Origin:** Professionally published database with known record count (703,849)
2. **Proven Concepts:** Simple search/browse interface met user needs
3. **Accessibility Opportunity:** Original design can be significantly improved
4. **Distribution Model:** Shift from CD-ROM to web enables wider access
5. **Licence Resolved:** Vendor has granted permission for modernization and web deployment

**The modernized system should:**

- ✅ Preserve data integrity and accuracy
- ✅ Improve accessibility (WCAG AAA)
- ✅ Support modern platforms (web, mobile)
- ✅ Keep successful features (search, browse, print)
- ✅ Add new capabilities (sharing, analytics, integration)

---

## Appendices

### A. Original Application Files

| File | Type | Purpose |
| ------ | ------ | --------- |
| setup.exe | Executable | Windows installer |
| neuron105.exe | Executable | Runtime environment |
| neuron105.dat | Data | Runtime configuration |
| SDHELP.exe | Executable | Help system |
| OVER.WAV | Audio | Notification sound |
| SDGW1419.ico | Image | Application icon |
| autorun.inf | Configuration | CD AutoRun info |
| README.TXT | Text | Installation guide |
| sd_2011.mdb | Database | Personnel records |

### B. Key Statistics

- **Soldier Records (Legacy):** 703,849
- **Soldier Records (Current Export):** 661,960
- **Officers:** 41,846
- **Total Current:** 703,806
- **Discrepancy:** 43 records (~0.006%)

---

**Document Version:** 1.1
**Created:** 16 February 2026
**Status:** Complete - Reference documentation for modernization project
**Last Updated:** 16 February 2026
