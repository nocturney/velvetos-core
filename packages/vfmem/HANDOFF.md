# Cross-harness handoff — vfmem

Pattern source: `affaan-m/ECC` unified-memory handoff. VelvetOS keeps `vfmem` / `vfharness` as the canonical backend; this is not a second memory runtime.

## Purpose

Transfer bounded work state between Cursor, ChatGPT/Codex, GrokBot, Mac workers, and future harnesses without depending on chat replay or stale coordination prose.

A handoff is **context, not authority**. It cannot widen permissions, override constitution, publish, send, spend, or promote memory to policy.

## Canonical file

Store handoffs as JSON under:

`packages/vfharness/state/handoffs/<handoff_id>.json`

Required fields:

```json
{
  "schema": "vf.handoff.v1",
  "handoff_id": "handoff-2026-09-13-example",
  "task_id": "task-id",
  "source_harness": "codex",
  "target_harness": "cursor",
  "status": "offered",
  "trust": "unreviewed",
  "summary": "bounded state needed to continue",
  "artifacts": [],
  "links": [],
  "supersedes": null,
  "verification": "named sensor / receipt / UNPROVEN",
  "created_at": "2026-09-13T00:00:00+03:00",
  "acknowledged_at": null
}
```

## States

`offered -> acknowledged -> consumed`

Alternative terminal states: `rejected`, `superseded`.

Rules:

- `acknowledged` requires `acknowledged_at`.
- `consumed` requires prior acknowledgement.
- `supersedes` may reference only another handoff ID; old records are not deleted.
- `links` are references only; missing links are a doctor failure.
- `verification` must be evidence or `UNPROVEN`; never infer green state from prose.
- Secrets, raw transcripts, customer-sensitive material, invented ILS, and invented Insights are forbidden.

## Handoff discipline

Before a different harness continues meaningful work:

1. Read the task checkpoint.
2. Read the newest matching handoff targeted to this harness.
3. Verify named artifacts still exist.
4. ACK the handoff before mutating shared surfaces.
5. Run the task's required sensors before claiming completion.

## Doctor

Run:

```bash
python3 scripts/vf_handoff.py doctor
python3 scripts/check-vf-handoff.py
```

The doctor reports duplicate IDs, malformed state, missing links, invalid transitions, stale unacknowledged handoffs, and `consumed` records without acknowledgement evidence.
