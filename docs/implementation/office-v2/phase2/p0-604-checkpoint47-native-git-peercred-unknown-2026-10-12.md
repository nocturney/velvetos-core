# Office 2.0 / #604 — Checkpoint 47: kernel peer-UID isolated **native local Git** sink with durable UNKNOWN recovery

**When:** 2026-10-12 (Asia/Jerusalem)  
**Status:** `LAB_ONLY_PASS / NOT_ADMITTED / NO_PRODUCTION_AUTHORITY`  
**Continuation:** [Checkpoint 46 / PR #706](https://github.com/nocturney/velvetos-core/pull/706), canonical main observed at baseline `d158ed121190b5786948c5f1a71ae3f4a8afa769`.

## 1. New, narrower claim — what actually changed

Previous Checkpoint 46 ran a Linux kernel `SO_PEERCRED` identity and filesystem isolation lab, but its effect and lease were *both* rows inside **the same SQLite fixture**. Earlier historical #604 experiments exercised local native Git write-ahead / crash semantics, but **did not demonstrate credential-owner OS principal isolation inside the same native-Git test**. This new lab connects those distinct boundaries in a **single self-contained execution**:

- Ephemeral Linux sink subprocess actually drops to numeric UID `62001`. Separate worker processes run under `62002`, `62003`, and attacker UID `62004`. No OS account is created. Kernel peer credentials, not asserted Worker labels, determine admission to an otherwise accessible UNIX-domain socket.
- The sink alone can access an `0700` isolated **native bare Git repository** and a `0600` fake credential; direct Worker attempts to read/write repository, fake credential and SQLite journal are denied by Linux permissions. A native Git `update-ref <ref> <new> <expected>` makes a **real local Git object/ref effect**, not a synthetic SQLite ref-row change.
- The controller rotates a synthetic epoch from Worker A to B **without changing the real local ref SHA**. A's real Git SHA is exactly current and its proposal is nevertheless denied by the sink's local authorization. Three distinct processes from two Worker UIDs race; only one native Git ref effect is committed and read back under a different local SQLite journal.
- Injected **trusted-harness-only** crash before `git update-ref` preserves durable `EFFECT_IN_FLIGHT` intent while leaving Git unchanged. Injected crash after Git effect and before SQLite terminal receipt/ACK leaves Git changed with SQLite still in flight. On *both* restarts, the sink transitions durably to `FROZEN_UNKNOWN` and refuses automatic retry. Root-controlled manual reconciliation distinguishes `MANUAL_CLOSED_NO_RETRY` from `COMMITTED_VERIFIED` using native local Git readback, after the controller verified prior PID exit. A Worker request to activate fault injection itself is denied.

**Critical distinction:** this is **local Git + local SQLite in the *same OS* under one sink UID**, not a real distributed provider or GitHub API. Their writes are *not atomic together*; in fact, the post-effect/pre-ACK crash intentionally demonstrates that gap.

## 2. Observed results

| Evidence | Observed outcome |
| --- | --- |
| Disposable Linux exact source | `vf_office_v2_604_native_git_peercred_unknown_lab.py`; SHA-256 `e0c5a53aea2b54d4f13fe33d9cf4b635268da517327eb8488dd7a2332081c41d` |
| Exact original positive receipt | `vf604_checkpoint47_primary.json`; SHA-256 `5fb8bb725bbc8c2b8111c5a4b2848197f879784fec34de8f56ec72f751c9f56c` |
| Positive source-byte-identical rerun | 20/20 PASS, exact same original source SHA-256 and receipt digest; `vf604_checkpoint47_final_run_a.json` |
| Additional diagnostic-instrumented repetitions | Three separate 20/20 PASS runs (`vf604_checkpoint47_run_2` through `_4`) while temporary tracing was added, i.e. a *different* code digest; distinguish from exact-byte runs |
| Intentional **stale-epoch-guard bypass** mutation | `18/20` FAIL-CLOSED: N08 stale/current Git SHA and N09 cross-UID native Git single-writer checks failed. Raw receipt SHA-256 `bc2b6a0aceee9539e46694e318f25f5e545142ce5ab43e8fd85bd4a5cb4bb043` |
| Intentional **UNKNOWN-on-restart bypass** mutation | `16/20` FAIL-CLOSED: N13, N14, N16, N17 failed. Raw receipt SHA-256 `0d0c06254a392176851b08346d9914028cc7a2c028eb0baca5c6a2e4ba8ebaf8` |
| Real physical host modifications | **0** — only the disposable assistant container; no OS accounts, TCP listeners, services, production credentials, GitHub writes or external API calls |
| Test cleanup | No remaining `vf604-git-peer-*` temp dirs or active sink/worker processes after the completed tests. One earlier tool-interrupted diagnostic run left a disposable scratch directory and was explicitly cleaned; do not silently count it as a clean pass |

Raw mutation **failed** statuses and all unpassed case IDs are kept. Never sanitize or count those unsafe-mutant runs as successful integration tests.

## 3. Specific acceptance probes (20)

N01: initial real Git SHA; N02: filesystem denial on fake secret, SQLite, bare Git and direct native Git write; N03: false Worker ID rejected by Linux UID; N04: unregistered principal rejected; N05: remote GitHub capability rejected; N06: Worker cannot rotate; N06B: Worker cannot invoke fault injection; N07: trusted synthetic epoch rotation leaves real Git ref unchanged; N08: old owner with **current real *local* Git SHA** denied; N09: three-process two-UID native local Git single writer; N10: Git readback and durable intent agree; N11: duplicate intent refused; N12: crash pre-Git with durable in-flight intent and no ACK; N13: restart freezes UNKNOWN without automatic replay; N14: manual no-effect closure; N15: crash post-Git before ACK keeps real changed ref and unresolved journal; N16: restart freezes unknown and denies retry; N17: manual verified-Git reconciliation; N18: no second effect after reconciliation; N19: provider-fixture outage denies native Git effect.

## 4. Auditability, safeguards and strict nonclaims

**Invocation safety:** The source prints a refusal unless it runs as root on Linux, `SO_PEERCRED` exists, four numeric UIDs are unassigned and the opt-in `VF604_DISPOSABLE_LINUX_LAB=YES` is present. It creates only marked cryptographically unpredictable disposable directories beneath OS temp; subprocesses drop OS UID/GID and lose supplementary groups; socket access is open enough for adversarial probes but trusted Linux peer UID is enforced. Git commands are forced to a new sink-owned local **bare** repo and restricted to `file` transport, with no GUI/network/provider keys. Trusted controller scenarios `race`, `before`, `after`, `outage` own failure injection; untrusted Worker cannot request service death. Python bytecode and Git process EUID remain within the ephemeral scope. No user host touched.

**Unproven (do not promote):** Real GitHub ref/API write and GitHub scoped credential exclusivity; external etcd lease generation/lease expiry races across two physical hosts; effects finishing *after* lease expiration or network partitions; provider-Sink atomicity; genuine mTLS SAN / CN to Dagu Worker ID binding; Windows SYSTEM and macOS UID501 least-privilege process identity; Windows/macOS process-tree cancellation / C1 sentinel; native remote lost-ACK/quarantine; remote verification independent of the sink owner; authorization for autonomous local-model generated code. The process acting as root in the disposable Linux test could bypass the fixture, so this does **not** prove protection against an OS administrator.

**Caution:** The code is an adversarial probe, not reusable production machinery. Numeric-UID isolation in an ephemeral root container is deliberately different from provisioning a separate least-privilege permanent account on a company PC. The output `COMMITTED_VERIFIED` is local Git under the fixture and cannot be generalized to externally distributed exactly-once.

## 5. Recommended next gate — explicit owner approval required

Before any LAN Worker, real GitHub scratch ref or credential change: decide per-host least-privilege OS principal and independently held Git Sink credential; approve dedicated scope/ACL, ephemeral certificate/key custody, rollback and `main` exclusion; then test expired-authorized-host with **current *GitHub remote* SHA** against an actual provider-validated Sink. Detect stale writer denied **at the only write gateway**, reconcile ACK loss and provider outage from a third verifier. Preserve historical #670 real stale-owner ACCEPT as unresolved until that denial is seen. #604 remains `OPEN/RED`; #612 remains `OPEN/PARTIAL`.

## 6. Offline replay (disposable Linux container only)

`python3 vf_office_v2_604_native_git_peercred_unknown_lab.py verify` is non-executing / non-admitted.

Only after independently confirming disposal and absence of real accounts with UIDs 62001–62004: `VF604_DISPOSABLE_LINUX_LAB=YES python3 vf_office_v2_604_native_git_peercred_unknown_lab.py lab`. Do **not** execute it on the user's Windows or macOS devices, with customer data, privileged OS accounts, Dagu, or actual GitHub token.
