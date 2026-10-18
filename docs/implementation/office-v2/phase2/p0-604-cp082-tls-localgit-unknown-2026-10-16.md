# CP082 — joined real etcd mTLS/RBAC to durable native local Git

**2026-10-16 · Office #604/#612 · LAB ONLY · `security_admission=RED`**

This closes one *integration-lab* gap between CP081's real, authenticated etcd admission and the pre-existing native bare-Git + SQLite/UNKNOWN crash-reconciliation harness. It does **not** close the production GitHub, separate-OS-principal or two-host generated-code gates.

## Execution and exact evidence

On the **existing** MacMiniOffice2 Colima `velvet-qa` Linux aarch64 guest (nonroot), a Python 3.12-authored script starts one new throwaway etcd 3.6.15 server per run, with fresh temporary CA, mTLS certificate identities, scoped etcd RBAC and a randomized key prefix. It atomically commits a real CP081 grant. A separate, sink-authorized mTLS certificate reads the grant before attempting a **real, local-only** bare-Git ref CAS backed by SQLite `synchronous=FULL` intent rows.

Two fresh provider instances completed **26/26 checks each (52/52 total)**. Original newline-terminated JSON results and SHA256 hashes, together with distinct randomized provider namespace hashes and all source/dependency pins, are sealed in [CP082 JSON evidence](p0-604-cp082-tls-localgit-unknown-2026-10-16.json). Exact script SHA256: `fa108cfd9bea1aec38a9e7e4c1a3e369e6ba4be94eef413ea0ec0304bb1a8eee`.

## Real effects and negative paths

| Test family | Expected result |
| --- | --- |
| Authenticated, durable grant and native local-Git CAS | `COMMITTED_READBACK`; exactly matching local ref |
| Root revokes grant before native Git | `DENIED_STALE`, ref unchanged |
| Revoke between successful native Git and final provider readback | Persistent `UNKNOWN_EFFECT_RECONCILE`, never a safe success |
| Reconciliation after apparent remote advance | `REMOTE_ADVANCED_REVIEW_REQUIRED`; no blind retry |
| Simulated ACK loss *after* native Git | Durable `UNKNOWN`; subsequent request blocked |
| Simulated ACK loss *before* native Git | Durable `UNKNOWN` with ref unchanged; still no blind retry |
| New SQLite reader after either lost-ACK case | Previous freeze still applies |
| A committed grant followed by revocation | `DRAINING_ADMITTED`, reservation preserved; no new effect admitted |

The Git ref exists only at `refs/heads/vf604-offline-local-only` inside a fresh temporary bare repository; no GitHub remote is configured or contacted. The provider's issuer is an unprivileged *synthetic root within the fixture*, not a protected real Core issuer. The Git-writer code and the etcd TLS client share the same Linux UID in this experiment. CP077's separate UID and mTLS key custody were proven separately, **not** in this combined test.

## Why this does not mean promotion

An etcd transaction **cannot atomically fence an external GitHub write**. If revocation races with a write already admitted, the write may have happened. The fixture must preserve `UNKNOWN`, freeze additional work and require an external readback/review. It never treats expiry or revocation as proof that GitHub could not have advanced.

Remaining hard gates are: separately credential-owning OS-UID sink in *the same* live integration, authentic owner/Core issuer authority, protected remote GitHub scoped credential and CAS/ref verification, an UNKNOWN outcome that survives process/host failure with independent remote readback, owner-selected **Option A or B** revocation semantics, two-physical-host generated-code isolation/QA, and independent security review. These are not waived by green lab or CI results.

## Safe replay

Offline-only static test: `python3 -B scripts/vf_office_v2_604_cp082_tls_native_git_reconcile_lab.py --selftest`. It emits `OFFLINE_STATIC_ONLY` with `security_admission=RED` and creates no provider, Git repo or credentials.

Native lab runs **only** in an existing isolated, nonroot Linux aarch64 Colima guest. It validates exact CP081 helper and official etcd/etcdctl 3.6.15 binary SHA256 pins, rejects ambient GitHub/cloud credentials, and requires both explicit lab environment gates:

- `VF604_CP081_DISPOSABLE_GUEST_ONLY=VF604_CP081_EXPLICIT_NO_GITHUB_TEST`
- `VF604_CP082_DISPOSABLE_GUEST_ONLY=VF604_CP082_EXPLICIT_NO_REMOTE_GIT`

Native CLI: `python3 -B scripts/vf_office_v2_604_cp082_tls_native_git_reconcile_lab.py --provider-lab /tmp/vf604-cp077-tools-20261015/etcd-v3.6.15-linux-arm64/etcd /tmp/vf604-cp077-tools-20261015/etcd-v3.6.15-linux-arm64/etcdctl`. **Never use these lab gates on a production Core, physical printer or protected GitHub writer.**
