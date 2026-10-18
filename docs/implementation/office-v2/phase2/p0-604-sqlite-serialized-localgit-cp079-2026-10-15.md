# CP079 — disposable serialized admission/revocation + native local Git CAS

**2026-10-15 | Office #604 / #612 | merged into main via #732 (8dbde3a2); lab-only, SECURITY RED | NO PRODUCTION**

## Delivered implementation

Source: [scripts/vf_office_v2_604_local_git_revoke_txn_cp079.py](../../../../scripts/vf_office_v2_604_local_git_revoke_txn_cp079.py).

Exact Python source SHA256: `15c47c393ff592acc3cb8e820c5f1a65626e2dc6cd475580d402393616b947b0`. Git content blob SHA: `8d212f849b599ba569f96d2b025f7ea92dad7020`.

Unlike the preceding CP078 self-authored finite abstract model, this CP079 harness actually exercises on-disk **SQLite serialized transactions** and a real **local bare Git repository** in random, cleanup-guarded `/tmp/vf604-cp079-*` fixtures. It only permits the `selftest` CLI command, uses a deliberately sanitized Git child environment with no credentials, user Git configuration or remote, and never connects to etcd, GitHub or a model endpoint.

**Not implemented:** signed Core issuer, actual etcd mTLS quorum/lease, protected GitHub App credential sink, real physical-host/GPU ownership, remote GraphQL `updateRefs`, network ACK-loss analysis, delayed GitHub request cancellation, privileged kernel UID separation or production source execution. This test is a narrow, separately scoped verification experiment, **not a substitute for those gates**.

## Actual 16 native-local test checks

1. Revoke committed before prepare/admit: refuse, local ref unchanged.
2. Revoke between prepare and admit: PREPARED transitions DENIED, no ref change.
3. Admit first, commit revoke later: keep EFFECTIVE blocked until exactly one pre-admitted **local** Git CAS has terminal verification. Native ref update after revoke REQUEST is expected under Option A.
4. UNKNOWN after SEND_STARTED: no blind retry, no EFFECTIVE ack, no successor.
5. Ref still at old OID while a sent request is UNKNOWN: no false no-effect; explicit late local Git delivery cannot make EFFECTIVE succeed.
6. Competing local ref update: native Git expected-old CAS fails, freezes UNKNOWN, no fallback to a newer SHA.
7. Scope mismatch (task/GPU/ref) and expected-old OID substitution: fail closed.
8. Second overlapping reservation/admission/send/effect request: deny replay and double-dispatch.
9. New SQLite connection/restart after UNKNOWN keeps the durable freeze.
10. Closed issuer generation denies stale epoch even after successor generation.
11. Two actual competing threads serialize **COMMIT_ADMITTED vs REVOKE_REQUESTED** via `BEGIN IMMEDIATE`; each allowed order must maintain the respective invariant.
12. **Deliberately unsafe CP077 legacy comparator**: a sink which bypasses issuer admission can change a disposable local Git ref **after REVOKED_EFFECTIVE**. This is an expected red vulnerability witness, **not** a passing security design.
13. Two competing threads attempt the same native local Git effect. An extra `GIT_CALL_STARTED` durable transaction ensures one effect and one explicit denial rather than two sends.
14. Simulated sink crash during `GIT_CALL_STARTED`: SQLite recovery freezes FROZEN_UNKNOWN and rejects replay/revoke-effective.
15. Successor is accepted only after acknowledged effective revoke backed by a verified terminal **local** effect.
16. No configured Git remote; non-`selftest` CLI arguments are refused.

The SQLite authority is **one fixed fixture task, host and NO_GPU resource**. Its transaction does not prove correct atomic allocation of real multi-host/GPU/ref leases. In particular this is not a general-purpose safe remote Git writer.

## Observed execution receipts

Run only in the assistant's **isolated container**, not on any user-controlled machine or real customer/production system:

- Runtime: Python 3.13.5; `/usr/bin/git` version 2.47.3.
- 16/16 Python `unittest` cases passed on each **30 independent full runs**, i.e. **480 successful case executions**.
- Subprocess return: 0; JSON outcome `PASS_DISPOSABLE_NATIVE_LOCAL_GIT_SQLITE_ONLY`.
- Source SHA256 `15c47c393ff592acc3cb8e820c5f1a65626e2dc6cd475580d402393616b947b0`.
- Aggregate receipt SHA256 `c8189d085927458820025a16d3f20e883a4156f8cf7402f11ca59bd53b4c3fb7`.
- Full ZIP evidence SHA256 `1e2525abfd46e476d9c9c57181b1b67659d91c07e067627f3520e6d553ba4472`.
- The ZIP, source, evidence JSON and representative test log are available as user-facing artifacts in the originating ChatGPT conversation; the *reviewable source code itself* is also committed on main via #732 (8dbde3a2); lab-only, SECURITY RED.

The observed 480 PASS counts do **not** mean 480 adversarial etcd/GitHub effect-time cases. All 70 CP078-R1 schedule definitions remain **DATA ONLY / NOT EXECUTED as native real-provider tests**. CP079's 16 local-fixture cases are a distinct set.

## Exactly what was improved

1. **Single local authority transaction** joins revoke and admission rather than separate provider-read and external-effect calls. This eliminates the particular two-sink stale-check admission race *inside this single SQLite fixture*.
2. A durable `SEND_STARTED` marker and an additional pre-native-`git update-ref` `GIT_CALL_STARTED` marker ensure **only one local dispatcher** can pass the local effect boundary, even under concurrent calls, and surviving crashes refuse retries.
3. `FROZEN_UNKNOWN` prevents false effective-revoke acknowledgements and blocks new owners; a ref equal to old or new SHA is **not** treated as authoritative absence/presence of an unrelated remote request.
4. **Option A** semantics are explicit: an already committed admission may result in local Git effect after the revoke *request*, so the UI cannot advertise instant hard cancellation.

## What still prevents P0 security admission

- Real issuer: canonical Core signed exclusive task/host/GPU/repo-ref scope with monotonic generation and authentic quorum writes, not synthetic SQLite.
- Real sink: isolated actual GitHub App credentials with exact expected-old `beforeOid` ref mutation, plus separately authorized remote blob/tree/commit pre-stage.
- Actual remote delivery: a GitHub HTTP request can complete asynchronously after the client crashes, after a snapshot or after a revocation request. Local synchronous Git return is **not** proof of remote safe completion.
- Recovery: lost ACK, third-party ref writes, ABA, actor attribution, no-effect proof and UNKNOWN escape policy cannot be derived from local Git readback.
- Actual OS isolation, independent protected-main policy/CI, branch mandatory reviews, CP058 Phase B hidden QA after source execution admission, and two real autonomous workers.
- Owner and independent security reviewer must **explicitly** select Option A delayed EFFECTIVE vs Option B strict request-time. Neither selection is implied by this laboratory.

**Verdict: LOCAL-NATIVE ADMISSION/REVOCATION MECHANICS TESTED, REAL EFFECT-TIME SECURITY STILL RED.**

`P0_GENERATED_SOURCE_OS_ISOLATION_NOT_ADMITTED` remains binding. Merged into main via #732 (8dbde3a2); lab-only, SECURITY RED. That merge does not authorize a live GitHub writer, allow a remote ref effect, relax protected main, use paid inference/Codex CLI, mount host drives or execute model-generated CP058 source. No production or customer work was touched.
