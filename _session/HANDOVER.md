# Handover

> **Read first when resuming.** Update at the end of every session.

## Status

**Phases A–D complete. Silent auto-update path proven hands-free end-to-end on 2026-05-13.** Three load-bearing fixes shipped that day: **AppMutex** (v0.2.3), **truststore SSL** (v0.2.5), **paired `[Run]` with `skipifnotsilent`** (v0.2.7). v0.2.6 → v0.2.7 hands-free relaunch in 71s.

**Most recent session (2026-05-14 PM): CWGC integration step 3 done + step 1 spot-check signed off + temp_support tidyup (~1.5 GB reclaimed).** Five production scripts moved into `src/scripts/`, canonical schema landed at new `src/sql/cwgc_schema.sql`, `requests==2.32.5` added to requirements, [CLAUDE.md](../CLAUDE.md) §3+§8 updated, `.gitignore` strengthened (db-shm/db-wal/temp_support). Obsolete v1 Playwright scraper overwritten in place by v4. Smoke-test artefacts (venv/, `data/cwgc_all.csv`, `data/cwgc_batches/`) deleted. From `temp_support/data/`, deleted: 6,536 batch CSVs (309 MB), merged `cwgc_all.csv` (205 MB), `source/` Feb-2026 CSVs (25 MB), both pre-CWGC `.bak` files (986 MB). `temp_support/` is now 2.3 GB, essentially just `sd_2011.db` (the enriched 2.5 GB DB awaiting step 4 swap).

**Step 1 spot-check verdict — data safe to adopt.** Sampled 25 soldier + 10 officer candidates from `v_cwgc_match_candidates`. All 19,399 medium candidates share match_reason `surname+christian_names+death_date`. Soldier candidates (18,051) overwhelmingly look like distinct men with the same name dying on major battle days (1916-07-01, 1915-09-25) — matcher correctly NOT promoting; operator default for most will be "reject". Officer candidates (1,348) have a much higher fraction of real matches; without service numbers to disambiguate, real secondment/attachment cases (SDGW Military Police ↔ CWGC parent regiment) bucket medium instead of high. **High-confidence band (615k matches) is trustworthy** — required name+DoD+svc# agreement. The 19,399-row operator-review queue is a Phase 4 UX problem; will need bulk-action tooling, not 1-by-1 clicking.

**SHA-mismatch finding (HANDOVER claim corrected).** Neither pre-CWGC .bak matched the canonical SHA `945347461aef...` recorded below; they were mid-pipeline checkpoints, not pristine pre-state. Current `data/sd_2011.db` still matches that canonical SHA — the true pre-CWGC baseline lives there + on GitHub `db-base` Release. Deleted both .bak files (user confirmed external backups).

