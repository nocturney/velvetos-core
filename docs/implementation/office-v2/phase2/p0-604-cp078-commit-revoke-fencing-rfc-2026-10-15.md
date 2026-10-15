# CP078 — A fenced COMMIT_ADMITTED boundary for Office #604 / #612

**2026-10-15 | RFC / security-review candidate only | P0 SECURITY ADMISSION RED | DOCS ONLY**
**Owner decision pending. Do not implement as a live GitHub writer, merge, or relax any P0 source-execution guard based on this RFC.**

**R1 SECURITY CORRECTION:** This first-pass RFC has a [subsequent adversarial desk review](p0-604-cp078-r1-security-review-2026-10-15.md) and a revised [70-case data-only schedule set](p0-604-cp078-adversarial-schedules-2026-10-15.json) (formerly 42). Read those corrections BEFORE implementation. No cases in CP078 were executed. The desk review is not independent audit sign-off.

## 0. Why this RFC exists: a witnessed, not hypothetical, bug

CP077 exact head: [2f9035b9b366353c35a6a224608c8e4c23709dc8](https://github.com/nocturney/velvetos-core/commit/2f9035b9b366353c35a6a224608c8e4c23709dc8).
Signed fixed claims, separate real Linux kernel identities (signer UID62005, worker UID62002 and single native Git sink UID62001), etcd 3.6.15 real mTLS/RBAC/TTL owner and durable unleased intent did **not** fence an external Git ref.

In the reproducible CP077 schedule the issuer deletes the etcd owner **after the sink's last successful owner + intent read, but before native git update-ref**. The stale sink changes its local disposable Git ref. The two extended 60/60 laboratory receipts count that behavior as an *expected negative vulnerability witness*, **not** 60 safe checks. Existing local-only proof never used GitHub credentials, remote GitHub ref, production source or actual CP058 model-authored code. Keep the witness in the permanent negative regression set.

- Baseline CP077: [source/evidence](https://github.com/nocturney/velvetos-core/blob/2f9035b9b366353c35a6a224608c8e4c23709dc8/docs/implementation/office-v2/phase2/p0-604-real-etcd-mtls-uid-git-cp077-2026-10-15.md)
- Canonical issues: [#604](https://github.com/nocturney/velvetos-core/issues/604) and [#612](https://github.com/nocturney/velvetos-core/issues/612)
- Exact remote CI for CP077: **NOT RUN** at this writing (stacked PR #730 targets unmerged #729, while check-all PR trigger targets main). A parent-PR check is not a CP077 check.

The remediation must define which operation irrevocably authorizes a subsequent GitHub effect and distinguish a *revocation request* from *acknowledged effective revocation*. Reading etcd an additional time cannot atomically transact with a separate GitHub ref update.

## 1. Scope and explicit non-goals

In scope: a canonical Core #604 issuer; exclusive real physical host/task/GPU generation ownership; one separately privileged GitHub credential sink; exact signed source and ref authority; durable intent; provider-side serialization of admission vs. revocation; unknown outcome reconciliation; GitHub ref compare-and-swap; unambiguous client receipts; adversarial negative schedule.

Out of scope: implementing or turning on remote credentials, changing main ruleset, executing model-authored CP058 source, allowing autonomous workers, installing services, scheduling additional GPUs, authorizing deployments, publishing media or involving production customers. A GitHub ref is **not** a serialization point for etcd; downstream Actions/webhooks/deployers are separate external effects and need their own admission mechanisms if in scope.

This proposal only targets *one exact Git ref effect under an admitted epoch*. "Exactly once" must not be claimed without independent evidence: API timeouts, ABA ref movement and asynchronous consumers can obscure whether a prior effect occurred.

## 2. Proposed security decision: Option A versus Option B

### Candidate A: delayed effective revocation (recommended for owner/security review)

- A **REVOKE_REQUESTED** event is durably committed by the issuer and **immediately prevents any future COMMIT_ADMITTED** for that generation, even if its original TTL lease has not expired.
- An operation which the issuer had **already** serialized as COMMIT_ADMITTED before the revoke request owns a narrowly scoped, irreversible grant to attempt **one** exact remote ref effect. That attempt may execute after *the request*, but it is not a post-*effective*-revocation effect.
- **REVOKED_EFFECTIVE** can be acknowledged only after *all* previously admitted operations are independently reconciled as terminal VERIFIED_EFFECT or VERIFIED_NO_EFFECT, with no ambiguous in-flight network effects. If any are UNKNOWN, remain REVOKE_PENDING / FROZEN_UNKNOWN; never report effective completion and never grant a successor overlapping the unresolved scope.
- Safety is prioritized over liveness: an unresolved remote ACK can block final revocation/new owner indefinitely until independent owner-approved remediation. A timeout by itself **never** establishes that no remote effect happened.
- The external effect guarantee is scoped to the GitHub ref transaction. Deferred workflow runs, webhooks or third-party publication are **not** covered unless separately gated.

This contract must be surfaced explicitly to operators. A UI must not present "revoke requested" as "revocation complete."

### Candidate B: strict no-effect after the *revocation request*

An asynchronous external GitHub API call can be accepted by GitHub after a local controller has observed a revoke request, even if the controller tried to cancel it. Neither an extra etcd read nor a GitHub ref CAS prevents this scheduling. Strict B is **NOT proven** with the current two-store architecture. Choosing B requires a different architectural dependency: a destination-side transaction/hold/fence or shared effect serializer which can abort already dispatched writes before effects. Otherwise the safe outcome is refusal to enable remote writes.

**Decision record: PENDING OWNER + INDEPENDENT SECURITY REVIEW.** Do not quietly implement A and then describe it with B's stronger guarantees.

## 3. Canonical authority and signed scope

The canonical issuer, not a local root lab fixture, is the sole authority for allocation and revocation of a monotonically increasing generation scoped to:
- task_id, real physical host identity, actual worker OS principal, exclusive GPU resource (or explicit NO_GPU), generation/epoch, issuer revision, and signed deadline/lease identity;
- repo stable ID, exact full ref, old Git OID, proposed new Git OID, source SHA256, model-source pin only if/when separately admitted, action class, unique durable intent ID, nonce, signer key identity and immutable protocol version.

A lease can expire or be revoked without changing an already durable COMMIT_ADMITTED decision. The issuer must also separately block new grants while any generation has unresolved admitted effects. TTL is a liveness/ownership signal, **not** a mechanism that retroactively makes already-sent GitHub requests disappear. Use authenticated, revisioned provider transactions and durable quorum-backed authority, not local wall-clock comparisons alone.

No worker, signer or untrusted model-source executor owns: the issuer revocation key, GitHub App credentials, an ambient GH_TOKEN/GITHUB_TOKEN, the sink's private TLS key, an unrestricted rootful containerd socket, or the authority to publish its own trusted QA status.

The privileged sink validates real kernel peer identity, cryptographic signature and complete fixed claim scope before it ever requests commit admission. Sink identity is a distinct protected OS principal with narrow, version-pinned API calls and auditable ref-scoped effects.

## 4. The one linearization point

Issuer storage must serialize **both** revocation requests and irreversible commit admission for a given generation/ref. A conceptual provider transaction:

~~~
COMMIT_ADMIT(task_id, generation, intent_id):
  compare current owner/generation/revision == signed exact scope
  compare lease LIVE and NO REVOKE_REQUESTED for that generation
  compare intent phase == PREPARED and sink identity == authorized sink
  compare no other effect is admitted or unresolved on this ref/resource
  put immutable grant phase COMMIT_ADMITTED,
      oldOID, newOID, sourceSHA, issuerRev, generation,
      admittedRevision, sinkIdentity, intentNonce
  mark resource/ref blocked against successor until terminal reconciliation
~~~

If the issuer processes REVOKE_REQUESTED first, the transaction rejects and **no ref effect may start**. If COMMIT_ADMIT linearizes first, the grant remains valid solely for the specified *one attempt* even if revocation is requested next. Do not grant after a closed generation. The sink must fsync/journal the admission and network-send state before attempting the external call.

There must be an issuer-enforced *single* admission owner per target (repo/ref and host/task/GPU scope); distinct GPUs alone do not authorize two concurrent writers to one ref. Durable unleased intent and successor exclusion survive provider TTL expiration and process death. Issuer/provider crash must not roll back an admission or re-enable an old generation.

**Crucial distinction:** this serializes *permission to start an irreversible attempt*; it does not make a GitHub ref update part of an etcd atomic transaction. Claims such as "zero writes after revoke request" are false under Option A.

## 5. Two orthogonal state machines

### Per-intent effect phase

CREATED -> PREPARED -> COMMIT_ADMITTED -> EFFECT_IN_FLIGHT -> {VERIFIED_EFFECT, VERIFIED_NO_EFFECT, FROZEN_UNKNOWN}.

- CREATED / PREPARED: no irreversible effect; revocation first causes DENIED / terminal no-attempt, retaining audit history.
- COMMIT_ADMITTED: persistent permission to start one exact effect under Option A, never a permission for retries or a different SHA.
- EFFECT_IN_FLIGHT: durable send-start intent **before** any external request is sent. Network timeout, 5xx, post-send process crash, lost ACK and unknown ref state transition to FROZEN_UNKNOWN; never blind replay.
- VERIFIED_EFFECT: independently read the exact repo/ref and immutable commit/tree/source scope; link to a trustworthy request/commit identity or leave uncertain if another actor may have produced the same visible state.
- VERIFIED_NO_EFFECT: requires proof that a send was never initiated (durably prior to handoff and no descendant effect) or authoritative destination evidence; simply seeing oldOid later is insufficient because an ABA move or intervening actor may have occurred.
- FROZEN_UNKNOWN: no automatic retry, no new generation, no "revoke complete"; owner-approved investigation with immutable readbacks and signed decision trail. The immutable intent ID is never reused.

There is NO transition from terminal states back to EFFECT_IN_FLIGHT. No background re-send of a previous attempt.

### Per-generation revocation phase

ACTIVE -> REVOKE_REQUESTED -> DRAINING_ADMITTED -> REVOKED_EFFECTIVE (only after all admitted intents independently verified terminal).

If no work was admitted, an atomic revoke can become effective immediately. If work was admitted before request, the generation remains draining. TTL natural expiry must enter the same admission-blocking, drain/freeze discipline and may not silently bypass UNKNOWN. The UI and task scheduler must distinguish these states. New owners are blocked on the exact overlapping host/GPU/repo-ref until closure.

## 6. GitHub compare-and-swap is necessary, not sufficient

GitHub's documented GraphQL **updateRefs** mutation accepts a RefUpdate with explicit **beforeOid**, **afterOid** and **force**. It specifies that beforeOid must match the current ref and that a multi-ref update is atomic. Candidate single-target update must set:
- repositoryId and fully qualified refs/heads/... fixed to the signed scope;
- beforeOid = exact oldOID from issuer grant (never substituted with the latest remote tip);
- afterOid = exact reviewed newOID representing fixed source/tree;
- force = false; enforce the repository's protected branch rules independently.

Official source: https://docs.github.com/en/graphql/reference/git

Git's explicitly expected-old form of force-with-lease also compares current remote ref, but forcing is undesirable for protected branches and requires separate security review: https://git-scm.com/docs/git-push

**Do NOT treat the REST update-reference force:false option as exact oldOID CAS**; REST documents only fast-forward protection: https://docs.github.com/en/rest/git/refs

The current connected GitHub tool catalog does **not** expose an authorized GraphQL updateRefs mutation for this purpose. This is a design candidate, **not** evidence that the existing ChatGPT connector or current privileged sink implements it. Never switch to a weaker available tool to claim equivalent safety.

Ref CAS protects against lost concurrent ref updates. It does **not** enforce a provider epoch/generation; it does not stop webhook side effects, and a malicious/different GitHub credential holder could bypass the sole-sink protocol. Mandatory branch review/protection and credential isolation are separate P0 gates.

## 7. Durable evidence and reconciliation

Every admission/attempt/reconciliation record must bind immutable (repoId, ref, oldOID, newOID, sourceSHA256, commit/tree SHA, intentId, generation, issuer revision, signer pubkey fingerprint, worker UID, sink UID, audit digest, timestamps, result/evidence URLs) with redacted secrets. Use append-only authenticated receipts; remote returned IDs are evidence but not independent confirmation.

The sink persists:
1. PREPARED with unique intent ID and immutable exact scope.
2. COMMIT_ADMITTED provider receipt (issuer revision) with durable local mirror.
3. EFFECT_IN_FLIGHT send-start marker before the API call.
4. Provider response bytes/status and separate remote readback.
5. Independently reconciled terminal state with verifier identity.

After any crash, provider restart or lost ACK, do not assume "no write" from absence of a local success receipt. On restart compare local WAL/SQLite and provider authoritative records, freeze on inconsistency, and read remote canonical ref/commit history. If another actor advanced the ref or an ABA is possible, treat outcome as UNKNOWN absent stronger audit evidence. Reconciliation authority is separate from the untrusted worker and from the signer. Admit no successor in ambiguity.

A received 200 response is not equivalent to a verified effect; a delayed webhook or status event is not equivalent to a ref readback. A remote ref landing is not necessarily exclusive proof of authorship if the same candidate SHA could be written by another principal.

## 8. Adversarial schedules and acceptance requirements

The adjacent data-only contract is:
[p0-604-cp078-adversarial-schedules-2026-10-15.json](p0-604-cp078-adversarial-schedules-2026-10-15.json)

At minimum, exercise:
- revoke before PREPARED; after PREPARED but before COMMIT_ADMITTED; at exactly concurrent admission; after COMMIT_ADMITTED but before send; after remote send and before provider ACK; after destination update but before ref readback;
- real TTL expiry at each boundary; issuer crash/restart; sink death at each fsync/network boundary; network delay, dropped response, HTTP timeout, wrong cert, stale/mismatched epoch, distinct OS UID, replayed nonce, mismatched source/ref/oldOID;
- two real workers and competing GitHub writers; same oldOID/newOID replay; third party ABA; ref CAS failure; multiple effects from a lost ACK; release of GPU/ref while UNKNOWN.

For every schedule, evidence must record the issuer linearization order, admitted generation, observed ref before/after, persistent local/provider state and whether the result is ALLOWED, DENIED or FROZEN_UNKNOWN. **An expected unsafe observation from CP077 is a baseline regression oracle, not a safety acceptance test**.

Acceptance tests must show:
- request-before-admission: zero irreversible Git effects, including an adversarial pause at the former last provider-read barrier;
- admission-before-request: at most one exact scoped attempt and **no effective revocation ACK** before verified terminal completion; if unresolved, UNKNOWN freezes grant and successor;
- after REVOKED_EFFECTIVE: no new effect from the closed generation; no ref/host/GPU successor overlaps with unresolved prior effect;
- no false green for network loss, destination ambiguity, spoofed worker or altered claim;
- source and signer provenance independently pinned; no credential leakage or capability escalation.

Exact-case tests must be executed in a separately authorized, disposable, credential-free test environment. A deterministic model or a synthetic lab is **not** a substitute for remote GitHub effect-time security admission.

## 9. CI is a separate trust boundary

Current .github/workflows/check-all.yml on main allows pull_request only for base main. Stacked Draft #730 targets CP076 so no automatic exact-head check has run. Although main workflow supports workflow_dispatch on a branch, its current job has statuses:write, and scripts from the PR branch execute inside that token-bearing job. A manual branch dispatch therefore must **NOT** be called "independent protected QA" and should not be invoked as a P0 admission shortcut.

Preferred security plan:
1. Reviewed protected-main policy/runner obtains the **data-only pinned candidate SHA**, validates repo/ref/commit provenance, and explicitly has no privilege to write commit statuses from candidate code.
2. Separate read-only or tokenless test execution of immutable exact source on independent physical/hosted boundary; no checkout credential persistence; no rootful worker socket, no outbound credentials, no model source until original P0 source-isolation gate is separately approved.
3. Independently owned status publisher verifies immutable test artifacts and exact HEAD; never let branch-under-test set its own trusted check or edit the workflow that judges it.
4. Record workflow run IDs and exact SHA; ordinary green check-all does not waive canonical Core lease, commit-revocation semantics or owner review.
5. GitHub default main ruleset 23284099 currently enforces deletion + non-fast-forward + required check-all, not mandatory PR/review; get owner/security approval for any change. Do not silently alter branch protections.

## 10. Prerequisites and explicit gates

GATE A — independent security reviewer signs the precise revoke semantics and effect scope (Option A or B).  
GATE B — owner explicitly authorizes protected main PR/review ruleset design and who holds issuer/GitHub credentials.  
GATE C — separately privileged issuer, signer, worker and sole GitHub Sink with no credentials in untrusted execution, with root/host threat boundary reviewed.  
GATE D — permanent red witness + new adversarial schedules run safely against a disposable real effect destination and durable provider with crash/expiry/UNKNOWN readback.  
GATE E — trusted exact-HEAD CI, phase-separated hidden QA of actual CP058 source **only after** source execution admitted, then two physically separate real coding tasks and serial owner-reviewed protected merge with postmerge SHA readback.

None of A–E are completed by publishing this RFC. In particular **P0_GENERATED_SOURCE_OS_ISOLATION_NOT_ADMITTED remains enforced**. No model-authored source, paid inference, Codex CLI, new scheduler, GitHub credentials, remote writes, branch rules or production changes are authorized here.

## 11. Owner decision template (not yet signed)

- Selected revocation contract: PENDING (A delayed-effective / B strict request-time / other).
- Definition of irreversible commit boundary: PENDING.
- Definition of "effect" (single Git ref only, versus downstream deployment/webhook): PENDING.
- Who is issuer authority and who is distinct privileged GitHub Sink: PENDING.
- UNKNOWN maximum duration, escalation owner and release criteria: PENDING.
- Mandatory branch review/ruleset approval: PENDING.
- Independently signed reviewer and evidence link: PENDING.

**Current status: REVIEW-ONLY DESIGN / RED. Keep #729 and #730 Draft. Do not merge this CP078 RFC as a claim of security admission.**


## 12. CP078-R1 security review (post-RFC)

[Read the 9 detailed findings and ten strengthened invariants](p0-604-cp078-r1-security-review-2026-10-15.md). The RFC above is a candidate, NOT an implementation-ready or independently validated safety specification.

**Clarifications that override ambiguous wording above:**

1. **Revocation click versus authority:** REVOKE_SUBMITTED is a client/UI observation and is NOT a committed authority event. Only REVOKE_REQUESTED_COMMITTED with a provider quorum revision races atomically against COMMIT_ADMITTED. Lost submit ACK remains REVOKE_REQUEST_UNKNOWN until issuer readback. Under Option A a grant can win while a user's click has not been durably recorded; never promise strict click-time revocation.
2. **One grant is not one network effect:** irreversible permission is separate from durable SEND_START and remote delivery. No automatic HTTP SDK/proxy/client replay. GitHub clientMutationId is documented as a client-generated identifier, not a guaranteed deduplication key. Crash/timeout may require indefinite FROZEN_UNKNOWN.
3. **Readback versus causal completion:** an unchanged old ref is not no-effect proof (late arrival or ABA); a matching new ref is not proof the authorized sink wrote it. REVOKED_EFFECTIVE requires positive evidence no prior admitted request can still land; when evidence is unavailable, do not ACK effective revoke.
4. **Object pre-stage is a separate external effect:** destination afterOID commit/tree/blob must be present and match source/parent/tree before ref promotion. Any necessary upload requires independent OBJ_PRESTAGE authority/data-classification approval; do not expand a ref-only grant into arbitrary remote object writes.
5. **All resource identities atomically reserved:** authoritative compare-and-write covers task/generation, authenticated physical host, GPU and repo/ref reservations together; otherwise unrelated task IDs or distinct GPUs can race for the same destination ref.
6. **Scope of guarantees:** without exclusively enforced GitHub principal and branch controls, property is about *the approved VelvetOS writer only*, not all admins/apps/webhooks. Protected main mandatory PR review and actual independent QA remain missing.
7. **CI separation:** Draft #722's token-separate publisher is necessary but insufficient if candidate code controls the test oracle; Draft #726 protected-main candidate policy remains unmerged. Neither authorizes shortcut checks of stacked CP077 via current status-write workflow.

The data-only JSON now specifies **70 distinct adversarial schedules**: prior 42 plus R1 28, all with executed_in_cp078=false. The historical CP077 late-revoke outcome is still the sole previously witnessed unsafe baseline and must NOT be counted as CP078's passing test. These statements do not select Option A or B on the owner's behalf.

**Security gate remains RED.** No new model-generated code execution, native provider experiment, GitHub privileged remote ref write, change to main ruleset, Codex CLI, paid inference, or Production action is admitted.
