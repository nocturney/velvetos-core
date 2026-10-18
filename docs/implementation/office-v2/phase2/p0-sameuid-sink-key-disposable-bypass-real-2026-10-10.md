# Office 2.0 / #604 — real disposable same-UID sink-key bypass (2026-10-10)

**VERDICT: EXPECTED NEGATIVE BYPASS OBSERVED. P0 IS NOT ADMITTED.**

This bounded Mac lab follows merged PR #674 (real local mTLS/RBAC 25/25). PR #674 showed that a process presenting its assigned Worker client cert is denied intent writes. It did NOT prove that two processes with the SAME OS user cannot read or reuse the Sink client private key. This separate real experiment proves that negative consequence with disposable credentials only.

## Sources, scope, and containment

- Script: scripts/vf_office_v2_604_sameuid_sink_key_bypass_lab.py
- Original local script SHA256: 7e2380e361e0595d817ba9ae1d217f841af36976246e246dff4a1b6f915b18fb
- Depends on the UNMODIFIED #674 script scripts/vf_office_v2_604_real_etcd_mtls_rbac_identity_lab.py, pinned source SHA256 b74c4b8a1baee7cc534ee82f7abede8c9b0c154ea9693143bb36d7c09319948c. Original is hashed before the new live test can start.
- Newly created, exclusively test-owned mode-0700 root on MacMiniOffice.local: /Users/chris/Velvet/Pilots/OfficeAccelerator/AgentEnvelopeLab/p0-604-sameuid-sink-custody-bypass-20261010
- The test creates a unique private disposable etcd 3.6.15 instance, temporary CA, short-lived sink/worker/root client certificates and private keys. All certificates and data are generated inside that isolated root and deleted after each run. The authentic etcd and etcdctl binary hashes are enforced by the reused #674 module. Both client and peer traffic are LOOPBACK ONLY; peer traffic is HTTP, not a secure multi-host cluster.
- Independent read-only host identity inventory: Mac Remote Desktop Commander executes as chris (UID 501). Chris Windows Remote Desktop Commander executes as NT AUTHORITY\SYSTEM. Neither demonstrates distinct Worker vs Sink OS principals. This lab never queries actual GitHub/native Git credential helpers, private keys, tokens or OS ACLs.
- The experimental child subprocess is deliberately GIVEN the path to the disposable Sink key. The test does not prove that a real attacker can locate a previously unknown production secret. It proves that a second process with the same Unix UID can read and reuse a known, same-UID-owned 0600 key inside a 0700 directory.

## Real Mac results — 17/17 PASS, meaning an UNSAFE negative result

1. Prior authentic mTLS/RBAC implementation pinned by byte SHA.
2. Genuine temporary loopback TLS/etcd server started.
3. Passwordless certificate-CN RBAC enabled for Sink and Worker identities.
4. Provider contains true unleased pending EFFECT_IN_FLIGHT.
5. Worker certificate can read only explicitly allowed owner key.
6. Worker certificate is DENIED deletion of pending intent.
7. Real short owner lease expires while pending intent survives.
8. Version-compare new-owner transaction is DENIED while pending intent exists.
9. The disposable sink private key is owned by the executing UID and mode 0600.
10. A second actual Python subprocess using only its real Worker certificate is DENIED.
11. Another process, with different PID but SAME OS UID, runs independently.
12. That process can READ the disposable mode-0600 Sink key; bytes never logged or exported.
13. The process presents the Sink certificate/key over genuine mTLS-authenticated etcdctl gRPC and the server ACCEPTS.
14. Using that identity, the synthetic untrusted process DELETES the previously unresolved pending intent.
15. The SAME new-owner transaction that failed before now SUCCEEDS, even though the original intended effect was never reconciled.
16. Original Worker certificate remains denied, confirming that RBAC itself still works; private-key custody is unsafe.
17. No production GitHub effects, real credentials, system accounts, global trust, paid API, scheduler, customer, social, print or CAD operations.

