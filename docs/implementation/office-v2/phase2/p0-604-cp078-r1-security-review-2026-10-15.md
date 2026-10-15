# CP078-R1 — adversarial security desk review and proof obligations

**2026-10-15 | Office #604 / #612 | companion to Draft PR #731 | REVIEW-ONLY / SECURITY ADMISSION RED**

This is an internal desk review sharpening the CP078 proposal. It is NOT an independently conducted external review, signed attestation, model checker result, new code executor, or authorization to run model-generated code. All new adversarial schedules are DATA ONLY / NOT EXECUTED. Original CP077 Linux late-revocation stale-local-Git witness is still an observed SECURITY RED.

Reviewed sources: [CP078 RFC](p0-604-cp078-commit-revoke-fencing-rfc-2026-10-15.md), [CP078 data-only schedules](p0-604-cp078-adversarial-schedules-2026-10-15.json), [CP077 Draft #730](https://github.com/nocturney/velvetos-core/pull/730), official [GitHub GraphQL Git API](https://docs.github.com/en/graphql/reference/git), [REST ref update](https://docs.github.com/en/rest/git/refs), [Git object database](https://docs.github.com/en/rest/guides/using-the-rest-api-to-interact-with-your-git-database).

## Material findings and required corrections

### F01 / CRITICAL: Operator click is not authoritative committed revocation

An operator clicking Revoke or an HTTP caller submitting a request does not mean the issuer durably serialized revocation. A partition, lost response or issuer crash can leave authority unchanged while another sink obtains a commit admission. The original RFC uses REVOKE_REQUESTED to mean an issuer-committed event; the UI must avoid presenting client submission as that state.

Requirement: model REVOKE_SUBMITTED (local UX observation) separately from REVOKE_REQUESTED_COMMITTED (quorum-authoritative transaction revision). Only the latter provably wins against COMMIT_ADMITTED. If the submit ACK is lost, return REVOKE_REQUEST_UNKNOWN rather than ACKing success; perform independent issuer readback. Never backdate an effective revocation receipt.

New negative cases: revoke_submitted_not_committed; revoke_submit_lost_ack; issuer_follower_stale_read.

### F02 / CRITICAL: One admitted grant does not guarantee exactly one remote network effect

COMMIT_ADMITTED serializes a permission decision, not network delivery. A sink can die before or after durable SEND_START, clients may retry automatically, and a replayed mutation can succeed again after remote ref ABA. GitHub describes clientMutationId as a client-supplied identifier; the official updateRefs documentation does NOT promise server-side deduplication using that field. Do not treat it as an idempotency key.

Requirement: a unique immutable grant/attempt ID; exact-request digest, no implicit HTTP/client SDK retries; durable SEND_START before socket handoff; no automatic replay after ambiguous response or death. Restart freezes FROZEN_UNKNOWN. Claim only at-most-one *locally dispatched attempt under a trusted sink* when proven, not universal exactly-once remote effects.

New cases: http_library_auto_retry; client_mutation_id_not_dedupe; crash_after_durable_send_marker_before_wire; duplicate_after_ref_aba.

### F03 / CRITICAL: Readback snapshot does not prove remote quiescence

A current remote ref == oldOID may conceal an earlier effect followed by a third-party rollback (ABA). A current ref == afterOID could have been written by an unrelated credential. A delayed GitHub request may arrive AFTER a verifier sampled an unchanged ref and even after a false REVOKED_EFFECTIVE acknowledgement.

Requirement: VERIFIED_NO_EFFECT requires positively proven lack of any possible in-flight request (including proxy/server queues), not just readback equality. VERIFIED_EFFECT requires provenance linking exact actor/intent/source/commit/tree and no pending ambiguous attempts; if audit evidence is insufficient, remain FROZEN_UNKNOWN and block overlap indefinitely rather than falsely granting effective revocation.

New cases: late_arrival_after_false_no_effect; audit_record_missing; readback_misattributes_same_oid; aba_no_effect_false_positive.

### F04 / HIGH: Remote Git object staging is itself an external write

Before updateRefs can point at afterOID, the candidate Git commit/tree/blobs must already exist on the remote. Creating raw objects is a separate GitHub-side mutation with data-disclosure/provenance risks even without changing a ref. A ref authorization does not authorize object uploads, sensitive source disclosure, or arbitrary blob writes.

Requirement: separate explicitly authorized OBJECT_PRESTAGE scope (or independently verified preexisting immutable remote object), data-classification checks and credential isolation; exact destination commit/tree/parent/source verification before granting ref promotion. No pre-stage privilege may leak to the worker/model. If pre-stage is unapproved, do not proceed with ref promotion.

New cases: candidate_commit_missing_at_destination; object_prestage_wrong_source; object_prestage_without_approval; objects_created_after_admission_before_send.

### F05 / HIGH: Sole GitHub Sink is an enforced scope, not a universal GitHub exclusivity claim

Other admins, GitHub Apps, workflow tokens, humans, integrations or compromised principals may update the same ref. The active main ruleset 23284099 does not currently require PR approval. Distinct worker OS UIDs do not by themselves isolate a privileged token from a root-capable controller.

Requirement: state precisely whether the property protects system-owned effects only or all repo ref changes (the latter needs stronger GitHub admin/ruleset controls). Bind GitHub App installation identity, reviewed branch permissions, issuer/sink principal separation, token absence in model/worker and independently protected status publisher.

New cases: external_admin_ref_update_during_revocation; credential_exposed_to_worker; branch_ruleset_review_not_required.

### F06 / HIGH: Atomic admission needs all overlapping scopes, not only task ID

A transaction that compares only one owner or task generation can permit another task on the same physical GPU or repo/ref. Per-task epoch increments are not global resource fencing.

Requirement: same-authority atomic compare-and-write of canonical task, real host identity, GPU lease, repo/ref ownership and durable unresolved intent. Pending/UNKNOWN blocks every overlapping resource until verified terminal reconciliation.

New cases: multi_key_partial_acquire; cross_task_same_ref_generation; successor_during_draining_different_task.

### F07 / HIGH: Exact GitHub ref compare is orthogonal to issuer authority

GitHub GraphQL updateRefs supports explicit exact beforeOid/afterOid and atomic ref updates. REST force:false only enforces fast-forward, not exact expected-old SHA. The currently connected ChatGPT GitHub tools do not expose a privileged updateRefs action.

Requirement: use a non-null, exact beforeOid and scoped nonzero afterOid, force=false, exact repo node ID and refs/heads/... name; forbid delete, force=true, scope mutation and REST fallback. A GitHub ref CAS still cannot fence an etcd generation. Review remote object availability and branch ruleset behavior.

New cases: graphql_before_oid_missing; graphql_force_true; graphql_after_oid_zero_deletion.

### F08 / HIGH: Lease time and provider availability are independent

Local wall clock, earlier successful read, follower stale revision and a 2-second TTL are not enough to establish the current active generation. Provider crash/restart and lease renewal can race revoke.

Requirement: signed issuer epoch, quorum-serialized provider revision, fail-closed on unavailable quorum, no granting after committed revoke and no successor during unresolved effects. Do not confuse online machine inventory with exclusive leased capacity.

New cases: issuer_follower_stale_read; lease_renewal_after_revoke; provider_quorum_lost_after_precheck.

### F09 / HIGH: Candidate-controlled CI is not a protected independent judge

Draft PR #722 separates statuses:write to a distinct publication job, but remains unmerged. Even that split alone does not establish that PR-controlled source cannot influence the result the publisher trusts. Draft #726 is a separate protected-main Phase A candidate; it too remains unmerged. Their shared file overlap requires an approved exact-tree integration and an independent protected workflow.

Requirement: protected-main policy hash and source pinned outside candidate PR, data-only candidate handshake, tokenless/non-root isolated candidate execution only after source admission, and trusted independent status publisher validating authentic raw receipts. Do not dispatch the current status-write workflow on stacked #730 as an independent exact-head test. The green docs-only PR #731 CI is NOT CP077 security evidence.

New cases: branch_overrides_trusted_ci_policy; status_publisher_trusts_candidate_fake_green.

## Corrected abstract state machines — SPECIFICATION, NOT CODE

Client/API observation: REVOKE_SUBMITTED -> (may be UNKNOWN if no authority ACK).
Issuer authority: ACTIVE -> REVOKE_REQUESTED_COMMITTED -> DRAINING_ADMITTED -> REVOKED_EFFECTIVE (only after all admitted work is independently terminal).
Effect: CREATED -> PREPARED -> COMMIT_ADMITTED -> SEND_START_DURABLE -> REMOTE_IN_FLIGHT -> {VERIFIED_EFFECT, VERIFIED_NO_EFFECT, FROZEN_UNKNOWN}.

The single admissibility linearization point is a quorum-backed compare-and-swap serializing admission versus committed revocation *and* all overlapping physical-host/GPU/repo-ref scopes. If revoke commits first, admission denied and no effect. If admission commits first, Option A may allow one narrowly scoped attempt after the **revoke request** but **not after REVOKED_EFFECTIVE**. Option B (strict no effect after client submission) is not proven and cannot be silently substituted.

## Required invariants to evaluate independently

- INV-01: Authority-committed revoke precedes admission => no subsequent COMMIT_ADMITTED for that generation.
- INV-02: Earlier admitted effect may be in-flight after revoke, but REVOKED_EFFECTIVE cannot be acknowledged while any late effect is possible.
- INV-03: Pending, draining or UNKNOWN blocks overlapping host/task/GPU/repo-ref successor.
- INV-04: Per unique immutable intent there is at most one locally dispatched network attempt; automatic retries prohibited. This is weaker than guaranteed remote exactly-once.
- INV-05: Exact oldOID/newOID, source/tree/commit, repo/ref, signer, generation and issuer revision are immutable at each admission.
- INV-06: Old/current remote ref alone cannot justify VERIFIED_NO_EFFECT; matching afterOID alone cannot establish actor/provenance.
- INV-07: clientMutationId is NOT a documented GitHub server deduplication guarantee.
- INV-08: Candidate/worker/model has no GitHub credentials, issuer authority, unconstrained container root socket or trusted status publication rights.
- INV-09: Remote Git object pre-stage has its own authorization, confidentiality gate and immutable readback.
- INV-10: REVOKED_EFFECTIVE receipt includes exact generation, issuer revision, scope, complete terminal intents and downstream-effect boundary, never a promise about unrelated GitHub admins/webhooks.

## Decisions needed before a live GitHub Sink prototype

1. Explicitly select Option A delayed-effective revocation or Option B strict request-time no-effect. Define exactly what the operator sees.
2. Accept or reject indefinitely quarantined UNKNOWN; do not install unsafe time-based force release.
3. Approve/prevent remote pre-staging of Git objects, including classification of model/customer source and ownership of separate credentials.
4. Define authorized writer identity and external repository ref policy (main mandatory review still missing).
5. Obtain independent security approval for GraphQL beforeOid capability, receipt verification and no automatic retry.
6. Review protected policy integration for #722/#726/#728/#729/#730 without silently merging overlapping shared files.

**Status:** internal adversarial review produced concrete unexecuted negative cases; no source/sink code executed, no GitHub remote mutation by a privileged agent, no production or security-settings effect, no model-based CP058 source execution. Security admission remains RED and P0_GENERATED_SOURCE_OS_ISOLATION_NOT_ADMITTED remains enforced. Draft #731 is not permission to merge.
