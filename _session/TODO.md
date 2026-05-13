# TODO

## Active queue

- [ ] **Validate the silent auto-update path end-to-end on the user's Windows machine.** AppMutex fix is shipped (v0.2.3 baseline) and v0.2.4 is published, but a clean observed silent update has not yet been confirmed in the field. Next concrete step (cut v0.2.5 with a tiny visible change vs. force-trigger on existing install) to be decided per author-approval in the next mini-pass.

## Next-up (not started; pick by user direction)

- [ ] **Audit the `archive` remote for unmerged work.** Older Inno Setup scripts and vendored assets done independently in the legacy private repo `SDGW1914-1919`. Deferred per [CLAUDE.md §11](../CLAUDE.md) — only revisit with explicit user sign-off because the two histories have diverged.

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

- [x] **AppMutex fix shipped + v0.2.4 published** (2026-05-12 / 2026-05-13). Fixed the missing-`AppMutex` bug in [`installer.iss`](../packaging/installer.iss) + matching mutex in [`launcher.py`](../launcher.py) (commit [`913c31a`](https://github.com/eek2020/SDGW1914-1919-v2/commit/913c31a) → v0.2.3 baseline). Cut v0.2.4 (commit [`2b22f3e`](https://github.com/eek2020/SDGW1914-1919-v2/commit/2b22f3e), `.version-tag` opacity 0.6 → 0.85) as a proof-point candidate. **End-to-end field validation of the silent update is incomplete and back in the Active queue** — a prior session log overstated success. See [PROGRESS.md](PROGRESS.md) for the correction.
- [x] **Adopted EngineeringFramework session-continuity pattern** (2026-05-12). Created `_session/HANDOVER.md` + `_session/TODO.md` + `_session/PROGRESS.md`; added bootstrap pointer at the top of [CLAUDE.md](../CLAUDE.md). See [PROGRESS.md](PROGRESS.md) for the framing decision.
- [x] **Phase A — Data Access** (mdbtools → CSV extraction pipeline; one-time).
- [x] **Phase B — Migration** (CSV → SQLite; `src/data_migration.py`; 703,806 rows landed across 8 tables + 27 indexes).
- [x] **Phase C — Web UI** (Flask app at `src/web_app.py`; 7 Jinja2 templates; Tom Select + Lucide vendored; 120 tests passing).
- [x] **Phase D — Windows desktop `.exe`** (substantially complete). PyInstaller spec at `packaging/sdgw.spec`; Inno Setup installer at `packaging/installer.iss`; CI workflow at `.github/workflows/build-windows.yml`; silent auto-updater at `src/updater.py`; version stamp at `src/version.py`; DB hosted at `db-base` Release tag; public download URL at `releases/latest/download/SDGW-Setup.exe`. Last remaining proof point: end-to-end validation on a real Windows machine (see Active queue).
