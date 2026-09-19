# Grok Bot automation contract

Status: production scheduler as of 2026-09-19.

## Authority

- Repository/runtime authority wins over embedded routine prose.
- The live protected Grok Bot routine inventory is the clock authority for owner-facing scheduled office work.
- GitHub Actions remains the deterministic execution layer for machine workflows and canonical Gmail delivery.
- ChatGPT scheduler copies and Antigravity shadow sidecars are retired/disabled after cutover; they are not fallback schedulers.
- Never revive legacy recurring routines or create a second scheduler without Christian's explicit instruction.

## Protected routine set

- VelvetOS Integrity Guard — 01:45 daily
- Velvet Research Seat — 02:00 daily
- OpenPost Release Watch — 07:15 daily
- Velvet Morning Brief — 09:00 daily
- Morning Delivery Guard — 10:00 daily
- VelvetOS Office Loop — 10:30 and 18:30 daily
- Weekly Research Accountability — Friday 12:00

Timezone: Asia/Jerusalem.

### Integrity Guard execution semantics

The 01:45 Integrity Guard is a **finite single-pass audit**, not a continuous monitor. Each run must inspect the current inventory once, perform any immediate authorized repair, verify the resulting state once, notify only when required, and then terminate. It must not loop, poll, sleep, wait for future drift, or intentionally remain active after the pass is complete.

The protected set is **positive protection**, not deletion authority. The Guard may repair enabled-state, schedule, or prompt drift on the seven protected routines. Known legacy/deleted routines stay disabled, but an unknown or newly added routine that is outside the protected set must not be deleted, disabled, paused, or rewritten merely for being unlisted. Leave it untouched and surface the conflict unless Christian has explicitly authorized its removal or retirement.

## Owner email

Any owner email must use the current Morning Brief V10.3 rich RTL responsive/Outlook-safe system, the exact Visible Text gate where required, and only the canonical production path:

`packages/vfops/out/gmail-send-request.json`
→ `.github/workflows/gmail-brief-send.yml`
→ `packages/vfops/gmail_brief_request.py`

Interactive/connected Gmail is not a normal or fallback owner-delivery path. Require real sender success/message ID and safe request reset semantics.

## Migration evidence

Before cutover, Grok Bot completed a read-only shadow verification for all seven routines and reported 7/7 SHADOW_PASS against current repository authority, web research, live business-source reads, Instagram read evidence, V10.3 assets, and the canonical Gmail/GitHub path. The routines were then updated in place to production mode without manual execution, preserving identity, schedule, timezone, and enabled state.