This result is intentionally named PASS_EXPECTED_NEGATIVE_SAME_UID_KEY_BYPASS: the assertions passed because the bypass really succeeded. All production authority / GitHub writer safety / OS isolation proof flags remain FALSE. It is a RED security gate, not a successful deployment.

The source also passed 16/16 PORTABLE negative/ownership/refusal tests. The non-executing verify mode returns DESIGN_ONLY_NOT_ADMITTED with all real proof flags FALSE. The exact fresh live experiment exited 0 and removed its own disposable certificate/WAL directory, with a separate read-only inspection confirming zero remaining fixture dirs, zero matching etcd daemons and no historical #670 ports opened. Historical #670 evidence, receipts and database were not touched.

## Comparative conclusion

- Prior #674 POSITIVE RESULT: user with only the Worker client certificate cannot read/write pending Intent under etcd mTLS+RBAC.
- Current NEGATIVE RESULT: a separate process running as the same macOS user can read the Sink private key even with directory 0700 / file 0600, can use the Sink identity to delete pending Intent, and can cause unauthorized owner takeover in a disposable provider.
- Therefore a separate PID, a separate certificate name or restrictive Unix file modes do NOT make two processes running as one Unix user separate security principals. This is NOT a failure of etcd RBAC; it is missing OS/credential custody. Similarly, Windows LocalSystem is not a safe untrusted worker identity for secrets on that host. No actual GitHub worker bypass was tested here; historical #670 separately proved an expired native actor's real GitHub write was accepted when expected SHA remained current.

## Commands and CI contract

Portable Windows or Mac: python scripts/vf_office_v2_604_sameuid_sink_key_bypass_lab.py selftest (16 independent portable tests).
Non-executing: python scripts/vf_office_v2_604_sameuid_sink_key_bypass_lab.py verify (DESIGN_ONLY_NOT_ADMITTED).
Mac real negative test ONLY when manually invoked with the two existing SHA-pinned etcd binaries and exact isolated lab root: python3 scripts/vf_office_v2_604_sameuid_sink_key_bypass_lab.py integration [local-pinned-etcd] [local-pinned-etcdctl] [exclusive-test-root].

The synthetic child mode fails closed on a non-matching test-root name, symlink, unexpected file ownership or mode, unmatched on-disk parent/nonce marker, non-loopback URL, foreign intent key prefix or unpinned etcdctl binary. The caller explicitly supplies only fixture paths. It must NEVER be used to inspect real user tokens or GitHub keys.

The portable CI gate must pin both source checksums and run selftest + verify. Portable CI must NOT create CA keys, launch a live etcd server, report live evidence or admit production. Exact PR-head Mac run of the real negative proof must be separate from Windows complete check-all=118, protected GitHub PR CI and postmerge full QA.

## Owner-only next security steps

1. Establish a separately protected least-privileged OS principal holding the ONLY native GitHub write key. Untrusted Worker code must have no ability to read the private key, impersonate it, invoke a shared Git helper or access privileged worker LocalSystem contexts. This requires explicit owner approval before creating system accounts, ACLs or moving tokens.
2. Only the canonical #604 provider may issue effect/lease authority. Prove authenticated two-host provider clients and durable unleased pending intent under properly restricted sink key custody. Do not create another scheduler or provider source of truth.
3. Independently verify GitHub scratch-ref server policy (main-only Ruleset #23284099 does not itself protect old scratch refs), then owner-authorize an isolated real GitHub native denied-direct-worker, current-SHA, mid-push lease expiry, lost ACK and UNKNOWN reconciliation test. GitHub repository-scoped app installation alone is not proof of per-ref limitations.
4. Keep #604 and downstream #612 OPEN / P0 PARTIAL, preserve UNKNOWN/FAILED events, no auto-replay and no false global exactly-once claims. No Codex CLI, paid model API, new services, production/customer/Instagram/CAD/printer effects or OS security/credential changes in this PR.

**Current security status remains RED for exclusive credential custody.**
