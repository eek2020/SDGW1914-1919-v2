# CLAUDE.md

Guidance for Claude (and other AI coding assistants) when working in this repository.

This file is the AI-facing complement to `README.md`, `docs/MASTER_PLAN.md`, and `docs/process/DEVELOPMENT_GUIDE.md`. Read those first if you need deeper detail; this document distils what an assistant needs to be productive without breaking anything.

---

## 1. Project at a Glance

- **Name:** SDGW 1914-1919 — Soldiers Died in the Great War 1914-19
- **Purpose:** Modern web/desktop search interface over **703,806 WWI military personnel records** originally distributed on a Naval & Military Press CD-ROM (Version 2.5).
- **Audience:** Genealogy researchers, historians, and family members — **many aged 60–80+**. The current primary end user is a specific 70-year-old, distributed via a one-URL download (see §11). Accessibility is not optional.
- **Status:** Phases A (Data Access), B (Migration), C (Web UI) complete. **Phase D (Windows desktop `.exe`) substantially complete** — PyInstaller spec, Inno Setup installer, GitHub Actions release workflow, silent auto-updater, and a public download URL are all shipped. Active work: validating the auto-update path end-to-end on a real Windows machine.
- **Single source of truth for planning:** `docs/MASTER_PLAN.md`. Update it when scope changes.

---

## 2. Tech Stack

| Layer | Choice | Notes |
| --- | --- | --- |
| Language | Python 3.11+ | Standard library used heavily; minimal deps |
| Web framework | Flask 3.0.0 | Single-file app `src/web_app.py` (~1,722 lines) |
| Templating | Jinja2 | Server-rendered, no SPA |
| Frontend | Vanilla JS + CSS | Tom Select 2.4.1 + Lucide 0.469 **vendored** at `src/static/vendor/` — no CDN dependency, works offline. **No build step.** |
| Database | SQLite (file-based) | `data/sd_2011.db` (~470 MB, gitignored) |
| Tests | pytest 7.4.3 + BeautifulSoup 4.12.2 | 120 tests across 4 files |
| Desktop shell | pywebview 5.1 | Single-window launcher (`launcher.py`) |
| Build (Windows) | PyInstaller via `packaging/sdgw.spec` + Inno Setup via `packaging/installer.iss` | CI in `.github/workflows/build-windows.yml` |
| Release host | GitHub Releases on `eek2020/SDGW1914-1919-v2` (public) | Asset URL is `releases/latest/download/SDGW-Setup.exe` |
| DB host | GitHub Release tag `db-base` | Asset `sd_2011.db.zip`; CI fetches at build time |
| Legacy extract | mdbtools | One-time, only needed to rebuild from `.mdb` |

Dependencies are pinned in `requirements.txt`. Build-time extras (`pyinstaller`) live in `requirements-build.txt`. Do not add new runtime dependencies without a strong reason — the project deliberately stays close to the standard library.

---

## 3. Repository Layout

