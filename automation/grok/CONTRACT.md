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
- Cognee Memory Sync — 06:30 daily
- Velvet Morning Brief — 09:00 daily
- Morning Delivery Guard — 10:00 daily
- Cognee Stable Updates — Monday 10:00
- VelvetOS Office Loop — 10:30 and 18:30 daily
- Weekly Research Accountability — Friday 12:00

Timezone: Asia/Jerusalem.

## Cognee scheduler cutover — live verified

On 2026-09-23, Christian moved `Cognee Memory Sync` (daily 06:30) and `Cognee Stable Updates` (Monday 10:00) from ChatGPT scheduling to Grok Bot. Provider readback verified both Grok routines live, enabled, in `Asia/Jerusalem`, with the canonical schedules and instruction intent locked in `automation/grok/cognee-routines.json`. Only after that readback were the two matching ChatGPT automation copies disabled.

The live provider IDs are `cognee-memory-sync` and `cognee-stable-updates`. `VelvetOS Integrity Guard` was then updated in place and read back as enabled at daily 01:45 with a eight-routine protected inventory. Git/manifest state alone is never provider proof; the verified readback is recorded in `automation/grok/cognee-routines.json`.

### Integrity Guard execution semantics

The 01:45 Integrity Guard is a **finite single-pass audit**, not a continuous monitor. Each run must inspect the current inventory once, perform any immediate authorized repair, verify the resulting state once, notify only when required, and then terminate. It must not loop, poll, sleep, wait for future drift, or intentionally remain active after the pass is complete.

The protected set is **positive protection**, not deletion authority. The Guard may repair enabled-state, schedule, or prompt drift on the eight protected routines. Known legacy/deleted routines stay disabled, but an unknown or newly added routine that is outside the protected set must not be deleted, disabled, paused, or rewritten merely for being unlisted. Leave it untouched and surface the conflict unless Christian has explicitly authorized its removal or retirement.

## Owner email

The 09:00 owner brief must use Morning Green v3.1, the current canonical RTL/Desktop-first responsive owner-email design. V10.3 remains available only for legacy/recovery surfaces that explicitly require it. Owner-visible prose still passes the exact Visible Text gate where required, and delivery uses only the canonical production path:

`packages/vfops/out/gmail-send-request.json`
→ `.github/workflows/gmail-brief-send.yml`
→ `packages/vfops/gmail_brief_request.py`

Interactive/connected Gmail is not a normal or fallback owner-delivery path. Require real sender success/message ID and safe request reset semantics.

## Migration evidence

Before the scheduler cutover, Grok Bot completed a read-only shadow verification for all seven routines and reported 7/7 SHADOW_PASS against current repository authority, web research, live business-source reads, Instagram read evidence, the then-current V10.3 assets, and the canonical Gmail/GitHub path. The routines were then updated in place to production mode without manual execution, preserving identity, schedule, timezone, and enabled state.

On 2026-09-23, owner-email authority moved from V10.3 to Morning Green v3.1 after OpenPost schedule read, thumbnail materialization, renderer/sensor checks, Apps Script bridge v5 health, canonical GitHub/Gmail send success, Gmail message ID, and Gmail readback with six CID images all passed. At that point the schedule, routine identity, timezone and eight-routine protected set did not change.

Later on 2026-09-23, live Grok readback verified `Cognee Memory Sync` (`cognee-memory-sync`, daily 06:30) and `Cognee Stable Updates` (`cognee-stable-updates`, Monday 10:00) as enabled in `Asia/Jerusalem`; only then were the corresponding ChatGPT copies disabled. A second provider readback verified `VelvetOS Integrity Guard` (`velvetos-integrity-guard`) still enabled at daily 01:45 and protecting the eight-routine set without changing any other routine.


## OpenPost retirement directive — 2026-09-26

`OpenPost Release Watch` is retired and must be disabled in the live Grok scheduler. It is not part of the protected set. The desired protected inventory is eight routines. Git state is desired authority only; a provider read-back is still required before claiming the live Grok routine is disabled.

The 09:00 Morning Brief must read scheduled Instagram state from the Cloudflare Instagram Publisher, not OpenPost.

## Live provider re-read — 2026-09-27

A fresh read-only inventory observation was taken from the already signed-in Grok Bot 0.59.1 renderer through its existing loopback DevTools surface, without sending a model prompt. The provider exposed the exact eight protected routine IDs, all eight enabled, with effective schedule displays matching this contract in an `Asia/Jerusalem` renderer.

The same live readback found the retired `OpenPost Release Watch` still enabled at 07:15 despite the 2026-09-26 retirement directive. That already-authorized drift was repaired in place by disabling only that routine. The provider write completed, and the post-write provider state read back `aria-checked=false` / `Resume OpenPost Release Watch`; all eight protected routines remained enabled and unchanged. Evidence is recorded in `automation/grok/provider-readback-2026-09-27.json`.

This readback proves current provider inventory, enabled state, effective schedule display and renderer timezone. It does **not** claim that every routine prompt body was re-read or byte-compared on 2026-09-27.
