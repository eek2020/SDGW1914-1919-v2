# Handover

> **Read first when resuming.** Update at the end of every session.

## Status

**Phases A–C complete. Phase D (Windows desktop `.exe`) substantially complete — PyInstaller spec, Inno Setup installer, GitHub Actions release workflow, silent auto-updater, and a public download URL are all shipped.** Active focus: validating the silent auto-update path end-to-end on a real Windows machine. Recent commits in support of this are [`5efb7bd`](https://github.com/eek2020/SDGW1914-1919-v2/commit/5efb7bd) (silent auto-updater), [`55ad769`](https://github.com/eek2020/SDGW1914-1919-v2/commit/55ad769) (version visible in the footer so the user sees `0.X.Y` change after an update), and [`4170850`](https://github.com/eek2020/SDGW1914-1919-v2/commit/4170850) (file logging in the updater to `%LOCALAPPDATA%\SDGW\updater.log` for failure diagnosis).

Working tree is clean on `main`.

## Active task

**Validate the silent auto-update path end-to-end on the user's Windows machine.**

Why this is the load-bearing thing: the whole distribution model (per-user install, no UAC, silent updates) depends on the auto-updater working without any user-visible failure mode. Until we've watched it succeed at least once in the field, the "email one URL forever" promise is unproven.

What "done" looks like:

1. Newer release tag exists on `eek2020/SDGW1914-1919-v2` than the version installed on the target machine.
2. Target machine: delete `%LOCALAPPDATA%\SDGW\last_update_check` to bypass the 24h throttle.
3. Launch SDGW.
4. Splash appears → installer downloads → app relaunches.
5. Footer shows the new version string.
6. `%LOCALAPPDATA%\SDGW\updater.log` contains the full decision trail with no swallowed exceptions.

If any step fails: read the updater.log first (`src/updater.py` logs at every decision point — throttle, API call, version compare, asset lookup, download, spawn, splash).

## Next-up candidates

Picked by user direction. None block the others.

1. **Cut a bump tag to give the updater something to update *to*** — e.g. `v0.X.Y+1` with a trivial visible change so the user can see the version flip in the footer. Manual `git tag` + `git push` (asks for confirmation per the standing autonomy posture). CI publishes `SDGW-Setup.exe` to `releases/latest/download/`.
2. **Fix the May 2026 USB build installer bug** (see [Carried items](#carried-items)) — broken PowerShell installer with a wrong source-folder path. Blocks any further USB handover. Lower priority now that the .exe + auto-update path is the primary distribution channel, but still real debt.
3. **Audit the `archive` remote for unmerged work** — older Inno Setup scripts, USB-build helpers, and vendored assets that were done independently. Deferred per CLAUDE.md §11; only revisit with explicit user sign-off because the two histories have diverged.
4. **Archival-as-skill question (parked)** — whether to operationalise PROGRESS.md archival cadence as a Claude Code skill rather than a prose rule in this file. Decide if archival passes start firing often enough to be friction.

## Carried items

- **USB installer bug.** May 2026 USB build ships a PowerShell installer with a wrong source-folder path. Needs a fix before any further Windows USB handover. Not blocking the .exe path.
- **Two-repo state.** `origin` = `SDGW1914-1919-v2` (PUBLIC, active). `archive` = `SDGW1914-1919` (PRIVATE, legacy with unmerged spec/vendor/USB work). Do not fetch from `archive` without explicit user sign-off.
- **DB distribution model.** DB ships as a separate versioned Release asset on tag `db-base`, not bundled in the .exe. Reader-only for now; annotation-DB split is deferred.
- **Code signing.** Explicitly out of scope (see [CLAUDE.md §6](../CLAUDE.md) hard constraint #9). SmartScreen blue dialog on first install is mitigated by an emailed screenshot showing **More info → Run anyway**. Subsequent auto-updates do not trigger SmartScreen.

## Decisions to date

Full ledger in [PROGRESS.md](PROGRESS.md). One-bite version:

- **Distribution model:** one URL, emailed once, that always resolves to the latest release. `https://github.com/eek2020/SDGW1914-1919-v2/releases/latest/download/SDGW-Setup.exe`.
- **Install path:** per-user install to `%LOCALAPPDATA%\SDGW` — **no UAC prompt**, no "this user / all users" dialog.
- **Auto-update:** silent, on-launch, throttled to once per 24h. Splash during download. Inno Setup spawned with `/SILENT /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS /NORESTART`. Fail-invisible — all exceptions swallowed; app launches normally on any error. Diagnostic file at `%LOCALAPPDATA%\SDGW\updater.log`.
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