```text
SDGW1914-1919/
├── CLAUDE.md                       <-- this file
├── README.md                       Human-facing overview
├── requirements.txt                Pinned runtime deps
├── requirements-build.txt          Extra deps for PyInstaller builds
├── server.sh                       Dev server control (start|stop|restart|status)
├── launcher.py                     pywebview single-window launcher (dev + frozen)
├── SDGW 1914-1919.app/             macOS dev launcher (Eric's local Mac)
├── SDGW 1914-1919.bat              Windows dev launcher (legacy; real Windows install is the .exe)
├── data/                           DBs, CSV exports, backups (mostly gitignored; ~470 MB DB)
├── .github/workflows/
│   └── build-windows.yml           CI: PyInstaller + Inno Setup, publishes Releases on v* tags
├── src/
│   ├── web_app.py                  Flask routes, search, APIs, settings
│   ├── annotations.py              AnnotationManager (user-contributed data + images)
│   ├── data_access.py              MDB -> CSV (one-time)
│   ├── data_migration.py           CSV -> SQLite (one-time)
│   ├── updater.py                  Silent self-update on launch (Windows + frozen only)
│   ├── version.py                  __version__ stamp (overwritten by CI at build time)
│   ├── schema.sql                  Core DDL: 8 tables, 27 indexes
│   ├── schema_amendments.sql       Annotation/image DDL: 4 tables, 2 views
│   ├── reference_data.sql          Regiment names, theatres, regions, keywords
│   ├── scripts/                    One-shot utilities (export, validate, migrate, etc.)
│   ├── templates/                  7 Jinja2 templates
│   └── static/
│       ├── style.css
│       ├── SDGW1419.ico / .icns
│       └── vendor/                 Tom Select + Lucide (vendored)
├── tests/                          120 tests (test_data_access, test_migration,
│                                              test_web_app, test_ui)
├── packaging/
│   ├── sdgw.spec                   PyInstaller spec (entry, hidden imports, datas)
│   ├── installer.iss               Inno Setup script (per-user install, no UAC)
│   └── upload-db-base.sh           One-time helper to zip + upload the DB to the db-base release
└── docs/
    ├── MASTER_PLAN.md              Authoritative plan; update on scope changes
    ├── architecture/DATABASE_SCHEMA.md
    ├── process/DEVELOPMENT_GUIDE.md
    └── archive/                    Historical PRDs and superseded plans
```

---

## 4. How to Run, Test, Debug

All commands assume the repo root as the working directory.

### Install (dev)

```bash
pip3 install -r requirements.txt
```

### Run (developer)

```bash
./server.sh start          # background, logs to logs/sdgw_server.log, port 5001
./server.sh status
./server.sh stop
./server.sh restart
```

Or directly:

```bash
python3 src/web_app.py     # foreground; same port 5001
```

### Run (single-window desktop, dev)

```bash
python3 launcher.py        # starts Flask in a daemon thread + native pywebview window
```

### Tests

```bash
python3 -m pytest tests/ -v                    # all 120 tests
python3 -m pytest tests/test_web_app.py -v     # routes
python3 -m pytest tests/test_ui.py -v          # HTML structure / accessibility
```

`tests/test_data_access.py` is auto-skipped if `mdbtools` and `data/sd_2011.mdb` are not present. The other suites require `data/sd_2011.db`.

### Rebuild the database (rare)

Follow the seven-step pipeline in `README.md` or `docs/process/DEVELOPMENT_GUIDE.md`. Do **not** invent a new pipeline — the existing scripts in `src/scripts/` are the contract.

### Cut a release (see §11 for the full flow)

```bash
git tag v0.X.Y
git push origin v0.X.Y      # CI builds and publishes SDGW-Setup.exe to GitHub Releases
```

---

## 5. Conventions to Respect

- **PEP 8** for Python. No linter is enforced but match the surrounding style.
- **SQL:** Uppercase keywords, lowercase identifiers.
- **HTML/CSS:** Semantic HTML5, ARIA landmarks, **WCAG AAA** contrast (7:1), 18px+ fonts, 44px touch targets, full keyboard support, `skip-to-main` link.
- **Templates:** Jinja2 server-side rendering. No SPA framework, no client-side router.
- **JavaScript:** Vanilla JS inline in templates. **Do not introduce a build step or framework** (React, Vue, Svelte, etc.).
- **Database access:** Direct `sqlite3` module. **No ORM.** Always use parameterised queries.
- **Comments:** Don't add or remove comments without being asked. Match the existing density.

---

## 6. Hard Constraints — Read Before Editing

These are non-negotiable invariants enforced by code review or the architecture:

