# Office 2.0 / #604 — REAL ephemeral etcd unleased intent vs native LOCAL Git (2026-10-10)

**Conclusion: bounded MAC LAB PROOF / NOT ADMITTED.** This advances #671's memory-only model and #672's native-local-Git/SQLite fixture to real **etcd v3 lease + transactional compare-and-swap + unleased provider-side pending effect**. A crash-durable pending intent survived worker process death, real lease expiry and a **SIGKILL/restart of the actual etcd 3.6.15 daemon with the same isolated WAL**. An independent local Git ref CAS can STILL be accepted after owner revocation: historical #670's real GitHub expired-writer failure remains a blocker, not overturned.

## Provenance and containment

- Source: `scripts/vf_office_v2_604_etcd_pending_intent_native_localgit_lab.py`.
- Source SHA256, Mac original lab: `cc2604fa439488970615cb564512d5fe8a58884c4c6244637f74e604812a82fb`.
- Mac workspace created fresh: `/Users/chris/Velvet/Pilots/OfficeAccelerator/AgentEnvelopeLab/p0-604-etcd-intent-crash-localgit-20261010`.
- Reused only the executable bytes of locally staged pinned **etcd 3.6.15 darwin/arm64**, SHA256 `dd2596ab902c23252da55e770cb7f7216522ae5599f84d2a20e0e7272d52fe82`; **did not open, change or reuse any prior etcd data-dir, token, historical #670 receipt or system configuration**.
- Each integration run creates its own `TemporaryDirectory` under the new workspace, randomly selects new **loopback-only** ports for client and peer, starts an **ephemeral unauthenticated** etcd process, runs tests, terminates it and deletes its disposable data-dir. No autostart, firewall change, trust store, RBAC/user credential, actual GitHub write, second scheduler, new permanent storage, system security change or paid API.
- Native Git is a **bare temporary local repository with no remote**, locked to a single `refs/heads/vf604-provider-intent-offline`, original commit-tree markers and native `git update-ref new expected`. Not a substitute for GitHub ref protection.
- CI-safe `selftest` (10 tests) and `verify` need no etcd binary. Only `integration <pinned-etcd-binary> <new-isolated-root>` can produce the positive result `PASS_REAL_LOOPBACK_ETCD_LOCAL_GIT` with 16 tests. The `verify` response deliberately keeps all live execution proof flags **false** and returns `DESIGN_ONLY_NOT_ADMITTED`.

## Transactional provider-owned unleased effect intent

The test prefix is uniquely randomized per case under `/velvetos/offline-vf604/<uuid>/`. A real etcd `/owner` key uses a genuine short lease (3–15 seconds) and stores synthetic `actor, epoch`; only the owner key is leased. Before a native local Git write, the caller reads the owner key and lease TTL, checks actor/epoch and expected Git SHA, then issues one real etcd v3 transaction with BOTH predicates:

1. Owner key `mod_revision` still equals the latest provider observation.
2. Provider intent key `version == 0` (no pre-existing unresolved effect).

Only when the transaction succeeds, an unleased, provider-persisted `EFFECT_IN_FLIGHT` intent is written. A later owner-acquisition transaction checks **both** owner key absent AND no pending intent. When the old lease expires or is revoked, the owner key disappears but the independent unleased intent remains; a new epoch cannot acquire ownership until an explicit separately authorized resolution. Even if the process crashes, no automatic intent removal or blind retry occurs.

**This is an experiment of etcd's actual transactional semantics, NOT a verified production provider identity.** The lab has no mTLS/RBAC: an untrusted local process could independently access the unauthenticated loopback server. The direct local-Git bypass remains possible. The provider transaction and native Git mutation are two separate stores and remain non-atomic; expiry between the transaction and Git is an unresolved risk.

## REAL evidence: 16/16 integration tests PASS after corrections

