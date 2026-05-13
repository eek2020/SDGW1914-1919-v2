# TODO

## Active queue — CWGC rebuild (5-phase plan)

- [ ] **Phase 1 — CWGC investigation & access.** Find out how CWGC data is accessible today: public API at [cwgc.org](https://www.cwgc.org/find-records/), scraping ToS/robots, rate limits, whether bulk download is permitted, whether a cached dataset exists (Internet Archive, genealogy datasets, researcher partnership). Output: a written assessment with tradeoffs. **No code yet.** Each subsequent phase needs sign-off before starting.

- [ ] **Phase 2 — Schema & storage design.** New `cwgc_records` table with FK to `soldiers`/`officers`. Preserve CD immutability per [CLAUDE.md §6.1](../CLAUDE.md). Match key: surname + initials/christian_names + service_number + regiment_id + death_date. Fields: `casualty_id`, `cemetery_or_memorial`, `grave_reference`, `country_buried`, `age_at_death`, `next_of_kin`, `additional_info`, `cwgc_url`, `match_confidence`, `last_fetched_at`. Design for `src/scripts/cwgc_enrich.py` (idempotent + resumable + rate-limited + logs unmatched). Schema-only — no fetch yet.

- [ ] **Phase 3 — Run enrichment & validate.** Execute against all 703,806 records. At 1 req/s = 8+ days runtime; needs background-resumable design. Spot-check matches against soldiers user can identify by name.

- [ ] **Phase 4 — UI integration.** Detail page: new "Commonwealth War Graves" section when CWGC record present (cemetery, grave ref, age, next of kin, link out to cwgc.org). New "Data sources" diff panel showing CD-vs-CWGC discrepancies on rank/regiment/death-date/etc. — the section the user remembers having before. Optional search facets: has-CWGC, cemetery, country buried.

- [ ] **Phase 5 — Distribution.** Re-upload enriched DB via [`packaging/upload-db-base.sh`](../packaging/upload-db-base.sh). Bump version. Silent auto-updater carries it to the end user.

## Next-up (paused while CWGC is active; pick by user direction)

- [ ] **Restore archive-only logging + 500 handler.** Archive had `web_app.log` at `%TEMP%/SDGWLogs/web_app.log` (overridable via `SDGW_LOG_DIR`) plus `@app.errorhandler(Exception)` returning a friendly 500 page that pointed at the log path. Origin removed both. Worth restoring — matches the diagnostic patterns the updater already uses, and is genuinely valuable for the no-screenshare end-user. Mini-pass; cherry-pickable from `archive/main`.

- [ ] **Decide on archival-as-skill for PROGRESS.md cadence.** Currently a prose rule in HANDOVER.md (Path A). Path B would author a `.claude/skills/archive-progress.md` skill to operationalise the cadence. Decide when archival passes start firing often enough that manual execution is friction. Right now, n = 0 archival passes — defer until needed.

- [ ] **Stale-folder cleanup (~3.7 GB reclaim).** Six candidates surveyed in 2026-05-13 PROGRESS entry: `~/SDGW-build`, `~/SDGW-USB`, `~/SDGW1914-1919`, `~/SDGW1914-1919 copy`, `~/Downloads/sdgw-test`, `/Volumes/Repos/SDGW`. **DO NOT delete `/Volumes/Repos/SDGW 1914-19 2.5/`** — original CD master.

- [ ] **Confirm Time Machine setup with user.** `tmutil destinationinfo` → "No destinations configured". The DB has no automatic backup beyond the GitHub `db-base` Release. Particularly important to flag before committing a freshly-enriched (and expensive-to-rebuild) post-CWGC DB.

## Open questions to resolve later

- **Annotation UI integration on the detail page** is partial (backend complete). When prioritised, do as its own mini-pass.
- **Image storage as filesystem instead of SQLite BLOBs.** Roadmap item; defer until BLOB size becomes a real concern.
- **Detail-page navigation query count** — 10 queries; replace with a 3-record window query. Performance debt, not a bug.
- **`fuzzy_suggest` query count** — 22+ queries; needs caching. Performance debt.
- **Test isolation** — tests run against the production DB; fixture-based isolation is on the roadmap.
- **CI test wiring** — CI runs the Windows build pipeline only; pytest is not yet wired into CI.
- **Auto-updater rollback path** — none currently. Recovery for a bad release is "uninstall via Add/Remove Programs, reinstall from URL". Ship releases carefully.
- **Updater throttle behavior on download failure.** `_mark_checked()` in [`src/updater.py`](../src/updater.py) is called after a successful API call but before the download attempt, so a failing download (e.g. the v0.2.3 SSL bug) sets the 24h throttle file anyway and the user can't naturally retry without deleting `%LOCALAPPDATA%\SDGW\last_update_check`. Better behavior: reset the throttle in the `worker()` exception path in `_show_splash_and_install()`. Won't recur once the silent path is fully validated; low priority but real friction if any future regression breaks the download leg again.
- **`windows-2025` → `windows-2025-vs2026` runner label.** Transparent today via the `windows-latest` alias used in [`.github/workflows/build-windows.yml`](../.github/workflows/build-windows.yml). Pin the explicit new label only if/when a build pins on the precise toolchain. Low priority.

## Done

- [x] **Audited `archive` remote for divergence** (2026-05-13). Read-only fetched per CLAUDE.md §11 sign-off; no merge. Diff characterised in PROGRESS — five things archive had that origin lost (search loading overlay, per-page selector, `/health` endpoint, app-level file logging, friendly 500 handler). Most are intentional removals; the logging/500-handler pair is worth restoring (carried in Next-up above).

- [x] **DB integrity sweep + canonical SHA recorded** (2026-05-13). All four reachable copies of `sd_2011.db` are byte-identical: SHA-256 `945347461aef1d1c493d42a3adb1dfa85de3cb314ff1afd73556b99b7771ee1a`. Stored in `/Volumes/SDGW/SDGW/data/`, `/Volumes/SDGW/NEW/Windows/data/`, the GitHub `db-base` Release zip (uploaded 2026-05-12 18:36 UTC), and `data/sd_2011.db` (extracted locally for next-session script work). Confirmed: this DB has the CD baseline + reference enrichment from `src/reference_data.sql` but no CWGC fields — re-acquisition planned in Active queue above.

- [x] **CI actions bumped to Node 24 majors** (2026-05-13). [`.github/workflows/build-windows.yml`](../.github/workflows/build-windows.yml): `checkout v4→v5`, `setup-python v5→v6`, `cache v4→v5`, `upload-artifact v4→v6`. Shipped in commit [`ddc0b0c`](https://github.com/eek2020/SDGW1914-1919-v2/commit/ddc0b0c). Clears the 2026-06-02 deprecation deadline; CI run [25791179643](https://github.com/eek2020/SDGW1914-1919-v2/actions/runs/25791179643) triggered automatically on the `main` push.
- [x] **Silent auto-update path validated end-to-end** (2026-05-13). Three load-bearing fixes shipped and proven in the field over a single working day: AppMutex (v0.2.3, commit [`913c31a`](https://github.com/eek2020/SDGW1914-1919-v2/commit/913c31a)) to close the running app cleanly, truststore SSL (v0.2.5, commit [`a754eef`](https://github.com/eek2020/SDGW1914-1919-v2/commit/a754eef)) to allow the installer download over GitHub's release CDN, paired `[Run]` with `skipifnotsilent` (v0.2.7, commit [`bfd6bf8`](https://github.com/eek2020/SDGW1914-1919-v2/commit/bfd6bf8)) to reopen the app post-install. Final field result: v0.2.6 → v0.2.7 hands-free, 71-second relaunch latency. See [PROGRESS.md](PROGRESS.md) for the full diagnostic narrative.
- [x] **Adopted EngineeringFramework session-continuity pattern** (2026-05-12). Created `_session/HANDOVER.md` + `_session/TODO.md` + `_session/PROGRESS.md`; added bootstrap pointer at the top of [CLAUDE.md](../CLAUDE.md). See [PROGRESS.md](PROGRESS.md) for the framing decision.
- [x] **Phase A — Data Access** (mdbtools → CSV extraction pipeline; one-time).
- [x] **Phase B — Migration** (CSV → SQLite; `src/data_migration.py`; 703,806 rows landed across 8 tables + 27 indexes).
- [x] **Phase C — Web UI** (Flask app at `src/web_app.py`; 7 Jinja2 templates; Tom Select + Lucide vendored; 120 tests passing).
- [x] **Phase D — Windows desktop `.exe`** (substantially complete). PyInstaller spec at `packaging/sdgw.spec`; Inno Setup installer at `packaging/installer.iss`; CI workflow at `.github/workflows/build-windows.yml`; silent auto-updater at `src/updater.py`; version stamp at `src/version.py`; DB hosted at `db-base` Release tag; public download URL at `releases/latest/download/SDGW-Setup.exe`. Last remaining proof point: end-to-end validation on a real Windows machine (see Active queue).
