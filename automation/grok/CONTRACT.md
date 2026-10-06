# Grok Bot automation contract

Status: production scheduler, **minimal recurring baseline approved 2026-10-06**.

## Current authority

- `automation/grok/current-baseline.json` and `automation/grok/manifest.json` are current scheduler policy.
- Repository/runtime authority wins over embedded routine prose.
- Only three Grok Bot routines are recurring and protected. Disabled/manual routines must not be revived by a guard, validator, migration helper, or historical Stage 7C wording.
- Provider evidence proves inventory/enabled/clock state only. It never proves prompt-body parity unless explicitly inspected.
- Unknown unlisted routines are not deletion-authorized merely because they are unlisted.
- Historical Stage 7C scheduler evidence is retained for provenance only and is not current desired-state authority.

## Current protected recurring set

Timezone: `Asia/Jerusalem`. Current protected count: **three**.

- `Cognee Memory Sync` — daily 06:30 (`cognee-memory-sync`)
- `VelvetOS Office Loop` — daily 18:30 (`velvetos-office-loop`)
- `Runtime Receipts Refresh` — daily 19:15 (`runtime-receipts-refresh`)

`Runtime Receipts Refresh` remains dependency-scoped evidence maintenance; receipt freshness is not a universal code/merge gate.

## Disabled / manual-only set

The following provider routines are intentionally disabled and may retain their saved prompts:

- `Velvet Morning Brief` — manual/event-driven only; no daily 09:00 clock.
- `Morning Delivery Guard` — retired.
- `Velvet Research Seat` — retired as a recurring clock; research is manual/event-driven when justified.
- `Weekly Research Accountability` — retired; no separate weekly research clock.
- `Cognee Stable Updates` — on-demand/upstream-review only.
- `VelvetOS Integrity Guard` — retired; there is no dedicated recurring routine manager/guard.
- `PC Offline Retry` — retired; no separate retry clock.

`OpenPost Release Watch` remains deleted/absent.

## Routine-manager role

A dedicated Grok Bot routine-manager role is not required. If the owning Grok agent must remain present as a provider shell so the three routines continue to exist, it stays dormant: no recurring governance work, no self-maintenance loop, and no owner notifications when nothing requires action.

## Morning Brief capability

Morning Green v3.1 remains the only current owner-email design; V10.3 remains available only for legacy/recovery surfaces. Morning Green is a valid capability, but it is not a recurring scheduler job. When explicitly triggered by an event or request, build the factual same-day artifact with:

`python3 scripts/vfops_loop.py brief --write --date <YYYY-MM-DD>`

Delivery claims still require real Gmail/provider evidence. A generated or backfilled artifact is not a delivery receipt.

## Research / upstream work

The former Research Seat may be invoked manually/event-driven when a real unresolved question, content need, or upstream decision justifies it. Broad daily research and a separate weekly accountability clock are retired. Upstream checks never auto-upgrade.

## Historical evidence

The 2026-09-19 through 2026-10-06 pre-reduction readbacks, `automation/grok/cognee-routines.json`, and Stage 7C acceptance artifacts remain historical evidence. They are not rewritten or back-filled and do not override the current three-routine baseline.
