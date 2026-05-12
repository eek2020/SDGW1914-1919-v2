# Progress log

> Append-only. Most recent entries at the top. Each entry is a dated mini-pass retrospective: work done, decisions, open questions raised.
>
> Archival cadence: when this file passes ~800 lines, move the oldest dated entries to `PROGRESS-archive.md` at end-of-session housekeeping. Hard ceiling ~1500 lines. (Pattern borrowed from the EngineeringFramework repo — see HANDOVER.md.)

---

## 2026-05-12 — Adopted EngineeringFramework session-continuity pattern

**What changed.** Created `_session/HANDOVER.md`, `_session/TODO.md`, and this file. Added a short bootstrap pointer at the top of [CLAUDE.md](../CLAUDE.md) so a new session reads the static project doc first and then the session-state files.

**Why.** Previous sessions ended without a written hand-off, so each new conversation had to re-derive *"what was I doing?"* from `git log` and the user's memory. The EngineeringFramework repo at `/Users/eric/Downloads/EngineeringFramework/` already runs the pattern at scale — five mini-pass artefacts (HANDOVER / TODO / PROGRESS / CLAUDE / decisions/) used in concert to guide both the human and the assistant on next steps. The pattern is the *handover* not the methodology; that's why it's worth adopting here even though SDGW is a much smaller project than AIDE.

**Decisions taken.**

1. **Seed from current known state, not empty templates.** HANDOVER.md status line names Phase D as substantially complete with the auto-update validation as the load-bearing remaining proof point. TODO.md active queue carries the validation task + a no-op bump-tag supporting task. Parked items (USB installer bug, archive repo audit, archival-as-skill) lifted into TODO.md's *Next-up* section so they don't disappear.
2. **Mini-passes + end-of-session checklist as the discipline level.** Not the full ADR-promotion ceremony — SDGW is unlikely to keep accumulating structural decisions at the rate that justifies a `decisions/` folder. If a decision later survives a session and feels load-bearing (e.g. *"DB ships separately from the .exe"*), promote it to ADR then.
3. **Keep the existing CLAUDE.md as the static project doc.** Don't rewrite it into a session-state file. It already documents tech stack, invariants, file paths, release flow — that content is durable and answers different questions than HANDOVER/TODO/PROGRESS do. The bootstrap addition is a 5-line block at the top pointing to `_session/`, not a restructure.
4. **Author-approval per commit holds.** This file documents the pattern adoption but does not commit it — that's a separate explicit user instruction.

**Cross-document edits.** New file `_session/HANDOVER.md` (snapshot + resume prompt + end-of-session checklist). New file `_session/TODO.md` (active queue + next-up + open questions + Done). New file `_session/PROGRESS.md` (this file). [CLAUDE.md](../CLAUDE.md) gained a *Read on session start* block at the top pointing to the three `_session/` files. Auto-memory updated: new feedback memory `feedback_session_handover_pattern.md` so future cross-conversation sessions don't drift back to *"we don't need handover files."*

**Source.** Pattern adopted from `/Users/eric/Downloads/EngineeringFramework/` — specifically `CLAUDE.md` + `_session/HANDOVER.md` + `_session/TODO.md` + `_session/PROGRESS.md`. The EngineeringFramework repo uses it for assembling an AI-assisted delivery methodology (AIDE); SDGW is using it for ongoing maintenance + release work on a Flask + Windows-desktop app. Different scale, same handover mechanic.

**Open questions raised.** None — this is operational adoption, not a methodology decision.

**No methodology changes; no code changes; no commits.**
