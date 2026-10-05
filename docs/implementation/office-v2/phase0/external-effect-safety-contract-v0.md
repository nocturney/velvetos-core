# Office v2 External Effect Safety Contract v0

This is a **coordination/proof contract**, not a new authorization engine.

## Canonical authority
Every external mutation first resolves exactly one existing authority from:
`packages/velvetos/policy/policy-registry.json#external_effect_contract.effects`.

If no effect mapping exists, the mutation is **BLOCKED**. Office v2 must not create an ad-hoc allow rule.

## Required sequence
1. Build an exact `EffectIntent`: effect class, action, target, payload digest, idempotency key/scope and correlation IDs.
2. Resolve the registry-mapped `policy_id`.
3. Obtain the policy-native decision / existing exact-action receipt required by that policy.
4. Execute one bounded provider attempt with a unique `attempt_id`.
5. Persist an `EffectReceipt` with provider outcome.
6. Perform required provider/domain readback.
7. Claim success only from the policy-required postcondition evidence.
8. If outcome is ambiguous, mark `UNKNOWN_OUTCOME`; do not blind-retry.
9. Reconcile provider/domain state first. Retry only after reconciliation proves the original attempt did not take effect or the canonical policy explicitly permits a safe retry.
10. Compensation/owner review follows the mapped domain policy; this contract cannot authorize compensation itself.

## Idempotency
- Key must bind the exact logical effect, not just a transport request.
- Scope is one of `exact_action`, `domain_entity`, `provider_operation`.
- A new attempt reuses the logical intent/idempotency identity when retrying the same action after a proven pre-effect failure.
- Changed payload/target is a new intent.

## Unknown outcome
Examples: provider timeout after mutation boundary, lost response, partial multi-step effect, unavailable readback.

Required state:
- `EffectReceipt.status = UNKNOWN_OUTCOME`
- `retry_allowed = false`
- `reconciliation_state = PENDING|UNRESOLVED`
- project checkpoint lists the unknown receipt ID
- next action is reconciliation, not another mutation

## Compatibility with Reform v2
- `velvetos.action-receipt.v1` remains the authorization-decision receipt where the policy registry requires it.
- `instagram.publish` keeps its policy-native receipt.
- Office v2 `EffectReceipt` is provider outcome/readback evidence; it never replaces the policy decision.
- Evidence, health, routing, QA and transport remain non-authoritative.

## Phase 0 known gaps
Drive writes and job/order updates are not yet clearly mapped to an effect authority in the current registry. They remain read-only/BLOCKED for mutation smoke until canonical mappings are added through the existing policy architecture.
