# Office v2 Phase 3A implementation spec

## Goal

Choose the smallest reliable durable-execution spine using one vendor-neutral destructive contract.

## Required proof

1. Exactly 20 correlated workflow steps.
2. Worker kill/recovery.
3. Engine kill/recovery.
4. Duplicate webhook and idempotency proof.
5. Long approval wait and resume.
6. Explicit cancel and retry.
7. Eligible work movement with ownership trace.
8. Unknown simulated effect outcome reconciled before retry.
9. Operator inspect/replay.
10. Backup/upgrade/rollback assessment and resource/cost capture.

## Benchmark set

Incumbent + Restate + Hatchet + Temporal. DBOS 3.1.0 is a credible reserve, not a fourth active challenger. No winner exists at entry.

## Safety

All challenger runtimes remain authority=NONE, LAB-only, no production credentials, loopback/bounded storage, and simulated effect surface only.
