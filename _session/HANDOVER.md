# Handover

> **Read first when resuming.** Update at the end of every session.

## Status

**Phases A–C complete. Phase D 95% signed off as of 2026-05-13 PM — silent install + file replacement + version flip is proven; one remaining issue (app doesn't auto-relaunch post-install) is fixed in `installer.iss` and awaits v0.2.7 validation.** All Phase-D plumbing shipped: PyInstaller spec, Inno Setup installer, CI workflow on tag push, silent on-launch updater, public download URL, and the three load-bearing fixes found and fixed across today's session — **AppMutex** (v0.2.3, closing the running app), **truststore SSL** (v0.2.5, downloading the new installer), and **paired `[Run]` with `skipifnotsilent`** (v0.2.7 pending, relaunching the app after silent install). v0.2.5 → v0.2.6 confirmed clean on the field machine: download 84,755,110 bytes in 6m52s, install 26s, footer reads v0.2.6 at full opacity.

Key recent commits: [`913c31a`](https://github.com/eek2020/SDGW1914-1919-v2/commit/913c31a) **AppMutex fix**, [`a754eef`](https://github.com/eek2020/SDGW1914-1919-v2/commit/a754eef) **truststore SSL fix**, [`40cb97c`](https://github.com/eek2020/SDGW1914-1919-v2/commit/40cb97c) `.version-tag` opacity bump (v0.2.6 visible signal), plus pending uncommitted `installer.iss` relaunch fix for v0.2.7.

Working tree currently dirty: `packaging/installer.iss` (the relaunch fix) + this file + `_session/PROGRESS.md` + `_session/TODO.md` + auto-memory `project_auto_update.md`, all reflecting the v0.2.6 confirmation and the relaunch-gap diagnosis. Pending commit + push + v0.2.7 tag.

## Active task

**Validate the post-install relaunch on the user's Windows machine via v0.2.7.** The silent update mechanism itself is proven. After v0.2.7 ships, the test is: launch v0.2.6 → splash → install → expect the app to reopen itself **without user intervention** with footer reading v0.2.7. If confirmed, Phase D is fully signed off and the Active task retires.

## Next-up candidates

Picked by user direction. None block the others.

1. **Audit the `archive` remote for unmerged work** — older Inno Setup scripts and vendored assets that were done independently. Deferred per CLAUDE.md §11; only revisit with explicit user sign-off because the two histories have diverged.
2. **Annotation UI integration on the detail page** is partial (backend complete). Promote when prioritised; do as its own mini-pass.
3. **Performance debt items** carried in TODO.md *Open questions* — detail-page query count, `fuzzy_suggest` caching, CI test wiring, fixture-based test isolation. Not blocking distribution; pick when feature work quiets.
4. **Archival-as-skill question (parked)** — whether to operationalise PROGRESS.md archival cadence as a Claude Code skill rather than a prose rule in this file. Decide if archival passes start firing often enough to be friction.

## Carried items

- **Two-repo state.** `origin` = `SDGW1914-1919-v2` (PUBLIC, active). `archive` = `SDGW1914-1919` (PRIVATE, legacy with unmerged spec/vendor work). Do not fetch from `archive` without explicit user sign-off.
- **DB distribution model.** DB ships as a separate versioned Release asset on tag `db-base`, not bundled in the .exe. Reader-only for now; annotation-DB split is deferred.
- **Code signing.** Explicitly out of scope (see [CLAUDE.md §6](../CLAUDE.md) hard constraint #9). SmartScreen blue dialog on first install is mitigated by an emailed screenshot showing **More info → Run anyway**. Subsequent auto-updates do not trigger SmartScreen.

## Decisions to date

Full ledger in [PROGRESS.md](PROGRESS.md). One-bite version:

- **Distribution model:** one URL, emailed once, that always resolves to the latest release. `https://github.com/eek2020/SDGW1914-1919-v2/releases/latest/download/SDGW-Setup.exe`.
- **Install path:** per-user install to `%LOCALAPPDATA%\SDGW` — **no UAC prompt**, no "this user / all users" dialog.
- **Auto-update:** silent, on-launch, throttled to once per 24h. Splash during download. Inno Setup spawned with `/SILENT /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS /NORESTART`. Fail-invisible — all exceptions swallowed; app launches normally on any error. Diagnostic file at `%LOCALAPPDATA%\SDGW\updater.log`. Field validation in flight (v0.2.5 → v0.2.6) as of 2026-05-13 PM.
- **`AppMutex` is mandatory.** Inno Setup's `/CLOSEAPPLICATIONS` flag is a no-op without `AppMutex` in `installer.iss`. The running `SDGW.exe` must hold a named Windows kernel mutex (`SDGW1914-1919-AppMutex`, created in `launcher.py` at module load when `FROZEN and win32`) so the installer can identify and close it. Without this, "silent updates" silently failed to replace locked files. Discovered + fixed in v0.2.3 commit [`913c31a`](https://github.com/eek2020/SDGW1914-1919-v2/commit/913c31a).
- **`truststore` is mandatory.** Frozen PyInstaller Windows bundles can't verify the cert chain on GitHub's release-download CDN (`objects.githubusercontent.com`, the 302 target). The API call works (different chain); the download leg fails with `CERTIFICATE_VERIFY_FAILED`. `truststore.inject_into_ssl()` at the top of `src/updater.py` routes SSL trust through Windows' OS cert store (Crypt32) so the download succeeds. Chosen over `certifi` because the OS cert store is kept current by Windows Update — no forced release every time a CA chain rotates. Discovered + fixed in v0.2.5 commit [`a754eef`](https://github.com/eek2020/SDGW1914-1919-v2/commit/a754eef).
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
