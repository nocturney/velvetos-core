# Office 2.0 / #604 — Native local Git crash and durable UNKNOWN reconciliation (2026-10-10)

**Verdict: OFFLINE process-crash LAB: 19/19 PASS independently on Chris Windows and MacMiniOffice.local. No live GitHub write, authenticated provider, credential custody, or production admission.** Consumer: #612, not granted authority.

## Scope after #670 and #671

Historical protected PR #670 proved a REAL stale actor GitHub write was accepted after authentic etcd TTL expiry while the Git ref remained unchanged. The later generation marker blocked the tested stale-expected-SHA request; this did not protect against an expired actor holding the current SHA or another credentialed process.

Protected PR #671 added an in-memory fail-closed model with 32 offline tests. The current probe adds an actual **native local Git ref CAS**, a committed SQLite write-ahead effect intent, two genuinely separate local processes and forced process deaths on both OSs. It is **only** a disposable LAB, not a new scheduler, lease authority, source of truth, runtime migration, or second durable-engine selection.

## Exact experiment

- Source: scripts/vf_office_v2_604_native_git_crash_reconcile_offline.py.
- Isolated scratch ref: refs/heads/vf604-offline-local-only inside a new temporary bare Git repository. No remote is configured. No GitHub, Git token, user Git credential helper, TLS service or network call is invoked.
- Intent is inserted as EFFECT_IN_FLIGHT in a local SQLite receipt fixture using BEGIN IMMEDIATE / synchronous FULL *before* a native git update-ref compare-and-swap. A synthetic provider JSON observation supplies actor, epoch, TTL and revision. This JSON is emphatically **not an authenticated canonical provider**.
- Child exits using os._exit(91) after intent commit but before Git: durable journal remains, ref unchanged. Reconciliation returns REMOTE_UNCHANGED_REVIEW_REQUIRED, never a blind retry.
- Child exits using os._exit(92) immediately after native local Git update-ref accepts candidate but before any local success receipt: ref advanced, SQLite row remains EFFECT_IN_FLIGHT, fresh reconciliation returns REMOTE_ADVANCED_REVIEW_REQUIRED, keeps UNKNOWN frozen and forbids replay.
- A separate physical process attempts new work while an earlier effect remains EFFECT_IN_FLIGHT: SQLite-backed fixture refuses it; simulated process handoff never clears UNKNOWN merely because a program restarted.
- A deliberately independent process can invoke local git update-ref directly and bypass the fixture sink. **This explicit negative result prevents claiming OS isolation, credential exclusivity or globally enforced fencing.**
- Provider revision change before or after effect, lost acknowledgement, conflict, unreadable provider and corrupt journal preserve fail-closed/no-replay semantics. A cross-store lease-expiry-versus-remote-write race is still NOT solved.

## Independent host evidence

MacMiniOffice.local: macOS 27.2 / Python 3.9.6 / Apple Git 2.54.0.
Chris: Windows / Python 3.11.9 / Git 2.55.0.windows.3.

Both independently ran selftest: PASS_OFFLINE, tests=19, exit 0. Source SHA256 on BOTH hosts: **2bbd81c9c7f59c1b28937286d1c365ca46c0ceb9db96157859f7225e0dd6d632**. Verify mode returns DESIGN_ONLY_NOT_ADMITTED, zero external_git_writes, unknown_auto_retries=0, credential_exclusivity_proven=false, provider_authoritative_journal_proven=false, mid_push_lease_expiry_fenced=false and production_authority=false.

Mac new isolated lab: /Users/chris/Velvet/Pilots/OfficeAccelerator/AgentEnvelopeLab/p0-git604-native-crash-reconcile-offline-20261010

Chris Windows new isolated lab: D:\Velvet\Pilots\OfficeAccelerator\AgentEnvelopeLab\p0-git604-native-crash-reconcile-offline-20261010

Commands from repository root:
- python scripts/vf_office_v2_604_native_git_crash_reconcile_offline.py selftest
- python scripts/vf_office_v2_604_native_git_crash_reconcile_offline.py verify

Nineteen selftests cover valid native CAS/readback, two genuine subprocess crash points, lost ack before/after effect, old actor with **current SHA**, expired/revoked/PENDING owners, provider outage, provider revocation on either side of native update, competing processes, duplicate idempotency key, invalid repo/ref/SHA, actual bypass through a direct local Git update, remote conflict, provider outage while reconciling, restart with unresolved intent, corrupt durable local fixture DB and negative production claims.

**Cross-platform issue found and fixed:** First Windows QA found that SQLite context manager alone did not close a file handle, causing WinError32 during temporary test teardown. Explicit contextlib-managed connection closure was added to the same source on both computers. Full tests were then rerun: 19/19 on each host, matching exact SHA. The initial FAILED run is not reclassified as PASS.

## Nonclaims and remaining gates

| Gate | State |
| --- | --- |
| Local native Git SHA CAS, SQLite process-crash write-ahead journal | PASS OFFLINE 19/19 each physical host |
| Process crash after accepted local ref update before receipt | PASS OFFLINE: ref advanced, pending durable journal, UNKNOWN review |
| Two local processes competing and pending admission denied | PASS OFFLINE within disposable SQLite fixture |
| Direct outside credential holder prohibited | NOT PROVEN; deliberate local bypass succeeds |
| Provider/lease/epoch authenticated and authoritative | NOT PROVEN: JSON is synthetic |
| Effect outcome durable in canonical #604 provider system | NOT IMPLEMENTED; local SQLite is disposable evidence, not a SoT |
| Native GitHub mid-push lease expiry / network partition / two native hosts writing | NOT PROVEN |
| Global etcd/Git atomicity, exactly-once and failover | NOT PROVEN |
| Production promotion / #612 autonomous protected worker writes | BLOCKED; P0 PARTIAL |

## Next owner gate (no implicit approval)

The next proof is not another synthetic green count. #604 must agree a *single* canonical approved provider and authoritative durable intent contract, then isolate one least-privilege Git credential holder so that all worker and same-user bypass paths are denied independently. A GitHub credential helper merely being configured on Windows LocalSystem or Mac Chris does **not** show custody isolation. A scoped GitHub App identity or broker may be evaluated as a design; provisioning credentials, changing OS/global Git auth/firewall/trust/autostart, production promotion and bypassing protected Git branches require explicit approval and independent review.

With that gate proven, conduct only an explicitly authorized short-lived two-host scratch-ref fault test for old generation with the **latest** SHA, actual delay/expiry during push, unknown acknowledgement, crash after native Git acceptance and independent provider/GitHub readback. Do not retry existing FAILED/UNKNOWN, set up second scheduler or SoT, call Codex CLI/paid API, or affect production business/Instagram/CAD/printers.

Historical #670 stopped etcd DB and receipts remain untouched, as do all prior project UNKNOWN journals.