Actual isolated server test cases:
1. A lease-backed owner key stores genuine etcd lease ID and live TTL.
2. Unleased provider intent remains after lease revoke and prevents new owner.
3. Worker subprocess exits forcibly (`os._exit(91)`) after real provider transaction but before Git: Git unchanged, provider intent pending, manual review.
4. Worker exits forcibly (`os._exit(92)`) after Git accepted native CAS but before provider receipt: Git advanced, provider intent pending, manual review.
5. Retrying the same request is denied by durable pending intent.
6. Old actor with **CURRENT** Git SHA is denied after a new owner epoch takes over.
7. Two concurrent admission attempts contend on real etcd v3 compare-and-swap: one success, one denial.
8. Real TTL expires (not only explicit revoke); unleased intent survives and blocks new owner.
9. **Negative**: native local Git CAS still succeeds after real owner revocation when bypassing the sink.
10. **Negative**: a third-party native local Git write succeeds even with no provider intent (no OS/credential custody).
11. A conflicting local ref cannot clear pending intent.
12. Wrong actor/epoch/ref/SHA/id inputs cannot create a provider intent.
13. Provider outage refuses admission without Git effect.
14. Native Git acknowledgement alone is NOT a provider/Git atomic completion; remains UNKNOWN.
15. No remote Git, no credentials, no paid calls, all false production claims.
16. Actual etcd **SIGKILL** followed by relaunch with same disposable WAL: identical intent value and revision survive, unleased, block new owner and remain UNKNOWN.

Initial real integration run on Mac failed 5 errors + one assertion because the gRPC JSON gateway omits a `false` boolean for a failed transaction; the client incorrectly accessed `response["succeeded"]`. The fix recognizes omission **only when a revision-bearing etcd response header is present**, otherwise fails closed. A later full run completed 16/16. Added ten portable negative tests to prevent regression of omitted-false handling, malformed response acceptance, scope escape, native Git bypass, unprotected fixture marker and false production proof.

Two distinct results must never be conflated: **a provider can remember an unresolved intent after crashes** versus **the provider can prevent a credentialed stale process from completing a later Git push**. Only the first was proven here.

## Read-only live GitHub ref-policy finding — separate gate

On 2026-10-10 the GitHub connector read canonical `nocturney/velvetos-core`: one repository ruleset, ID `23284099`, `enforcement=active`, `target=branch`, `conditions.ref_name.include=["~DEFAULT_BRANCH"]`, no excludes/bypass actors, rules `deletion`, `non_fast_forward`, `required_status_checks(check-all)`. Thus **that ruleset only applies to the default branch**, not the prior `office-v2-lab-604-*` ref patterns. A separate branch-protection endpoint returned 403 to the integration; therefore do not assert the absence of every possible protection. The GitHub connector's repo capability readback reports `permissions.push=true` for **that connected app identity**; it does not establish the native Windows Git credential principal or isolate that principal from workers.

GitHub's current [rulesets documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository) scopes branch rules by target patterns, and [REST rulesets documentation](https://docs.github.com/en/rest/repos/rules) explicitly supports `~DEFAULT_BRANCH` and `~ALL`. Neither main-only CI nor source-SHA compare-and-swap proves exclusive scratch-ref writer credentials.

## Acceptance gates still OPEN / protected next action

| Required evidence | Verified state |
| --- | --- |
| Mac real etcd lease, mod-revision txn and unleased intent | **PASS 16/16 local integration** |
| Pending intent survives actual TTL and provider SIGKILL+same WAL restart | **PASS local integration** |
| Current-SHA stale owner rejected at provider admission | **PASS, only unauthenticated local fixture** |
| Direct native-Git bypass after real lease expiry denied | **FAIL / BYPASS SUCCEEDED as intentional negative control** |
| macOS/Windows provider mTLS+RBAC, independently attested worker identity | **NOT PROVEN** |
| One credential owner with worker-unreachable private key/token and GitHub-side ref scope | **NOT PROVEN** |
| GitHub native push safe during real lease expiry, timeout and lost acknowledgement | **NOT PROVEN (#670 shows unsafe acceptance)** |
| Canonical provider runtime/admission selected and deployed | **NOT AUTHORIZED / NOT IMPLEMENTED** |
| Cross-store atomicity, globally exactly-once, autonomous #612 coding/PR | **NOT PROVEN / P0 PARTIAL** |

Owner decision recommended, not executed: evaluate a **separately owned, least-privileged, repository-scoped GitHub App installation into a dedicated disposable pilot repository** plus a restricted OS process identity and a provider-authoritative durable-intent gate. Repo-scoped installation alone is NOT branch/ref-scoped; a necessary GitHub ruleset and independent deny test for other actors must be verified. Existing Windows Remote Desktop Commander runs LocalSystem and the Mac remote executor runs user chris: neither constitutes secure isolated credential custody by itself. Do not change global Git credential helper, native GitHub login, OS principals/permissions, firewall, trust store, producer services, or create a repo/app without separate explicit owner authorization. Retain historical #670 unsafe Git acceptance, original FAILED/UNKNOWN evidence and #604/#612 open. No Codex CLI, paid provider, production Instagram, CAD/printer/customer operations or second scheduler.