1. **Original historical records are immutable.** All user-contributed data goes into `record_annotations`, `record_images`, and `annotation_history` (see `src/schema_amendments.sql`). Never `UPDATE` rows in `soldiers` or `officers`.
2. **No string-interpolated SQL.** The only place column names may be interpolated is via the `_SAFE_TEXT_COLUMNS` allowlist or `VALID_ANNOTATION_FIELDS` in `src/web_app.py`/`src/annotations.py`. Everywhere else: `?` placeholders.
3. **Write endpoints must call `_check_write_auth()`** in `src/web_app.py`. The optional `SDGW_WRITE_PASSPHRASE` env var gates all annotation/image writes.
4. **Secret key from env only.** `FLASK_SECRET_KEY` is sourced from the environment; `server.sh` and `launcher.py` auto-generate one if not set. Never hardcode a secret.
5. **120 tests must stay green.** If you change behaviour, update or add tests in the same change. If a test now fails, fix the cause — do not delete or weaken the test.
6. **Filter cache is shared state.** `src/web_app.py` uses `threading.Lock` around the filter-options cache (TTL 20 s, max 256 entries). Preserve the lock when touching that code.
7. **Don't commit data files.** `data/*.db`, `data/*.mdb`, `data/backups/`, and the two big CSVs are gitignored. The DB is ~470 MB.
8. **Accessibility regressions are bugs.** Lowering contrast, shrinking fonts/targets, or removing keyboard handlers requires explicit user sign-off.
9. **End-user distribution UX is a hard constraint.** See §11. The primary end user is a 70-year-old who can't be visited or screen-shared; the install/update flow must be friction-zero from his end. Any change that adds a UAC prompt, dialog choice, or "click here to update" path needs explicit user sign-off.

---

## 7. Key Configuration Values

These constants live in `src/web_app.py` (or `src/annotations.py`, `src/updater.py`). When tuning, change them in one place.

| Setting | Value | Where |
| --- | --- | --- |
| Server port | 5001 | `server.sh`, `src/web_app.py`, `launcher.py` |
| Results per page | 20 | `RESULTS_PER_PAGE` in `src/web_app.py` |
| Filter cache TTL | 20 s | `src/web_app.py` |
| Filter cache max entries | 256 | `src/web_app.py` |
| Slow-query log threshold | 250 ms | `src/web_app.py` |
| Max CSV export rows | 10,000 | `src/web_app.py` |
| Max image upload size | 10 MB | `src/annotations.py` |
| Text suggestion limit | 60 | `src/web_app.py` |
| Update check throttle | 24 h | `CHECK_INTERVAL_SECONDS` in `src/updater.py` |
| Update API timeout | 5 s | `NETWORK_TIMEOUT_SECONDS` in `src/updater.py` |
| Update download timeout | 10 min | `DOWNLOAD_TIMEOUT_SECONDS` in `src/updater.py` |
| PID file (dev) | `/tmp/sdgw_server.pid` | `server.sh` |
| Server log (dev) | `logs/sdgw_server.log` | `server.sh` |
| Updater log (frozen) | `%LOCALAPPDATA%\SDGW\updater.log` | `src/updater.py` |

---

## 8. Frequently Useful Paths

- **Search routing & SQL:** `src/web_app.py` — start at `/search` and `/api/filter-options`.
- **Annotations CRUD:** `src/annotations.py` (`AnnotationManager`) + write routes in `src/web_app.py`.
- **Schema:** `src/schema.sql` (core), `src/schema_amendments.sql` (annotations), `src/reference_data.sql` (regiment names, theatres, regions, keywords).
- **Search results template:** `src/templates/search_results.html` (card/table toggle, pills, pagination).
- **Detail view:** `src/templates/detail.html` (record nav, related records, clipboard, print).
- **Styling and themes:** `src/static/style.css` (light/dark/system, density, layout, font size).
- **Desktop entry:** `launcher.py`; frozen-build entry uses `getattr(sys, 'frozen', False)` branch in `src/web_app.py`.
- **Auto-updater:** `src/updater.py` (silent on-launch check + splash + Inno Setup spawn).
- **Version stamp:** `src/version.py` — `__version__` is overwritten by CI at build time from the git tag.
- **PyInstaller bundle recipe:** `packaging/sdgw.spec` (hidden imports, datas, console=False, icon).
- **Installer recipe:** `packaging/installer.iss` (per-user, no UAC, /SILENT-capable for the updater).
- **DB upload helper:** `packaging/upload-db-base.sh` (zip + push DB to the `db-base` Release).
- **CI workflow:** `.github/workflows/build-windows.yml`.

