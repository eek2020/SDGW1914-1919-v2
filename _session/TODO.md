# TODO

## Active queue

- [ ] **Validate the silent auto-update path end-to-end on a real Windows machine.** The load-bearing thing right now — the whole "email one URL forever" distribution promise is unproven until we've watched a silent update succeed in the field.
  - Pre-requisite: a newer release tag than the version installed on the target machine. Either an existing newer release on `eek2020/SDGW1914-1919-v2`, or cut a no-op bump tag (see next item).
  - On target machine: delete `%LOCALAPPDATA%\SDGW\last_update_check` to bypass the 24h throttle. Launch SDGW. Watch for splash → install → relaunch → footer shows new version.
  - On any failure: read `%LOCALAPPDATA%\SDGW\updater.log` — every decision point is logged ([`src/updater.py`](../src/updater.py)).
  - Once proven: never lower the 24h throttle in production code.

- [ ] **Cut a no-op version-bump tag** *(supports the validation above; needs explicit user sign-off — tag push affects shared state)*.
  - `git tag v0.X.Y+1 && git push origin v0.X.Y+1`. CI ([`.github/workflows/build-windows.yml`](../.github/workflows/build-windows.yml)) builds and attaches `SDGW-Setup.exe` to the matching GitHub Release.
  - Pair with a trivial visible change (e.g. footer string tweak) so the user can confirm the version flipped after the silent update.

## Next-up (not started; pick by user direction)

- [ ] **Fix May 2026 USB build installer bug.** Wrong source-folder path in the PowerShell installer ships in the May 2026 USB build. Blocks any further Windows USB handover. Not blocking the .exe path. Lower priority since auto-update is now the primary channel.

- [ ] **Audit the `archive` remote for unmerged work.** Older Inno Setup scripts, USB-build helpers, vendored assets done independently in the legacy private repo `SDGW1914-1919`. Deferred per [CLAUDE.md §11](../CLAUDE.md) — only revisit with explicit user sign-off because the two histories have diverged.

- [ ] **Decide on archival-as-skill for PROGRESS.md cadence.** Currently a prose rule in HANDOVER.md (Path A). Path B would author a `.claude/skills/archive-progress.md` skill to operationalise the cadence. Decide when archival passes start firing often enough that manual execution is friction. Right now, n = 0 archival passes — defer until needed.

## Open questions to resolve later

- **Annotation UI integration on the detail page** is partial (backend complete). When prioritised, do as its own mini-pass.
- **Image storage as filesystem instead of SQLite BLOBs.** Roadmap item; defer until BLOB size becomes a real concern.
- **Detail-page navigation query count** — 10 queries; replace with a 3-record window query. Performance debt, not a bug.
- **`fuzzy_suggest` query count** — 22+ queries; needs caching. Performance debt.
- **Test isolation** — tests run against the production DB; fixture-based isolation is on the roadmap.
- **CI test wiring** — CI runs the Windows build pipeline only; pytest is not yet wired into CI.
- **Auto-updater rollback path** — none currently. Recovery for a bad release is "uninstall via Add/Remove Programs, reinstall from URL". Ship releases carefully.

## Done

- [x] **Adopted EngineeringFramework session-continuity pattern** (2026-05-12). Created `_session/HANDOVER.md` + `_session/TODO.md` + `_session/PROGRESS.md`; added bootstrap pointer at the top of [CLAUDE.md](../CLAUDE.md). See [PROGRESS.md](PROGRESS.md) for the framing decision.
- [x] **Phase A — Data Access** (mdbtools → CSV extraction pipeline; one-time).
- [x] **Phase B — Migration** (CSV → SQLite; `src/data_migration.py`; 703,806 rows landed across 8 tables + 27 indexes).
- [x] **Phase C — Web UI** (Flask app at `src/web_app.py`; 7 Jinja2 templates; Tom Select + Lucide vendored; 120 tests passing).
- [x] **Phase D — Windows desktop `.exe`** (substantially complete). PyInstaller spec at `packaging/sdgw.spec`; Inno Setup installer at `packaging/installer.iss`; CI workflow at `.github/workflows/build-windows.yml`; silent auto-updater at `src/updater.py`; version stamp at `src/version.py`; DB hosted at `db-base` Release tag; public download URL at `releases/latest/download/SDGW-Setup.exe`. Last remaining proof point: end-to-end validation on a real Windows machine (see Active queue).
