# Office v2 Phase 3A — Durable Execution Bake-off

Authority: START HERE Phase 3A. Baseline: `main@7fa9cb1f03da0876831c9d05efbfe44de2f8c280` after Phase 2 GREEN.

Status: **CONTRACT FROZEN / THREE ADMISSION SMOKES PASS / DESTRUCTIVE BAKE-OFF NOT YET RUN / NO WINNER / NO PRODUCTION AUTHORITY CHANGE**.

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
- `candidate-restate` — Restate 1.7.12, OCI digest pinned; isolated start/kill/restart smoke PASS with one documented node-incarnation observation.
- `candidate-hatchet` — Hatchet Lite 0.107.2, OCI digest pinned; isolated Postgres-only start/kill/restart smoke PASS with zero host ports.
- `candidate-temporal` — Temporal CLI 1.9.1 / embedded OSS Server 1.32.0, immutable runtime pinned; isolated engine-kill/restart smoke PASS with namespace persistence.

Credible reserve:
- `candidate-dbos` — DBOS Python 3.1.0, wheel SHA256 pinned. It briefly entered the active set after a Hatchet embedded-sidecar URL failure, then returned to reserve when the official `hatchet-lite` OCI artifact passed admission.

`durable-execution-shortlist-reopen-v0.json` preserves the temporary fail-closed decision; `durable-execution-shortlist-correction-v0.json` records the evidence-based correction. Exact artifact pins are in `runtime-pins-v0.json`. No `winner` is declared.

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

`durable-execution-admission-v0.json` is a research/admission receipt, not a benchmark result. Restate, Hatchet and Temporal now have immutable pins and have each passed isolated LAB admission smoke. DBOS remains a pinned credible reserve. A health probe, teardown path, zero production credentials and zero production authority remain mandatory; admission success is not a benchmark verdict.

## Evidence

Raw runtime benchmark evidence stays under:
`D:/Velvet/Artifacts/OfficeV2/phase3/evidence/2026-10-06/`.

Versioned definitions contain no secrets and no production payloads.
