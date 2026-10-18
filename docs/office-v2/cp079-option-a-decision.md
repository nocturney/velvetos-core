# CP079 revocation timing: Option A decision memo

**18 October 2026 | For Christian and independent security reviewer | DECISION PENDING**
**SECURITY RED / LAB ONLY. Documentation and recommendation, not authorization.**

This memo compares three possible meanings of "revoke" for a previously approved
Git ref change. It does **not** select the system contract, make the CP079
fixture safe for real GitHub writes, or grant any production authority. Christian
and an independent security reviewer must approve the contract separately
before any implementation or privileged sink is admitted.

Sources: [CP079 merged PR #732](https://github.com/nocturney/velvetos-core/pull/732)
(merge `8dbde3a2`), [CP079 lab evidence](../implementation/office-v2/phase2/p0-604-sqlite-serialized-localgit-cp079-2026-10-15.md),
[QA verdict, especially test 12](https://github.com/nocturney/velvetos-core/pull/732#issuecomment-6250922203),
[CP078 proposed contract #731](https://github.com/nocturney/velvetos-core/pull/731),
and [Office coordination issue #612](https://github.com/nocturney/velvetos-core/issues/612).

## 1. What Option A means to an operator

**Option A: approval is a commitment that survives a later revoke request.**
A change already recorded as `COMMIT_ADMITTED` in the issuer's serialized
transaction may still be *sent and applied* after the issuer commits
`REVOKE_REQUESTED`. Revocation stops *new* approvals, but its effective
acknowledgement must wait for all earlier approvals to reach a verified terminal
outcome. `PREPARED` alone is **not** approval. A UI saying "revoke requested"
must not imply "the ref cannot change any more."

Concrete single-intent example (times illustrative, local CP079 semantics):

| Time | Event | What is allowed under A? |
| --- | --- | --- |
| 10:00:00 | Intent for epoch 7, exact task/host/GPU/ref, and old/new OIDs becomes `COMMIT_ADMITTED` inside SQLite `BEGIN IMMEDIATE`. | This intent has already won admission. |
| 10:00:01 | Christian clicks revoke; the issuer commits `REVOKE_REQUESTED`. | No new admission. The prior intent may still finish. A click and a committed issuer record are not identical events. |
| 10:00:02 | The approved sink marks `SEND_STARTED` and `GIT_CALL_STARTED`, then its local `git update-ref <ref> <new> <old>` succeeds. | **The ref changes after revoke was requested.** This is the intended Option A outcome of CP079 test 03. |
| 10:00:03 | Sink verifies the terminal local Git result; issuer marks `REVOKED_EFFECTIVE`. | Only now may it acknowledge effective revoke and consider a non-overlapping successor (test 15). |

If the send or effect is **UNKNOWN** (crash, lost result, ambiguous delivery),
Option A must **not** claim `REVOKED_EFFECTIVE`, retry blindly, or admit a
successor. CP079 tests 04, 05, 09 and 14 exercise this freeze in a disposable
fixture. "Approved before revoke" never means "may write after an effective
revocation acknowledgement." Option A may result in indefinite draining if a
terminal outcome cannot be independently established.

These are **local** observations: SQLite + synchronous, credential-free
`git update-ref` against a temporary bare repository. They say nothing
conclusive about a delayed GitHub request that could apply after the client
disconnects.

## 2. The choices (not interchangeable)

For comparisons below, "revoke" means an **issuer-committed revoke event**,
not merely a UI click; "apply" means the actual protected ref mutation at the
destination, not simply dispatching an HTTP request.

| Alternative | Contract and benefit | Principal risk | Cost and implementation implications | CP079 regression cases that change |
| --- | --- | --- | --- | --- |
| **A - keep committed admission** | Admission ordered before revoke remains entitled to one scoped effect; revoke drains it before `EFFECTIVE`. Easiest match to current CP079. | Operator may see a **post-request ref change**, perhaps much later. UNKNOWN can block effective revoke and successors indefinitely. Mistaking `REQUESTED` for `EFFECTIVE` is unsafe. | **Lower relative change cost**, but still substantial work for real issuer, sole authorized GitHub sink, exact old-OID CAS, recovery and honest UI states. A cannot fix unadmitted writers. | **03, 11, 15 remain A assertions** (admit-first may finish after request); **01, 02** keep revoke-before-admit denial. **04, 05, 06, 08, 09, 13, 14** keep no-replay/UNKNOWN/CAS invariants; extend delayed-delivery negative cases. **12** remains an independent unsafe witness until the bypass is closed. |
| **B - revoke wins any time before actual apply** | If issuer revoke commits before the destination ref change, **no earlier admission may subsequently mutate that ref**. Matches the intuitive "stop outstanding changes" expectation. | A local last-second check cannot stop an already in-flight, asynchronously applied GitHub request; falsely claiming strict cancellation would be a serious security bug. External GitHub ref CAS alone checks old OID, **not** the issuer revoke epoch. | **Highest cost / currently unproven**: needs destination-coupled atomic revoke/effect arbitration or equivalent enforceable hard fence, durable cancellation/no-effect proof, and a trustworthy sole credential holder. Until proven, freeze/deny real sends; do **not** label the current CP079 implementation B. | **03 and 15 must invert** the post-request successful-send expectation into denial or independently verified no-effect; **11** must test revoke vs actual apply, not only revoke vs admission; **04, 05, 09, 14** need in-flight/late-effect/UNKNOWN no-effect proofs, not just local freeze. **13** adds revoke-vs-concurrent delivery. **01, 02, 06, 07, 08, 10, 16** retain their independent guarantees. **12** needs a protected-path denial regression plus retained negative witness. |
| **C - revoke wins only before a fence/lease** | A short, uniquely scoped, durable *effect fence/lease* wins if committed before revoke; after that point the one authorized effect can finish despite revoke. If revoke wins before fence, deny effect. Makes the irrevocable point explicit. | A stolen/stale fence, cross-resource overlap, expiry ambiguity or delayed HTTP delivery after lease expiry can recreate post-revoke writes. An issuer-only TTL is **not** a destination-enforced fence. | **Medium-to-high cost**: define an atomic fence-vs-revoke linearization point, bounded validity, unique epoch/intent/ref scope, revocation/expiry checks at a sole sink and destination-bound enforcement; collect late-delivery and renewal/ABA proof. No approved implementation today. | **03 and 15 must distinguish admitted-but-unfenced (deny) from fenced-before-revoke (permitted)**. **11** becomes a true fence-vs-revoke race; **04, 05, 09, 14** add expired-fence, delayed completion and crash recovery; **08, 10, 13** add fence replay/epoch and duplicate dispatch negatives. **01, 02, 06, 07, 16** remain base invariants. **12** still needs protected-path denial and an unsafe comparator. |

**Every option** must continue to enforce exact task/physical host/GPU/repo-ref
scope, pinned expected-old OID, unique owner generation, no overlapping
resources, one durable send/effect attempt, fail-closed UNKNOWN and truthful
effective-revoke acknowledgement. Option choice **does not** resolve the
legacy unadmitted writer from test 12. CP079's 16 tests do not validate real
GitHub request ordering, network cancellation or a production credential
boundary. CP078's 70 adversarial schedules are **data-only, not a passing
provider-backed test suite**.

## 3. Recommendation, not a decision

**RECOMMENDATION, NOT A DECISION: choose B as the security target and
keep real writes disabled until an independent test proves it enforceable.**

Reason: Christian's expected meaning of "revoke before apply" should not
silently depend on an earlier admission the operator cannot see. B gives the
strongest post-revoke safety promise and avoids Option A's unbounded delayed
effect or Option C's difficult lease-expiry edge. Its difficult cost is real:
the current SQLite/local-Git race proof plus GitHub old-OID CAS **cannot**
enforce B across a remote asynchronous destination. A wish for B is not B
implemented; if an effect-time hard gate is unavailable, stop at SECURITY RED
rather than pretending a new pre-send check makes B true.

A may be acceptable only as an **explicit** Christian + independent security
risk acceptance with UI wording that distinguishes `REQUESTED` from
`EFFECTIVE`, a documented drain/UNKNOWN policy, and adversarial remote
tests. C is a possible future bounded compromise only if its destination-side
fence and expiry behavior are proven. Neither alternative is implicitly
approved by this memo or the CP079 merge.

**Decision record for later sign-off (currently blank):**
owner-selected alternative: **UNDECIDED**;
independent security verdict: **NOT GIVEN**;
issuer/destination effect-boundary evidence: **NOT PROVEN**;
production admission: **DENIED**.

## 4. Plan to close the test-12 legacy bypass (no code in this PR)

**Problem demonstrated:** CP079 test
`test_12_legacy_unguarded_last_read_is_observably_unsafe` explicitly calls
raw, fixture-local `git update-ref` *after* `REVOKED_EFFECTIVE` without
issuer admission or the approved sink. It passes by **reproducing a violation**,
not by preventing one. This CP077-style negative comparator is valuable
evidence; changing the revocation semantics alone cannot close the bypass.

Proposed later security implementation/review sequence:

1. **Inventory every possible writer:** old direct Git ref paths, GitHub App
   identities, scripts, worker subprocesses, tokens, inherited Git auth, remote
   APIs and pre-staged object uploads. Require a trace showing which principal
   can cause a protected ref effect. Do not assume the fixture inventory proves
   production closure.
2. **Designate one protected effect sink:** only a separately credentialed,
   isolated service can mutate the target ref. Workers and legacy sinks get no
   ref-write credentials or reachable privileged API. Security reviewer verifies
   OS/UID boundary, secret custody, network exposure and revocation/rotation of
   every bypass credential; deny by default.
3. **Bind effect authority to issuer state:** verify genuine issuer identity,
   canonical signed task/physical host/GPU/ref scope, non-ABA owner epoch,
   unique intent, exact old/new OIDs and committed admission (or the separately
   approved B/C fence). Enforce a single serialized resource decision and a
   durable pre-effect marker. Reject stale, missing, replayed, overlapping or
   revoked authority; do not downgrade to a raw Git fallback.
4. **Handle the real destination separately:** require exact expected-old
   GitHub ref CAS, not generic force=false fast-forward behavior; separately
   authorize object pre-stage, record request identity and outcomes, and freeze
   UNKNOWN on ambiguous/delayed requests without assuming readback proves
   no-effect. Define independent recovery/effective-revoke proof *before* live
   credentials exist.
5. **Add independent negative acceptance evidence:** preserve test 12 as a
   clearly labelled **unsafe local comparator** in an isolated no-credential
   fixture, but add tests that send the *same late attempt through the only
   protected sink* and require **DENIED / no ref change**. Test forged/stale
   epochs, wrong UID/scope/ref/OID, revoked credentials, concurrent sinks,
   crash and lost ACK, fence expiry (if C), and delayed real provider
   delivery. A future green count must distinguish "unsafe witness reproduced"
   from "protected path denied." Review both results independently.
6. **Gate any rollout:** two-person owner/security approval of the chosen
   semantics; inspect credential topology and code paths, run provider-backed
   adversarial cases on an authorized disposable remote fixture, require
   protected exact-head CI and independent review. No migration, remote writer
   activation, permissions change or production ref effect comes from this PR.

### Hard boundaries

**SECURITY RED / LAB ONLY throughout.** CP079 is a local Git+SQLite experiment,
not real etcd quorum/mTLS, a privileged GitHub sink, kernel-enforced isolation,
remote request cancellation or CP058 model-authored-source admission.
`P0_GENERATED_SOURCE_OS_ISOLATION_NOT_ADMITTED` remains binding. This memo
modifies no scripts, tests, receipts, PINs, CI/workflows, credentials, ref
writers or policy files; it changes no actual admission or revocation behavior.
A docs-only PR and a green `check-all` are **not** a security sign-off.
