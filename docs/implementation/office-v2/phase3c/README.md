# Office v2 Phase 3C - Model Gateway, independent acceleration lane

Status: **CONTRACT PREP ONLY**. No model gateway was installed, admitted to LAB, compared in a live bake-off or promoted. No production authority, credentials, payment or routing changes.

## Why this lane starts now

Phase 3A Restate winner and Phase 3B production *read* are already bounded. Phase 3C can validate a vendor-neutral model gateway contract now without waiting for the typed-agent definition layer (3D), persistent workers (3E), business SoT selection or Fleet scheduling. Those lanes can work independently against frozen Phase 0/2 contracts.

## Candidate policy

Phase 2 shortlist: incumbent `incumbent-current-model-routing` against `candidate-litellm` and `candidate-tensorzero`. The Office Master Plan also lists Bifrost and any credible challengers: intake/triage them through the existing competitor-neutral registry before admission, rather than silently excluding or installing them. A working `candidate` is not an architectural winner by default.

## Frozen first semantic scenarios

The 13-case synthetic fixture checks allowed routing, retryable timeout/rate-limit fallback, policy/budget/credential/cross-tenant/capability DENY without provider invocation, local/cloud routing, exhausted providers, unknown-result reconciliation and trace/latency/token/cost evidence. All prompt/request data is synthetic metadata. A canonical policy DENY must never fall back to seek ALLOW; UNKNOWN must not blindly retry.

`scripts/vf_office_v2_model_gateway.py` provides `validate`, `plan`, `evaluate --receipt <file>` and `selftest`. The runner is **offline and read-only**; it neither invokes providers nor verifies vendor claims. Even a semantically matching adapter receipt returns CONTRACT_COMPATIBLE_UNVERIFIED, not LAB_PASS. Runtime proof requires separately admitted versions, immutable pins, actual isolated runs, negative controls, standard scorecards, a recorded winner/fallback and separate promotion gates.

## Acceleration and isolation

This lane owns only `docs/implementation/office-v2/phase3c/`, `scripts/vf_office_v2_model_gateway.py`, and the minimal call inside `scripts/check-office-v2-contracts.py`. It must not alter Phase 3B production read, any Instagram writer, core authorities, live credentials, fleet scheduler, domain data or cost policy. Any concurrent 3D/3E/Fleet work must use its own worktree and file ownership. Keep existing production working throughout.

## Next runnable gates

1. Read live routing incumbent and pinned tested local/cloud runtimes; capture baseline and cost/resource evidence.
2. Review license/security and version/artifact pins; admit only selected candidates to isolated LAB.
3. Run *the same* semantic fixture against incumbent/LiteLLM/TensorZero plus accepted alternatives and negative controls, storing sanitized receipts.
4. Score fitness/safety/operations/evidence/rollback; record winner and fallback only after runtime proof.
5. Pilot a bounded real Office workload later, retaining the incumbent and performing separate authority promotion and readback.
