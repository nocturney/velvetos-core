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

## Pending owner-requested Cognee cutover

Christian requested on 2026-09-23 that `Cognee Memory Sync` (daily 06:30) and `Cognee Stable Updates` (Monday 10:00) move from ChatGPT scheduling to Grok Bot. The exact prompts, cadence, timezone and ChatGPT automation IDs are locked in `automation/grok/cognee-routines.json`.

This is a fail-closed provider cutover: the two ChatGPT copies remain enabled until the live Grok Bot inventory is read back and proves that both routines exist, are enabled, and match the locked cadence/prompt intent. Only then may those two ChatGPT automation IDs be disabled. Until that readback exists, these two entries are pending provider activation and are **not** counted as live protected Grok routines. Do not infer live Grok creation from Git/manifest changes alone.

### Integrity Guard execution semantics

The 01:45 Integrity Guard is a **finite single-pass audit**, not a continuous monitor. Each run must inspect the current inventory once, perform any immediate authorized repair, verify the resulting state once, notify only when required, and then terminate. It must not loop, poll, sleep, wait for future drift, or intentionally remain active after the pass is complete.

The protected set is **positive protection**, not deletion authority. The Guard may repair enabled-state, schedule, or prompt drift on the seven protected routines. Known legacy/deleted routines stay disabled, but an unknown or newly added routine that is outside the protected set must not be deleted, disabled, paused, or rewritten merely for being unlisted. Leave it untouched and surface the conflict unless Christian has explicitly authorized its removal or retirement.

## Owner email

The 09:00 owner brief must use Morning Green v3.1, the current canonical RTL/Desktop-first responsive owner-email design. V10.3 remains available only for legacy/recovery surfaces that explicitly require it. Owner-visible prose still passes the exact Visible Text gate where required, and delivery uses only the canonical production path:

`packages/vfops/out/gmail-send-request.json`
→ `.github/workflows/gmail-brief-send.yml`
→ `packages/vfops/gmail_brief_request.py`

Interactive/connected Gmail is not a normal or fallback owner-delivery path. Require real sender success/message ID and safe request reset semantics.

## Migration evidence

Before the scheduler cutover, Grok Bot completed a read-only shadow verification for all seven routines and reported 7/7 SHADOW_PASS against current repository authority, web research, live business-source reads, Instagram read evidence, the then-current V10.3 assets, and the canonical Gmail/GitHub path. The routines were then updated in place to production mode without manual execution, preserving identity, schedule, timezone, and enabled state.

On 2026-09-23, owner-email authority moved from V10.3 to Morning Green v3.1 after OpenPost schedule read, thumbnail materialization, renderer/sensor checks, Apps Script bridge v5 health, canonical GitHub/Gmail send success, Gmail message ID, and Gmail readback with six CID images all passed. The schedule, routine identity, timezone and seven-routine protected set did not change.
