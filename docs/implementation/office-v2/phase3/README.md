# Office v2 Phase 3A — Durable Execution Bake-off

Authority: START HERE Phase 3A. Baseline: `main@7fa9cb1f03da0876831c9d05efbfe44de2f8c280` after Phase 2 GREEN.

Status: **CONTRACT + ADMISSION FREEZE IN PROGRESS / NO WINNER / NO PRODUCTION AUTHORITY CHANGE**.

## Objective

Choose the smallest reliable durable-execution spine before domain migrations. Phase 3A compares the current VelvetOS execution composition against at most three serious challengers under one destructive, vendor-neutral contract.

## Frozen safety rules

- Production work retains priority and existing production authority.
- LAB/SHADOW candidates receive no production credentials and no production writer role.
- A failed incumbent never auto-promotes a challenger.
- The benchmark effect surface is simulated/local. No real production mutation is used to prove unknown-outcome recovery.
- Every candidate uses the same 20-step destructive fixture and standard Phase 2 scorecard.
- A product is not a winner because it installs, starts, or performs well on a subset of the contract.
- Promotion requires an explicit winner/fallback record after evidence, rollback and operator-inspection gates pass.

## Benchmark set

Incumbent:
- `incumbent-current-durable-execution`.

LAB-admission shortlist:
- `candidate-restate` — target Restate 1.7.12.
- `candidate-hatchet` — target Hatchet 0.107.2.
- `candidate-temporal` — target Temporal server 1.32.0.

Credible reserve:
- `candidate-dbos` — DBOS Python 3.1.0. Fresh September evidence is recorded, but the candidate remains reserve so the Phase 2 default cap of three challengers is preserved. It may replace a shortlisted candidate if admission or benchmark evidence materially justifies reopening.

No `winner` is declared.

## Destructive fixture

`durable-execution-destructive-v0.json` is exactly 20 semantic steps and must exercise:
- worker death and recovery;
- engine death and recovery;
- duplicate webhook/idempotency;
- long approval wait;
- cancel;
- retry;
- resume;
- eligible work movement;
- unknown external-effect outcome followed by reconciliation;
- operator inspect/replay.

The fixture succeeds only when no completed external effect is duplicated, recovery is deterministic enough for the contract, operator inspection/replay works, and backup/upgrade/rollback is acceptable.

## Admission boundary

`durable-execution-admission-v0.json` is a research/admission receipt, not an installation receipt. A candidate may enter LAB only after its immutable runtime artifact is resolved, network/storage are bounded to OfficeV2-Lab, a health probe and teardown path exist, and the runtime has zero production credentials/authority.

## Evidence

Raw runtime benchmark evidence stays under:
`D:/Velvet/Artifacts/OfficeV2/phase3/evidence/2026-10-06/`.

Versioned definitions contain no secrets and no production payloads.
