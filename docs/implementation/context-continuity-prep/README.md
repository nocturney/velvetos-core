# Context Continuity prep

Status: **NON_NORMATIVE_REFORM_PREPARATION**  
Authority: **none**  
Runtime: **disabled**  
Production integration: **none**  
Prepared against `main` `dfd699dcee63d5175f03ae3312fbb89992ea78ca`.

## Why this exists

VelvetOS already has the continuity primitives we want to preserve:

- `packages/vfharness/LOOP.md` is the only global execution-loop authority.
- `packages/vfharness/templates/checkpoint.schema.json` is canonical for bounded task execution/resume state.
- `office/control/HANDOFF.json` is the cross-harness continuation/index projection.
- `packages/vfmem/HANDOFF.md` explicitly forbids a second memory runtime/store.
- `packages/vfharness/playbooks/context-thrift.md` already defines CCR (Compress · Cache · Retrieve) and phase-boundary compaction as a pattern.
- Reform v2 Stage 7A classifies current state, evidence, authorization decisions and audit history; compaction must respect those roles.

This prep package turns those existing rules into an implementation-ready contract for a future **verified automatic continuation runtime**. It deliberately does **not** add runtime hooks, a daemon, a proxy, a database, a scheduler, a second orchestrator, or external-effect authority.

## Draft artifacts

| File | Purpose |
|---|---|
| `context-continuity-contract-v0.json` | invariants and canonical dependencies |
| `state-manifest-v0.schema.json` | rebuildable, non-authoritative continuation projection |
| `compaction-policy-v0.json` | eligible triggers, hard blocks, recovery order and rollout |
| `provider-interface-v0.md` | provider-neutral adapter contract |
| `acceptance-vectors-v0.json` | regression scenarios for future implementation |
| `integration-plan-v0.md` | bounded path from shadow mode to production |

## Non-negotiable architecture

```text
existing canonical sources
        |
        +--> task checkpoint (task execution SoT)
        +--> HANDOFF.json (cross-harness continuation projection)
        +--> domain state / evidence / exact-action receipts
        |
        v
derived continuation manifest
        |
        v
provider compactor (optional)
        |
        v
post-compaction verifier
        |
        +-- PASS --> continue with smaller working set
        |
        +-- FAIL/UNPROVEN --> reject compacted result and recover from canonical sources
```

The manifest and compacted summary are disposable. They never replace the checkpoint, HANDOFF, policy registry, domain state, receipts or evidence.

## Integration boundary

No current Reform v2 behavior is changed by this branch. After the reform closes, integration should be a small extension of `vfharness`, behind feature flags and a kill switch, first in shadow mode.

## Acceptance philosophy

The question is not whether a compacted summary reads well. The question is whether the next agent can execute the **same correct next step**, with the same blockers, IDs, evidence and authority boundaries, without chat replay.

## Explicitly out of scope for prep

- choosing production token thresholds;
- enabling OpenAI/other provider compaction;
- modifying `LOOP.md`, `HANDOFF.json`, checkpoint schema or policy registry;
- writing raw transcripts to durable memory;
- enabling a new Work Ledger store;
- merging this branch before the active Reform v2 integration point is reviewed.
