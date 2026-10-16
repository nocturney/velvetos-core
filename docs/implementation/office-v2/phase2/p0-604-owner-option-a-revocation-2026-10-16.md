# Office 2.0 — Owner-approved Option A for revocation

**Decision date:** 2026-10-16  
**Decision:** **OPTION A APPROVED** — explicit confirmation by the project owner in the current chat.  
**Scope:** Future design, implementation and QA of Office #604/#612 task-admission/revocation semantics.  
**Security status:** **RED**. This decision is *not* a cryptographically signed production authorization, protected-branch approval or security-review signoff.

## Decision: what revoke actually means

1. **Before an admission transaction wins:** Revoke wins the atomic provider race, and every further admission for that grant/epoch is denied. No new task, host, GPU or ref reservation can be issued from the revoked generation.
2. **Once admission has won:** Revoke moves the provider generation to **`DRAINING_ADMITTED`**, retains its ref/task reservations and rejects new work. A remote effect that has already been dispatched may still finish. Revoke must **never** be presented as an atomic rollback of an in-flight GitHub request.
3. **At the external-effect boundary:** If it is uncertain whether the write occurred, including lost acknowledgement, timeout, process crash, provider ownership loss or a revoke racing between Git CAS and readback, record **`UNKNOWN_EFFECT_RECONCILE`** durably and keep the job/epoch frozen. No blind retry and no false `COMMITTED` or `CANCELLED` status.
4. **Recovery and lock release:** First obtain independent authoritative remote Git ref/commit readback and match it to the durable expected SHA/intent. Conflict, missing evidence, partition or unknown caller termination keeps the grant frozen with **`REVIEW_REQUIRED`**. Confirmed effects still require separately authorized safe closure; neither process restart nor lease expiry silently reopens the grant.
5. **Option B is not approved:** Immediate cancellation guarantees for a GitHub request already sent to a remote service are not technically proven and cannot follow from etcd atomicity alone.

## Test and delivery contract

Machine-readable decision: [Option A policy JSON](p0-604-owner-option-a-revocation-2026-10-16.json).

`scripts/vf_office_v2_604_owner_option_a_policy_gate.py` checks the exact owner choice, fixed transition vocabulary, no implicit production permission, and the relevant existing **CP082** authenticated etcd + local bare-Git + SQLite negative cases. Its selftest deliberately mutates approval to B, turns security GREEN, permits automatic retries and removes a required revocation case; each must fail closed.

The canonical `scripts/check-office-v2-contracts.py` runs this checker and pins the decision source and checker bytes. The CP082 sealed raw receipts are unchanged: historical experiments remain evidence of **LOCAL** behavior and cannot become remote/prod proof because an owner made a policy choice.

## Actual remaining gates (not waived)

- Authenticated real Core owner/epoch authority and a separate OS-UID Git credential-holding sink **in the same integration**.
- Protected remote GitHub write and truthful lost-ACK/readback reconciliation; secure credential isolation and independent security audit.
- Two distinct real source-coding workers, bounded OS isolation, crash/restart resumption and protected CI/merge verification.
- No paid-model/API orchestration, extra daemon, uncontrolled merging or production deployment without separate explicit authorization.

**Owner's approval resolves the open A/B policy decision only. It does not resolve any of the above implementation/security gates.**
