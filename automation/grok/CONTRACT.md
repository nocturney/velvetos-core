# Grok Bot automation contract

Status: **recurring Grok scheduler retired by owner on 2026-10-06**.

## Current authority

- Owner-facing recurring scheduler authority is `chatgpt-automations`.
- Grok Bot has **zero enabled recurring routines** from the VelvetOS set.
- Grok Bot remains available on demand as a tool/agent, not as scheduler, routine manager, integrity guard, or retry daemon.
- `automation/grok/current-baseline.json` is the current scheduler policy. Historical Stage 7C/Grok readbacks are provenance only.
- Never fabricate a ChatGPT provider receipt. The repository records declarative authority; live execution is verified when a real run/effect requires it.
- Unknown/unlisted provider routines are never deletion-authorized merely because they are not in the current set.

## Current ChatGPT schedules

- `VelvetOS Office Loop` — daily 18:30 Asia/Jerusalem.
- `Cognee Memory Sync` — once daily, flexible around 11:30 Asia/Jerusalem.
- `Runtime Receipts Refresh` — daily 19:15 Asia/Jerusalem.

`Velvet Morning Brief` and `Velvet Research Seat` are manual/event-driven capabilities, not standing clocks.

## Retired Grok clocks

Morning Brief, Morning Delivery Guard, Research Seat, Weekly Research Accountability, Cognee Stable Updates, Cognee Memory Sync, Office Loop, Runtime Receipts Refresh, Integrity Guard and PC Offline Retry are disabled in Grok. OpenPost Release Watch remains absent/deleted.

Provider retirement evidence: `automation/grok/provider-readback-2026-10-06-retired.json`.

## Execution semantics

Retry/backoff/reconciliation belong to durable workflow execution. Runtime evidence is dependency-scoped and created from real observations only. A health check that cannot affect production or a pending owner decision does not justify an owner notification.

The dedicated Grok automation-manager chat may remain dormant for historical audit context only. It has no recurring governance or notification duty.
