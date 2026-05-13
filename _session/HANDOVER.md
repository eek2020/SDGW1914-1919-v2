# Handover

> **Read first when resuming.** Update at the end of every session.

## Status

**Phases A–D complete. Silent auto-update path proven hands-free end-to-end on 2026-05-13.** Three load-bearing fixes shipped that day, each diagnosed from the live `updater.log` rather than assumed: **AppMutex** (v0.2.3, closing the running app), **truststore SSL** (v0.2.5, downloading the new installer), and **paired `[Run]` with `skipifnotsilent`** (v0.2.7, relaunching the app after silent install). v0.2.6 → v0.2.7 validated: download 84,792,335 bytes in 5m27s, install 26s, **app auto-relaunched 71s after install completion** with no human interaction.

**Most recent session (2026-05-13, evening 3):** Audit of stale SDGW-related folders across `/Users/eric/` and `/Volumes/Repos`/`/Volumes/SDGW`. Read-only fetched the `archive` remote (per CLAUDE.md §11 sign-off) and characterised the diff with origin — five things archive had that origin lost (notable: app-level file logging + friendly 500 handler; full audit in PROGRESS). DB integrity sweep confirmed all four reachable copies of `sd_2011.db` are byte-identical (`945347461aef…`), with the canonical version stored on the `db-base` GitHub Release (uploaded 2026-05-12). User identified that this DB is missing a CWGC enrichment layer that previously existed in the running app — agreed to budget for re-acquisition (5-phase plan in TODO and below) rather than continue searching for the lost copy. Original Naval & Military Press CD contents preserved at `/Volumes/Repos/SDGW 1914-19 2.5/` (do NOT delete).

**Important lesson saved this session.** Saved feedback memory `feedback_no_absence_claims.md` after I overclaimed "the DB never had CWGC scraping" based on a partial search. User's firsthand recollection (they had demonstrated CWGC data in the UI) outranks my partial inspection. New rule: state scope of search precisely, never assert "never had", treat user recollection as a lead worth pursuing rather than a mistake to correct.

Key recent commits: [`ddc0b0c`](https://github.com/eek2020/SDGW1914-1919-v2/commit/ddc0b0c) **CI actions Node 24 bump**, [`913c31a`](https://github.com/eek2020/SDGW1914-1919-v2/commit/913c31a) AppMutex fix, [`a754eef`](https://github.com/eek2020/SDGW1914-1919-v2/commit/a754eef) truststore SSL fix, [`bfd6bf8`](https://github.com/eek2020/SDGW1914-1919-v2/commit/bfd6bf8) paired `[Run]` relaunch fix.

Working tree currently dirty with session-wrap doc updates (this file, [_session/PROGRESS.md](PROGRESS.md), [_session/TODO.md](TODO.md)). `data/sd_2011.db` exists locally (extracted from `db-base` zip; gitignored, useful for next-session script work). Pending commit + push.

## Active task

**Phase 1 of the CWGC rebuild plan: investigation & access.** Find out how CWGC data is accessible today (public API, scraping ToS/robots, cached datasets), what the rate limits are, and whether bulk download is permitted. Output is a written assessment with tradeoffs — no code yet. See full 5-phase plan below; each phase is its own session per the mini-pass agreement.

## CWGC rebuild plan (5 phases, sign-off between each)

| Phase | Scope | Notes |
| --- | --- | --- |
| **1 — Investigation & access** | CWGC public access today (API/scrape/cached dataset), ToS/robots, rate limits. | **NEXT — start here.** No code, just an assessment doc. |
| 2 — Schema & storage design | New `cwgc_records` table with FK to `soldiers`/`officers`. Preserves CD immutability per [CLAUDE.md §6.1](../CLAUDE.md). Match key: surname + initials/christian_names + service_number + regiment_id + death_date. Fields: `casualty_id`, `cemetery_or_memorial`, `grave_reference`, `country_buried`, `age_at_death`, `next_of_kin`, `additional_info`, `cwgc_url`, `match_confidence`, `last_fetched_at`. | Schema-only; no fetch yet. |
| 3 — Run enrichment & validate | Execute against all 703,806 records. At 1 req/s = 8+ days runtime. Background-resumable design required. Spot-check matches against soldiers user can identify. | Long-running; needs idempotent `src/scripts/cwgc_enrich.py`. |
| 4 — UI integration | Detail page: new "Commonwealth War Graves" section when CWGC record present (cemetery, grave ref, age, kin, link out to cwgc.org). New "Data sources" diff panel showing CD-vs-CWGC discrepancies — the section user remembers. Optional facets: has-CWGC, cemetery, country buried. | The user-visible payoff phase. |
| 5 — Distribution | Re-upload enriched DB via `packaging/upload-db-base.sh`. Version bump. Silent auto-updater carries it to the end user. | Final ship. |

## Next-up candidates (paused — promote after CWGC work, or interleave by user direction)

None block the others. The CWGC rebuild is the active priority; everything below is parked.

1. **Annotation UI integration on the detail page** is partial (backend complete). Promote when prioritised; do as its own mini-pass.
2. **Performance debt items** carried in TODO.md *Open questions* — detail-page query count, `fuzzy_suggest` caching, CI test wiring, fixture-based test isolation. Not blocking distribution.
3. **Restore archive-only logging + 500 handler** — `web_app.log` + friendly error page that points at the log file. Matches the diagnostic patterns the updater already uses; valuable for the no-screenshare end-user. Carried in TODO Open questions.
4. **Updater throttle-on-failure refinement** — `_mark_checked()` in [src/updater.py](../src/updater.py) sets the 24h throttle after API success but before download attempt, so a download failure locks out retries for a day. Low priority.
5. **Archival-as-skill question (parked)** — whether to operationalise PROGRESS.md archival cadence as a Claude Code skill rather than a prose rule in this file.
6. **Stale-folder cleanup** — six candidates surveyed, totalling ~3.7 GB reclaim. Reported in 2026-05-13 PROGRESS entry; user can delete at their discretion. **Do NOT delete `/Volumes/Repos/SDGW 1914-19 2.5/`** — original CD contents.

## Carried items

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