---

## 9. Working Style for Claude

- **Prefer minimal, focused edits.** Match existing patterns rather than refactoring opportunistically.
- **Read before editing.** This codebase has accumulated context. Many "obvious" cleanups have already been done deliberately.
- **Confirm before sweeping changes.** Splitting `web_app.py` into blueprints, adding a JS framework, swapping to an ORM, or migrating image storage are all on the roadmap — they are not drive-by tasks.
- **Update `docs/MASTER_PLAN.md` when scope shifts.** It is the single source of truth.
- **Don't create extra docs unprompted.** This file, the README, and the docs in `docs/` already cover everything; don't scatter new `.md` files at the root.
- **Honour the audience.** Any UI change should be testable by a 70-year-old on a 1366×768 laptop with reading glasses. Big targets, plain language, no jargon, no tiny icons without labels.
- **Use the project permission allowlist.** `.claude/settings.json` pre-approves read-only inspection commands (git status/log/diff, gh run/release view, file reads) so non-destructive work moves at pace. Operations that change state — `git push`, `git tag`, `gh release create/upload`, `gh repo edit`, `rm`, etc. — still prompt for confirmation. **Do not silently expand the allowlist** to include state-changing commands; ask first.
- **Keep code clean and lean. Don't trade clean for fast silently.** When a quick fix would solve the immediate problem but introduce later rework (a hardcoded branch, a workaround layered on a workaround, a copy-paste rather than a small extraction), name the tradeoff out loud before taking it: "this solves it now but costs us X later because Y — happy to do the lean version, takes a bit longer." Silent quick fixes accumulate into technical debt that becomes invisible until it's expensive to unwind. Three more lines of properly-scoped code today is almost always cheaper than the rewrite next quarter.

---

## 10. Known Technical Debt (Do Not Re-Discover)

These are tracked in `docs/MASTER_PLAN.md` §6. Don't rediscover them as "bugs" — they're intentional deferrals:

- Annotation UI integration on the detail page is partial (backend complete).
- Images are stored as SQLite BLOBs; filesystem migration is on the roadmap.
- Detail-page navigation issues 10 queries; a 3-record window query is planned.
- `AnnotationManager` opens its own DB connections rather than sharing the Flask request-scoped one.
- `fuzzy_suggest` issues 22+ queries; caching is planned.
- Tests run against the production DB; fixture-based isolation is planned.
- `reference_data.sql` is not auto-applied during migration.
- CI runs the Windows build pipeline only; pytest is not yet wired into CI.
- Auto-updater has no rollback path; recovery for a bad release is "uninstall via Add/Remove Programs, reinstall from URL". Ship releases carefully.
- Vendored JS/CSS in `src/static/vendor/` are not auto-updated; bump manually when needed.

---

## 11. Distribution & Releases — How This Ships

The end-user pipeline is the load-bearing thing right now; understand it before changing anything in `packaging/`, `.github/workflows/`, `launcher.py`, `src/updater.py`, or `src/version.py`.

### Two remotes

```
origin   https://github.com/eek2020/SDGW1914-1919-v2.git   (PUBLIC, active)
archive  https://github.com/eek2020/SDGW1914-1919.git      (PRIVATE, legacy)
```

`archive` holds an earlier parallel iteration with overlapping but unmerged work (older Inno Setup scripts, USB-build helpers, vendored assets done independently). Do not fetch/merge from `archive` without explicit user sign-off — it is preserved for audit, not for active development.

### The end-user journey

The primary end user is one specific 70-year-old. He cannot be visited, cannot screen-share, and any install step that requires him to make a decision is a likely support call. The whole pipeline exists to eliminate those decisions:

