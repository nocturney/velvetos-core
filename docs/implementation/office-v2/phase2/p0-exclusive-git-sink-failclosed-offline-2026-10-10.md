# Office 2.0 / #604 — Exclusive Git sink: fail-closed OFFLINE probe (2026-10-10)

**Verdict: Mac synthetic selftest 32/32 PASS; DESIGN ONLY / NOT_ADMITTED.** Consumer #612. This is a new gate after protected merged PR #670, not a repetition of its live Git writes.

## Prior evidence and motivation

PR #670 really demonstrated an expired etcd generation-2 owner whose native GitHub scratch-ref SHA CAS was ACCEPTED before the generation-5 marker cutover. The later marker blocked only the tested stale-expected-SHA operation. No global etcd/GitHub atomicity, source-authenticated credential exclusivity, mid-push expiry fencing, or production authority is proven.

## Proposed #604-owned trust contract (not deployed)

1. Credential custody: a single isolated Windows Git sink alone may hold a least-privilege authorized Git credential. Workers/model processes cannot receive it. Today's existing Windows native credential is NOT proven isolated from other same-user processes; do not modify Git authentication, security policy or firewall as part of this fixture.
2. Authority: #604 owns one provider/lease/epoch authority; worker-provided epoch, Git expected SHA and actor must be independently checked against authenticated live provider state. There may be no second scheduler, authority or lease SoT.
3. Admission: deny wrong repo/ref/protected main, stale actor or epoch even with a CURRENT remote SHA, revoked/expired owner, pending cutover, provider or remote read failures, concurrency and unresolved UNKNOWN.
4. Serialize and record a durable intent in the canonical #604 provider-backed ledger BEFORE external Git push; recheck authenticated owner immediately before dispatch. An in-memory dictionary or local mutex is not crash durable and does not enforce credential custody.
5. Git effect: sanctioned exact-ref conditional push only, never unguarded force or protected main. Remote Git SHA CAS is atomic only in GitHub; preflight cannot make it one atomic transaction with etcd. A native push may still finish after the lease expires.
6. Readback: independent exact remote SHA/commit plus provider owner read; only full matching evidence may establish the effect for a bounded LAB. Lost ack, partition, post-push provider revision change, missing process termination or remote uncertainty -> UNKNOWN_EFFECT_RECONCILE, fail closed.
7. Reconcile: first establish that the old push can no longer complete, inspect the authoritative intent and provider history and compare remote ref/commit. Whether remote advanced, unchanged or conflicted, preserve UNKNOWN pending human/policy review. NO blind replay, no auto-unfreeze after restart.
8. Epoch cutover: new owner remains PENDING_CUTOVER until sink-native marker commit is read back independently, then the canonical provider may activate; still no cross-store atomicity or cryptographic exclusion of old credential holders.
9. Crash/failover: prohibit overlapping credential holders; prove durable intent restore, interrupted process termination, scoped credential revocation/isolation and independent remote readback before any live autonomous admission. Keep historical FAILED/UNKNOWN records unchanged.

## New isolated OFFLINE artifact

Source: scripts/vf_office_v2_604_exclusive_sink_failclosed_offline.py

Mac local isolate: /Users/chris/Velvet/Pilots/OfficeAccelerator/AgentEnvelopeLab/p0-git-sink-failclosed-offline-20261010.

Source Mac SHA256 before PR upload: 6b3e67c6d226b785474893f5d37ae3edad2fb6904b7fc3f97d910598b84c4ad3. Verify exact canonical blob bytes from independent Windows checkout.

Run via Python standard library:
- python3 scripts/vf_office_v2_604_exclusive_sink_failclosed_offline.py selftest
- python3 scripts/vf_office_v2_604_exclusive_sink_failclosed_offline.py verify

32 synthetic negative/positive tests: active vs expired/revoked/pending owner; wrong actor/epoch when ref SHA is CURRENT; provider outage before dispatch, second read and after push; mid-push expiry actually allows synthetic remote advance but reports UNKNOWN; lost Git acknowledgment with unchanged/advanced/conflicted remote; terminated vs possibly still active writer; UNKNOWN blocks new actions and survives simulated sink restart; disallow protected main/wrong repo/malformed SHA; stale remote CAS, concurrent competing ref change, remote read failure, duplicate intent; concurrent requests serialized within one process; all critical nonclaims remain false.

Selftest reports PASS_OFFLINE / tests 32 / production_effects 0 / network_git_writes 0 / paid_api_calls 0 / unknown_auto_replays 0. Verify reports DESIGN_ONLY_NOT_ADMITTED. Neither mode invokes Git, network, model API, filesystem effects, certificates or live provider.

## Explicit nonclaims

| Gate | Current evidence |
| --- | --- |
| Offline test fixture | 32/32 Mac PASS; independent Windows and protected PR CI pending |
| Credential-owning exclusive process isolation | NOT PROVEN |
| Real mid-push lease-expiry fencing | NOT PROVEN; simulated gap actually advances remote |
| Durable provider-backed write-ahead intent | NOT IMPLEMENTED (in-memory only) |
| Actual remote lost-ack recovery | NOT PROVEN (synthetic only) |
| HA/quorum/partition and real two-host writer failover | NOT TESTED |
| #612 autonomous protected agent PR acceptance | BLOCKED pending #604 |
| Production promotion | DENIED, P0 still PARTIAL |

## Next narrow proof

Independently run exact-head tests on clean Chris Windows; require protected PR CI, independent QA and postmerge before claiming repository delivery. Then plan a separate scoped native scratch-ref experiment with operator-approved isolated credential custody, exact provider/remote live readback, interrupted native push, UNKNOWN, and old generation equipped with the **current** Git ref SHA. Do not touch the stopped historical #670 etcd DB, deleted keys, Windows security settings, production branch, business actions, 3D work, Dagu or printers. Do not invoke Codex CLI or any paid model/API. Record a real BLOCKED rather than claiming production readiness if credential isolation cannot be established.
