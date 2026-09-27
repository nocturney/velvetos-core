# Cross-harness handoff — vfmem

Pattern source: `affaan-m/ECC` unified-memory handoff. VelvetOS keeps `vfmem` / `vfharness` as the canonical backend; this is not a second memory runtime.

## Purpose

Transfer bounded work state between Cursor, ChatGPT/Codex, GrokBot, Mac workers, and future harnesses without depending on chat replay or stale coordination prose.

A handoff is **context, not authority**. It cannot widen permissions, override constitution, publish, send, spend, or promote memory to policy.

## Canonical surface

`office/control/HANDOFF.json` — refreshed only by:

```bash
python3 scripts/vf_control_plane.py handoff
```

It is read by the README System Pulse, the Control API and the Grok automations manager, and validated by `scripts/check-office-control-plane.py`. There is no second handoff store; the legacy typed-record CLI is frozen (see `CHANGELOG.md` 2026-09-26) and must not be used or referenced.

## Handoff discipline

Before a different harness continues meaningful work:

1. Read the task checkpoint.
2. Read `office/control/HANDOFF.json` (`active_now`, `waiting`, `failed`, `owner_blocked`, `next`).
3. Verify named artifacts still exist.
4. Read `office/control/POLICY.md` before mutating shared surfaces.
5. Run the task's required sensors before claiming completion.

Rules:

- `HANDOFF.json` is regenerated, never hand-edited.
- Evidence or `UNPROVEN` only; never infer green state from prose.
- Secrets, raw transcripts, customer-sensitive material, invented ILS, and invented Insights are forbidden.