1. Eric emails one URL: `https://github.com/eek2020/SDGW1914-1919-v2/releases/latest/download/SDGW-Setup.exe`
2. He clicks it in a browser. Browser downloads `SDGW-Setup.exe` (~81 MB; LZMA2/ultra compression of ~525 MB worth of app + DB + Python).
3. He double-clicks. SmartScreen blue dialog appears (because no code-signing). He follows the emailed screenshot: **More info → Run anyway**. (SmartScreen does NOT fire on subsequent auto-updates because the trusted running app launches the new installer.)
4. Inno Setup wizard runs. **No UAC prompt** (per-user install to `%LOCALAPPDATA%\SDGW`). **No "this user / all users" prompt** (we explicitly suppressed it). Welcome → Install → Progress → Finish (with "Launch SDGW" pre-ticked).
5. App opens. Desktop shortcut + Start Menu entry exist.
6. **From here on, every launch silently checks for updates** (throttled to once per 24 h) and installs them with a small "Updating SDGW…" splash. He never sees the URL again.

### Cutting a release

```bash
git tag v0.X.Y
git push origin v0.X.Y
```

The workflow `.github/workflows/build-windows.yml`:
- Computes version from the tag, **stamps `src/version.py`** so the frozen app knows its own identity.
- Downloads the SQLite DB from the `db-base` Release asset (CI doesn't have the DB locally — it's gitignored).
- Runs `pyinstaller packaging/sdgw.spec` → `dist/SDGW/SDGW.exe` + `_internal/`.
- Compiles `packaging/installer.iss` with Inno Setup → `build/SDGW-Setup.exe`.
- Uploads as a workflow artifact (30-day retention) on every push.
- **On `v*` tag pushes only**, attaches to the matching GitHub Release so `/releases/latest/download/` resolves to it.

The download URL is stable: GitHub redirects `/releases/latest/` to the most recent non-prerelease release.

### Updating the database

When the local DB content changes (regiment scrapes, theatre enrichment, typo fixes), re-upload it:

```bash
./packaging/upload-db-base.sh                           # default: ~/SDGW-USB/Windows/SDGW/data/sd_2011.db
./packaging/upload-db-base.sh /path/to/sd_2011.db       # override
```

The script zips with `zip -9`, ensures the `db-base` Release exists, and uploads `sd_2011.db.zip` as an asset (replacing the previous one). The next tagged release picks it up automatically.

### Auto-update mechanics

`src/updater.py` runs first in `launcher.main()`. On Windows + frozen only:

1. Skip if `%LOCALAPPDATA%\SDGW\last_update_check` is younger than 24 h.
2. GET `https://api.github.com/repos/eek2020/SDGW1914-1919-v2/releases/latest` (5 s timeout).
3. Parse `tag_name`; compare to `__version__` using `_parse_version` (major.minor.patch tuple).
4. If newer and `SDGW-Setup.exe` is an asset, open a small pywebview splash, download to `%TEMP%`, spawn the installer with `/SILENT /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS /NORESTART`.
5. Inno Setup overwrites files in place, relaunches `SDGW.exe`, new version opens.

**Fail-invisible:** every exception is swallowed; the app launches normally on any error.

**Diagnostics:** `%LOCALAPPDATA%\SDGW\updater.log` contains timestamped entries for every decision point (throttle skip, API call, version comparison, asset lookup, download, spawn, splash failure with traceback). Ask the user to paste it when investigating "no update happened."

**Testing the path:** the throttle file blocks repeated checks. To force a check on a test machine: delete `%LOCALAPPDATA%\SDGW\last_update_check` before launching. After validating manually, the throttle stays at 24 h in production code — never lower it.

### What stays manual

- Cutting a tag (deliberate — releases shouldn't be automatic).
- Uploading a new DB (rare, manual triggered by Eric).
- Auditing the `archive` remote for any work worth bringing over (deferred).
- Code signing (explicitly out of scope — see hard constraint §6.9).

---

**Last updated:** May 2026. Keep this file short and current; if it grows unwieldy, link out to `docs/` rather than duplicating.