Key recent commits: [`ddc0b0c`](https://github.com/eek2020/SDGW1914-1919-v2/commit/ddc0b0c) CI actions Node 24 bump, [`913c31a`](https://github.com/eek2020/SDGW1914-1919-v2/commit/913c31a) AppMutex fix, [`a754eef`](https://github.com/eek2020/SDGW1914-1919-v2/commit/a754eef) truststore SSL fix, [`bfd6bf8`](https://github.com/eek2020/SDGW1914-1919-v2/commit/bfd6bf8) paired `[Run]` relaunch fix.

## Active task

**Step 2 — decide on inactive-match pruning policy.** Two of four CWGC integration sub-tasks are done (step 3 repo integration + step 1 matcher spot-check). Remaining:

- [ ] **Step 2 — inactive-match pruning.** `cwgc_match` has 9,992,775 rows of which **9,358,116 are `is_active=0`** (overnight launchd refresh-cycle audit; *no* manual decisions — `confirmed_by` NULL on every active row, verified). Pruning takes the staged DB from **2.5 GB → ~700-1100 MB est.** (VACUUM-dependent). Distribution-relevant: with no pruning, the next 81 MB installer becomes ~350-400 MB. Reversible by re-running `cwgc_match.py --hard-reset` (which would re-derive matches from scratch). Decision points: do we prune to active-only? Prune but keep last N refresh cycles? VACUUM in same pass or separately? Recommend: full prune to active-only, VACUUM in same pass; the deactivated rows have zero forensic value (no human decisions in them).
- [ ] **Step 4 — DB swap.** Once pruned, move `temp_support/data/sd_2011.db` → `data/sd_2011.db` (current pre-CWGC baseline goes away — it's already preserved on GitHub `db-base` Release + user's external backups). Discard `temp_support/` entirely. Re-record canonical SHA in HANDOVER.

Phase 4 (UI wiring per the integration doc) and Phase 5 (distribution upload + version bump) remain after this batch.

## CWGC rebuild plan (5 phases, sign-off between each)

| Phase | Scope | Notes |
| --- | --- | --- |
| **1 — Investigation & access** | CWGC public access today (API/scrape/cached dataset), ToS/robots, rate limits. | **Done 2026-05-13.** [`docs/cwgc/phase1-assessment.md`](../docs/cwgc/phase1-assessment.md) — Option D (re-scrape) chosen. |
| **2 — Schema & storage design** | New `cwgc_records` + `cwgc_match` tables; convenience views joining through highest-confidence active match. Polymorphic `(record_type, record_id)`. Preserves CD immutability per [CLAUDE.md §6.1](../CLAUDE.md). | **Done 2026-05-14.** Schema in repo at [`src/sql/cwgc_schema.sql`](../src/sql/cwgc_schema.sql): 2 tables + 4 views + 10 indexes; verified consistent with deployed DB. |
| **3 — Run enrichment & validate** | Scrape 1914-08 → 1921-08; import to `cwgc_records`; layered matcher (exact / high-1:1-unambiguous / medium) populating `cwgc_match`. | **Done 2026-05-14.** 1.02M records, 88.2% soldier / 75.6% officer high-conf coverage. Step 1 spot-check signed off — high band trustworthy; medium band is honest ambiguity for operator review (Phase 4 UX needs bulk-action tooling, not 1-by-1). |
| 4 — UI integration | Detail page: new "Commonwealth War Graves" section sourced from `soldiers_with_cwgc` / `officers_with_cwgc` views. Operator review screen at `/admin/cwgc-review` driven by `v_cwgc_match_candidates` (needs bulk-action design for the 19,399-row queue). "Other casualties" tab driven by `v_cwgc_unmatched` (402k Indian Army / Newfoundland / etc.). Optional "Data sources" diff panel for CD-vs-CWGC discrepancies. Detailed wiring instructions in [`temp_support/cwgc_ingest_handover.md`](../temp_support/cwgc_ingest_handover.md). | Pending — starts after step 2 + step 4. |
| 5 — Distribution | Re-upload enriched DB via `packaging/upload-db-base.sh`. Version bump. Silent auto-updater carries it to the end user. | Pending — last step. |

## Next-up candidates (paused — promote after CWGC work, or interleave by user direction)

None block the others. The CWGC rebuild is the active priority; everything below is parked.

1. **Annotation UI integration on the detail page** is partial (backend complete). Promote when prioritised; do as its own mini-pass.
2. **Performance debt items** carried in TODO.md *Open questions* — detail-page query count, `fuzzy_suggest` caching, CI test wiring, fixture-based test isolation. Not blocking distribution.
3. **Restore archive-only logging + 500 handler** — `web_app.log` + friendly error page that points at the log file. Matches the diagnostic patterns the updater already uses; valuable for the no-screenshare end-user. Carried in TODO Open questions.
4. **Updater throttle-on-failure refinement** — `_mark_checked()` in [src/updater.py](../src/updater.py) sets the 24h throttle after API success but before download attempt, so a download failure locks out retries for a day. Low priority.
5. **Archival-as-skill question (parked)** — whether to operationalise PROGRESS.md archival cadence as a Claude Code skill rather than a prose rule in this file.
6. **Stale-folder cleanup** — six candidates surveyed, totalling ~3.7 GB reclaim. Reported in 2026-05-13 PROGRESS entry; user can delete at their discretion. **Do NOT delete `/Volumes/Repos/SDGW 1914-19 2.5/`** — original CD contents.

## Carried items

- **`temp_support/` remnant — 2.3 GB, just the enriched DB now.** Scripts + schema + handover docs already extracted to `src/scripts/` / `src/sql/` (step 3 done); intermediate scrape artifacts and the .bak files deleted (~1.5 GB reclaimed). Only `temp_support/data/sd_2011.db` + 3 handover .md files remain. Gitignored as of this session — won't accidentally stage. Step 4 swaps the DB into `data/` and discards `temp_support/` entirely.
- **Two-repo state.** `origin` = `SDGW1914-1919-v2` (PUBLIC, active). `archive` = `SDGW1914-1919` (PRIVATE, legacy with unmerged spec/vendor work; **fetched read-only on 2026-05-13 evening 3 with sign-off** — diff characterised in PROGRESS, no merge performed). Do not merge from `archive` without explicit user sign-off.
- **DB distribution model.** DB ships as a separate versioned Release asset on tag `db-base`, not bundled in the .exe. Reader-only for now; annotation-DB split is deferred. Canonical SHA-256 of current `sd_2011.db` (CD baseline + reference enrichment, no CWGC): `945347461aef1d1c493d42a3adb1dfa85de3cb314ff1afd73556b99b7771ee1a`.
- **CD master.** `/Volumes/Repos/SDGW 1914-19 2.5/` — original Naval & Military Press CD-ROM contents (`setup.exe`, `database/`, `help/`, `runtime/`). Bedrock reproducible source; do **NOT** delete or move without backup. Loose `.mdb` copy also at `/Volumes/Repos/sd_2011.mdb`.
- **No Time Machine backup.** `tmutil destinationinfo` returns "No destinations configured". The DB has no automatic-backup safety net beyond the GitHub `db-base` Release. Worth flagging to the user before committing the post-CWGC enriched DB.
- **Code signing.** Explicitly out of scope (see [CLAUDE.md §6](../CLAUDE.md) hard constraint #9). SmartScreen blue dialog on first install is mitigated by an emailed screenshot showing **More info → Run anyway**. Subsequent auto-updates do not trigger SmartScreen.

## Decisions to date

Full ledger in [PROGRESS.md](PROGRESS.md). One-bite version:

- **Distribution model:** one URL, emailed once, that always resolves to the latest release. `https://github.com/eek2020/SDGW1914-1919-v2/releases/latest/download/SDGW-Setup.exe`.
- **Install path:** per-user install to `%LOCALAPPDATA%\SDGW` — **no UAC prompt**, no "this user / all users" dialog.
- **Auto-update:** silent, on-launch, throttled to once per 24h. Splash during download. Inno Setup spawned with `/SILENT /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS /NORESTART`. Fail-invisible — all exceptions swallowed; app launches normally on any error. Diagnostic file at `%LOCALAPPDATA%\SDGW\updater.log` (load-bearing for postmortem). **Validated end-to-end on 2026-05-13** (v0.2.6 → v0.2.7, hands-free, 71-second relaunch latency).
- **`AppMutex` is mandatory.** Inno Setup's `/CLOSEAPPLICATIONS` flag is a no-op without `AppMutex` in `installer.iss`. The running `SDGW.exe` must hold a named Windows kernel mutex (`SDGW1914-1919-AppMutex`, created in `launcher.py` at module load when `FROZEN and win32`) so the installer can identify and close it. Without this, "silent updates" silently failed to replace locked files. Discovered + fixed in v0.2.3 commit [`913c31a`](https://github.com/eek2020/SDGW1914-1919-v2/commit/913c31a).
- **`truststore` is mandatory.** Frozen PyInstaller Windows bundles can't verify the cert chain on GitHub's release-download CDN (`objects.githubusercontent.com`, the 302 target). The API call works (different chain); the download leg fails with `CERTIFICATE_VERIFY_FAILED`. `truststore.inject_into_ssl()` at the top of `src/updater.py` routes SSL trust through Windows' OS cert store (Crypt32) so the download succeeds. Chosen over `certifi` because the OS cert store is kept current by Windows Update — no forced release every time a CA chain rotates. Discovered + fixed in v0.2.5 commit [`a754eef`](https://github.com/eek2020/SDGW1914-1919-v2/commit/a754eef).
- **Paired `[Run]` entry in `installer.iss` is mandatory.** `/RESTARTAPPLICATIONS` passed to the installer is decorative — it only restarts apps registered with Windows Restart Manager, which the running SDGW.exe is not. Without an explicit `[Run]` entry that fires during silent installs, the silent auto-update path leaves the app closed (the elderly-friction problem). The fix: keep the existing `skipifsilent postinstall` entry for the first-time interactive install (shows the "Launch SDGW now" tickbox), and add a paired `skipifnotsilent nowait` entry that fires only during silent installs and reopens SDGW.exe immediately. Discovered + fixed in v0.2.7 commit [`bfd6bf8`](https://github.com/eek2020/SDGW1914-1919-v2/commit/bfd6bf8).
- **DB is separate from the app binary.** Shipped as `sd_2011.db.zip` on the `db-base` Release tag. CI fetches at build time so the .exe always carries a fresh DB without bloating the repo.
- **No code signing.** SmartScreen blue dialog mitigated by emailed screenshot on first install only; auto-updates inherit trust from the running app.
- **No new runtime dependencies.** Standard library + Flask + Jinja2 + Tom Select (vendored) + Lucide (vendored). No build step. No SPA framework.
- **Original historical records are immutable.** All user-contributed data goes into `record_annotations` / `record_images` / `annotation_history`.

## Resume prompt

Paste this as the first message in a new session:

```text
Continuing work on SDGW 1914-1919 (Soldiers Died in the Great War search app).

Read these in order before doing anything:
1. CLAUDE.md             (static project doc — tech stack, invariants, release flow)
2. _session/HANDOVER.md  (current state + active task + resume prompt)
3. _session/TODO.md      (active queue)
4. _session/PROGRESS.md  (decisions + log so far)

Then proceed with the active task in HANDOVER.md. Mini-passes only — one focused
unit of work, then check in. Update HANDOVER + PROGRESS + TODO at session end.
Author-approval per commit; don't auto-commit, don't auto-push.
```

## How to use these files

- **HANDOVER.md** — the snapshot. Reflects current state. Edit on session end.
- **TODO.md** — active queue. Tick items as done; add new ones as they emerge.
- **PROGRESS.md** — append-only log. Decisions, work done, open questions raised.

## Working agreement

- **Mini-passes.** One focused unit of work, then check in. Don't blast through multiple tasks in one run without an explicit handover gate between them.
- **Update handover at session end.** Refresh this file, append to [PROGRESS.md](PROGRESS.md), tick [TODO.md](TODO.md).
- **Ask before destructive actions.** Per the standing autonomy posture in [CLAUDE.md §Executing actions with care](../CLAUDE.md).
- **Git: author approval per action.** No commit, no push, no tag without explicit human approval each time. Trigger phrases: `commit` / `commit and push` / `ship it` / `tag it`.
- **Don't trade clean for fast silently.** Per the May 2026 CLAUDE.md addition: name the tradeoff out loud before taking a quick fix.

## End-of-session checklist

When wrapping up:

1. Update **Status** above.
2. Update **Active task** above.
3. Append a dated entry to [PROGRESS.md](PROGRESS.md) with: work done, decisions, open questions raised.
4. Tick / re-order [TODO.md](TODO.md).
5. If a meaningful direction changed, also reflect it in the Decisions block above.
