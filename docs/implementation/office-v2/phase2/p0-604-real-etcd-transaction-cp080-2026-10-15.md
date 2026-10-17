# CP080 — real one-member etcd atomic admit/revoke + disposable local Git

**2026-10-15 | Office #604 / #612 | DRAFT ONLY | P0 GENERATED-SOURCE ADMISSION RED**

## Purpose and prior RED witness

CP077 [Draft #730](https://github.com/nocturney/velvetos-core/pull/730) repeatedly reproduced the unsafe timing gap: after the last genuine mTLS etcd owner/intent read, the issuer can revoke owner before native local Git `update-ref`, yet the stale sink still writes. CP078 [Draft #731](https://github.com/nocturney/velvetos-core/pull/731) proposed separate **REVOKE_REQUESTED_COMMITTED** vs **REVOKED_EFFECTIVE** semantics; CP079 [Draft #732](https://github.com/nocturney/velvetos-core/pull/732) exercised these mechanics with SQLite + native Git only.

**This CP080 moves the atomic admission/revocation and overlapping resource reservation to a REAL ephemeral etcd server with actual Raft-backed one-member transactions** while keeping any Git side effect strictly **LOCAL**. It is a tested **lab fixture**, not a production-suitable privileged Sink.

## Exact source and environment

- Executable test-only source: [`scripts/vf_office_v2_604_real_etcd_revoke_admit_lab_cp080.py`](../../../../scripts/vf_office_v2_604_real_etcd_revoke_admit_lab_cp080.py).
- Final source SHA256: `02c90170b3b741d4ba2d1fd985b1189b83ff4b5dcc515a6936ca50ca8068ddae`, Git blob `77698f88cc3c09084d9058b1cdf7c7e9c5fc9a9d`.
- Physical host: `MacMiniOffice2.local`, **existing** Colima `velvet-qa` Linux **aarch64 rootless guest**; no host-global install or new daemon/service. Script was piped into the guest over stdin with `env -i` and the exact explicit non-production guard; it was **not an autonomous CP058 model-authored agent**.
- Pinned official etcd **3.6.15** executable SHA256 `117cc09981c0f1eb378e7520be6969756c2d6a762f376944e53f7bc9800c0c59`, etcdctl SHA256 `de07257495499384f91f028dbc0c8e0394e0bd572b728ac486bbadbfa1cdf275`, reused from the previously verified CP077 official release cache and rechecked at each invocation.
- Both etcd peer and client bind to dynamically allocated **127.0.0.1** ports. One-member Raft quorum. **HTTP without mTLS or RBAC in CP080**; unlike CP077, this run does **not** prove authentication/authorization of remote identities.
- All server data, locks, one short-lived bare local Git repository, test lease/intent namespaced under `/vf604/cp080/<random>`, and provider log live under `/tmp/vf604-cp080-*`; per-run cleanup stops/waits for etcd and checks a sentinel before recursive delete.
- Ref is only `refs/heads/cp080-local-only` in a newly initialized `/tmp` Git bare repo; no Git remote configured. No GitHub App token, `GITHUB_TOKEN`, SSH agent, cloud API or production mounts passed through the subprocess env.

The harness permits `--selftest` (static no provider) or `--provider-lab` only after an exact `VF604_CP080_DISPOSABLE_LOOPBACK_ONLY=VF604_CP080_EXPLICIT_NO_GITHUB_LAB` environment gate, Linux aarch64 check, non-root UID check and official executable SHA pinning.

## What the real provider transactions exercise

**One global (within this ephemeral namespace) etcd atomic transaction** compares generation status `ACTIVE`, one real TTL-backed owner with fixed claimant **and exact provider `mod_revision`**, and absence of prior intent, task, host, GPU and repo/ref reservations. If and only if all conditions match, the same transaction puts `COMMIT_ADMITTED`, the unleased intent and all four durable reservation keys.

The revoke transaction competes against that admission on the same authoritative generation value:

- **Revoke wins first:** `ACTIVE → REVOKE_REQUESTED_COMMITTED`, owner deleted in one transaction; subsequent admission fails, no intent/ref reserved. With no admitted intent, a separate guarded transaction may acknowledge `REVOKED_EFFECTIVE`.
- **Admission wins first:** pre-admitted immutable local intent + task/host/GPU/ref reservations persist even if owner is subsequently revoked or naturally expires. A second guarded transaction changes `COMMIT_ADMITTED → DRAINING_ADMITTED`; no `REVOKED_EFFECTIVE` while outcome is in-flight or `FROZEN_UNKNOWN`.
- **Local Git after request:** one admitted intent may mark `GIT_CALL_STARTED`, perform exactly one **local native** expected-old-`git update-ref` after the issuer's committed revoke request and then reconcile `VERIFIED_LOCAL_EFFECT` and `REVOKED_EFFECTIVE`. This is specifically proposed **Option A**, not a strict no-effect-after-revoke-request promise.
- **Competing dispatches:** two threads issue the same `COMMIT_ADMITTED→GIT_CALL_STARTED` etcd CAS; only one succeeds. Reused intent cannot be dispatched twice.
- **UNKNOWN and successor:** `FROZEN_UNKNOWN` and still-reserved ref deny early effective ACK, blind retry, and successor reservation.
- **Real lease expiry:** a short real TTL-backed owner disappears; an unleased intent/ref reservation remains. A fresh successor cannot exploit owner loss.
- **Owner ABA denial:** replace a prior owner key with the **same value** and a new lease after TTL expiration or explicit deletion. Admission is **denied** because it must compare the original owner `mod_revision` in the same etcd transaction. This exact weakness was found and fixed during CP080 review; the earlier 15-case source and runs are superseded.
- **Permanent security-negative control:** a sink that deliberately bypasses the admission transaction can still change the disposable local Git ref AFTER acknowledged effective revocation; this is the same class of **critical unsafe behavior** as CP077. The negative case passing means *the vulnerability was witnessed*, not fixed for arbitrary actors.

The lab fixture's `VERIFIED_LOCAL_EFFECT` marker is written by the trusted test controller after synchronous local Git readback. It is NOT independent remote GitHub effect-attribution evidence.

## Native execution receipts — exact FINAL pinned source

The final 17-case source at SHA256 `02c90170b3b741d4ba2d1fd985b1189b83ff4b5dcc515a6936ca50ca8068ddae` ran in **four independent provider/temp-directory instances**, with:

| Metric | Observed |
|---|---:|
| Full experiment invocations | 4/4 exit 0 |
| Named scenario outcomes (includes one expected negative unsafe witness per run) | **68/68 as expected** |
| Concurrent real etcd revoke/admit transaction races | **48/48** |
| Admission wins first | 20 |
| Revocation wins first | 28 |
| ABA stale owner/lease rebind negatives | 2 per run |
| GitHub remote ref effects or credentials | **0** |
| Independent authorized production security sign-offs | **0** |

The first source run after ABA fix recorded `3 admitted / 9 revoked` out of 12 races. Three further raw JSON receipts were validated independently against count, SHA, deliberate ABA cases and `SECURITY RED` marker:

- Repeat A: `5 / 7` admission/revoke; SHA256 `f2df918c543710734f16a88665d394d1c464dcff749b1d398102ddba110c21a7`.
- Repeat B: `4 / 8`; SHA256 `0aed7fb4f1bf0198caf071d1b55747d96df859abb56fb85a478e59d0e2a62729`.
- Repeat C: `8 / 4`; SHA256 `840a8313688e53efce396639596750f383383b9af2a129bb25dd211208d691d3`.

Data-only canonical receipt: [`p0-604-real-etcd-transaction-cp080-2026-10-15.json`](p0-604-real-etcd-transaction-cp080-2026-10-15.json). The first revised run is evidenced by connected-device stdout, not a separate raw-file hash. **DO NOT** add the earlier superseded 15-case preliminary runs to these final 68 results.

Independent cleanup check after the final suite: **zero** `/tmp/vf604-cp080-*` guest test roots, **zero** `--name vf604-cp080` provider processes. No permanent service, installed agent, modified Mac login, branch rule, production data or globally changed OS security setting.

## Important limitations, barriers and next necessary review

1. **Cross-store time-of-check/time-of-use is not eliminated by etcd:** GitHub is external to etcd. Option A narrows the guarantee to no effects AFTER **acknowledged effective** revoke; admitted effects can still land after the *request*. Option B strict request-time no-effect remains not proved.
2. **No authenticated issuer/sink:** CP080 uses one-member etcd with loopback HTTP and **no mTLS/RBAC**. CP077 proved temporary mTLS/RBAC with real separate Linux UIDs but still exposed late-revoke stale Git. A single experiment combining authenticated issuer, privileged sink, owner+resource reservation, crash recovery and remote CAS is not yet validated.
3. **Remote GitHub semantics missing:** real GitHub `updateRefs` `beforeOid` and credential isolation; separate approved Git object pre-staging; asynchronous network send, ACK loss, remote audit, third-party writers and ABA remain out of scope. A local `git update-ref` is NOT a remote async ref promotion.
4. **Owner/canonical identity missing:** synthetic fixed task, host, NO_GPU and ref, not a real Core multi-host GPU allocator or signed monotonic generation.
5. **No independent external review:** all new CP080 harness logic was authored for the experiment and run inside the existing sandbox guest, not verified by independent security reviewers. No hidden CP058 3+12 real source QA or two autonomous coding PR tasks.
6. **70 CP078/R1 adversarial provider schedules remain an unexecuted separate test contract.** CP080 implements only its own 17 narrower scenarios, one negative deliberately unsafe.

**Verdict:** `REAL_ETCD_SINGLE_MEMBER_TRANSACTION_LAB_PASS` and `P0_SECURITY_ADMISSION_RED`. Draft branch is not authorization to merge, relax branch reviews, run the autonomous coding agent or use a credentialed GitHub Sink. Preserve `P0_GENERATED_SOURCE_OS_ISOLATION_NOT_ADMITTED`. No Codex CLI, paid inference, or customer/production effect occurred.
