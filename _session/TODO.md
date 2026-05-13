# TODO

## Active queue

*(empty — Phase D is fully signed off in the field as of 2026-05-13. Pick from Next-up.)*

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
- **Updater throttle behavior on download failure.** `_mark_checked()` in [`src/updater.py`](../src/updater.py) is called after a successful API call but before the download attempt, so a failing download (e.g. the v0.2.3 SSL bug) sets the 24h throttle file anyway and the user can't naturally retry without deleting `%LOCALAPPDATA%\SDGW\last_update_check`. Better behavior: reset the throttle in the `worker()` exception path in `_show_splash_and_install()`. Won't recur once the silent path is fully validated; low priority but real friction if any future regression breaks the download leg again.
- **GitHub Actions deprecation warnings.** CI annotations on every run flag Node.js 20 actions (`actions/cache@v4`, `actions/checkout@v4`, `actions/setup-python@v5`, `actions/upload-artifact@v4`) as deprecated by 2026-06-02 with removal by 2026-09-16. Also the `windows-2025` runner is being redirected to `windows-2025-vs2026` (already transparent; pin the new label when convenient). Not blocking today but worth a maintenance mini-pass before the June deadline.

## Done

- [x] **Silent auto-update path validated end-to-end** (2026-05-13). Three load-bearing fixes shipped and proven in the field over a single working day: AppMutex (v0.2.3, commit [`913c31a`](https://github.com/eek2020/SDGW1914-1919-v2/commit/913c31a)) to close the running app cleanly, truststore SSL (v0.2.5, commit [`a754eef`](https://github.com/eek2020/SDGW1914-1919-v2/commit/a754eef)) to allow the installer download over GitHub's release CDN, paired `[Run]` with `skipifnotsilent` (v0.2.7, commit [`bfd6bf8`](https://github.com/eek2020/SDGW1914-1919-v2/commit/bfd6bf8)) to reopen the app post-install. Final field result: v0.2.6 → v0.2.7 hands-free, 71-second relaunch latency. See [PROGRESS.md](PROGRESS.md) for the full diagnostic narrative.
- [x] **Adopted EngineeringFramework session-continuity pattern** (2026-05-12). Created `_session/HANDOVER.md` + `_session/TODO.md` + `_session/PROGRESS.md`; added bootstrap pointer at the top of [CLAUDE.md](../CLAUDE.md). See [PROGRESS.md](PROGRESS.md) for the framing decision.
- [x] **Phase A — Data Access** (mdbtools → CSV extraction pipeline; one-time).
- [x] **Phase B — Migration** (CSV → SQLite; `src/data_migration.py`; 703,806 rows landed across 8 tables + 27 indexes).
- [x] **Phase C — Web UI** (Flask app at `src/web_app.py`; 7 Jinja2 templates; Tom Select + Lucide vendored; 120 tests passing).
- [x] **Phase D — Windows desktop `.exe`** (substantially complete). PyInstaller spec at `packaging/sdgw.spec`; Inno Setup installer at `packaging/installer.iss`; CI workflow at `.github/workflows/build-windows.yml`; silent auto-updater at `src/updater.py`; version stamp at `src/version.py`; DB hosted at `db-base` Release tag; public download URL at `releases/latest/download/SDGW-Setup.exe`. Last remaining proof point: end-to-end validation on a real Windows machine (see Active queue).
