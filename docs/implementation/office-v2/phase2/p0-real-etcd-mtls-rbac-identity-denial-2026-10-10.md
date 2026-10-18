# Office 2.0 / #604 — REAL temporary etcd mTLS/RBAC identity-denial lab (2026-10-10)

**Verdict: 25/25 real Mac mTLS/RBAC checks PASS; 13/13 portable checks PASS. NOT production, NOT exclusive GitHub Git writer and NOT separated OS principals.** Owner #604; downstream consumer #612.

## Purpose and historical boundary

This experiment follows protected merged PRs #670, #671, #672 and #673. In #670 an actual expired etcd owner successfully wrote a real GitHub ref after lease expiry because the ref SHA was unchanged. #673 proved real etcd transaction and unleased pending intent survived provider SIGKILL + same WAL restart, but used an unauthenticated local provider. The current test adds actual client certificate identity, etcd RBAC and denial tests. It DOES NOT reverse the #670 stale-credential GitHub negative or prove a single Git credential owner.

## Authentic and isolated experimental inputs

Source: scripts/vf_office_v2_604_real_etcd_mtls_rbac_identity_lab.py

Mac original source SHA256: b74c4b8a1baee7cc534ee82f7abede8c9b0c154ea9693143bb36d7c09319948c

Pin: etcd 3.6.15 darwin/arm64 executable SHA256 dd2596ab902c23252da55e770cb7f7216522ae5599f84d2a20e0e7272d52fe82 and etcdctl SHA256 05f34d3be92b0ba78dfc5aa9fd5d63224d551a7f8c2eadfbaa7dc2f35ae625ad. Both are hashed before launch, not downloaded, replaced or installed. The source verifies the hashes.

Isolated Mac workspace: /Users/chris/Velvet/Pilots/OfficeAccelerator/AgentEnvelopeLab/p0-604-mtls-rbac-identity-isolation-20261010

Each run creates a distinct private 0700 temporary directory inside that lab, generates an ephemeral CA private key, a server TLS certificate with SAN IP:127.0.0.1, and passwordless CN certificate identities root, vf604-sink and vf604-worker; an outsider certificate signed by the same CA but not enrolled as a user, and a forged sink-CN certificate signed by a different untrusted CA. Private keys have 0600 permissions. No credentials are installed in macOS Keychain, Git or a global trust store. All test keys, certificate serials, users, roles, WAL and server log are confined to the temporary directory and deleted during cleanup.

The temporary server binds ONLY the loopback interface, using HTTPS mutual client TLS for client connections; its temporary peer listener is HTTP on loopback. This is NOT a secure multi-host peer-cluster test. Real etcd passwordless certificate-CN user authentication and RBAC are enabled in that disposable database. The sink role may read/write a uniquely randomized test prefix. The worker role may READ only the single owner key; not the unleased effect intent, and not any other key. A valid unregistered cert is not sufficient for authorization.

## Actual checks passed — 25/25

1. Real loopback TLS server is healthy.
2. Missing client certificate denied.
3. Fake sink CN signed by WRONG CA denied.
4. Passwordless user/CN RBAC enabled on real etcd.
5. Trusted CA client with unknown user CN denied.
6. Sink writes synthetic owner key.
7. Sink writes synthetic intent key.
8. Worker reads ONLY its assigned owner key.
9. Worker cannot read intent.
10. Worker cannot change owner.
11. Worker cannot change intent.
12. Worker cannot read other keys.
13. Worker cannot create unassigned key even inside sink prefix.
14. Sink cannot write outside its assigned prefix.
15. Sink cannot manage RBAC users or roles.
16. Real TTL lease attached to owner.
17. Real authenticated etcd transaction succeeds only on BOTH owner.mod_revision match AND intent.version==0; intent is written WITHOUT a lease.
18. Actual TTL expiration deletes owner, not unleased intent.
19. New-owner transaction fails because pending intent exists, even when owner lease is gone.
20. Real etcd SIGKILL, fresh process using SAME private WAL: exact pending intent value, revision and lease-free state survive.
21. Worker still denied read/write on intent after provider restart.
22. Root CN and RBAC still work after restart.
23. Sink scope still enforced after restart.
24. Pending UNKNOWN remains unreplayed; no new owner or auto-resolution.
25. All native GitHub writer, OS custody and production nonclaims remain FALSE.

**Important negative finding:** All temporary client private keys are owned by ONE macOS user, chris, so another process with the same operating-system identity might access the sink or root key. This lab demonstrates enforceable server-side identity/role access for separate client certificates only when those private keys are actually protected. It does not establish OS-user separation or credential secrecy and never connects to native GitHub.

## Real debugging failures, documented rather than reclassified

Initial post-auth calls through the etcd HTTP JSON gateway returned HTTP 400 for an authorized certificate-CN client. That path was NOT authenticated enough to rely on and must never become an assumed fallback. Final code makes the HTTP JSON post method unconditionally refuse with REFUSE_HTTP_JSON_GATEWAY_IDENTITY_NOT_PROVEN. Final authorized operations use native mTLS-authenticated etcdctl gRPC only.

The first txn commands failed with EOF due to an incomplete input grammar: etcdctl expects a terminated empty failure-request section after success-request lines. The test now supplies the required extra final newline and strictly parses a response with a revision-bearing header. Omitting false transaction results (protobuf JSON default) is accepted ONLY for a valid revision-bearing result; malformed responses are not promoted to successful CAS. After these corrections, the entire live suite PASSED 25/25 from scratch, and the portable suite PASSED 13/13.

## Reproduction / CI safety

Run portable only on Windows or Mac: python scripts/vf_office_v2_604_real_etcd_mtls_rbac_identity_lab.py selftest (13/13). Mode verify returns DESIGN_ONLY_NOT_ADMITTED with all live proof flags false and no network/server/credential creation.

Actual attended Mac-only proof requires the pinned local etcd, pinned local etcdctl and the exact guarded Mac lab root. Only integration mode starts ephemeral provider and creates ephemeral credentials, and only after 25 real checks pass may output PASS_REAL_LOCAL_MTLS_RBAC. The Windows/GitHub CI contract should pin the exact source hash, run portable 13/13 and verify false live/production claims. It does NOT perform live TLS or use a privileged credential.

Read-only post-run inspection found ZERO remaining disposable certificate/data directories, ZERO active matching etcd daemon and unchanged closed historical ports. #670 receipts/WAL are left untouched.

## Remaining owner-controlled blockers

- REAL OS/security-principal isolation of the SOLE Git credential-holding sink from all untrusted worker identities; Mac same-user and Windows remote LocalSystem are insufficient.
- Production provider identity, scoped RBAC and mutual TLS over TWO authenticated physical hosts, secure inter-peer transport and only one approved provider authority, with guarded durable pending-intent control.
- GitHub ref restrictions: verified repository ruleset #23284099 applies to the DEFAULT branch, not proved to cover historical LAB refs. Repo-scoped app installation alone would not restrict writes to a particular ref. Current GitHub connector permission is not a native Git process identity proof.
- Expired worker with CURRENT Git SHA must be denied by live credential security; native mid-push expiry, partitions, lost acknowledgement and reconciled UNKNOWN require a separately owner-authorized real GitHub scratch experiment. Never assume etcd lease and GitHub CAS are atomic.
- #612 agent-authority admission and production remain BLOCKED / P0 PARTIAL. No Codex CLI, paid model API, new scheduler, production writer, customer/social/print/CAD effects, global Git credential/OS security/trust/firewall/autostart modification performed.

The test is safe evidence and an enforceable offline CI denial contract — NOT admission or deployment.
