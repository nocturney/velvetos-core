# #604 / CP083 — native Git+SQLite lost-ACK and two fresh receipts (2026-10-18)

**Scope: authored independent native-local subgate proof, not CP083 full-chain admission. merged into main via #764 (9c2f3347); lab-only, SECURITY RED.** This work was a separate branch stacked on closed #755 at `e065552825d64e9151dca0a53d4b3c7a896ab479`. Guest kernel UIDs, etcd mTLS/RBAC, protected Core issuer, remote GitHub effect and independent QA are **out of scope and NOT proven**. That merge does not admit the full chain or authorize deploy.

## Exit criteria and observed proof

| Claimed subgate | Required evidence to close its **native-local** portion | Actual fresh evidence / outcome |
|---|---|---|
| Native Git/SQLite lost ACK | Execute the **existing CP083 native implementation** (`OfflineLab`) from a new subprocess against fresh marker-guarded LOCAL bare Git and SQLite (`PRAGMA synchronous=FULL`). Kill the subprocess before and after native ref update with **no returned ACK**, independently re-open Git/SQLite in another process, classify changed/unchanged ref, retain `UNKNOWN_EFFECT_RECONCILE` and deny a blind second effect. Exercise an injected ACK-drop for each position, a normal successful readback, a genuine native compare-and-swap stale rejection, and a synthetic revocation-after-write uncertainty path. | **Local-only tested**, on two physical Mac hosts below; each run exercised six independent throwaway Git+SQLite cases. Unexpected exit 91 (before write) left the old ref; exit 92 (after native Git write) left the candidate ref. Both lacked an ACK. Separate-process readback classified them `REMOTE_UNCHANGED_REVIEW_REQUIRED` and `REMOTE_ADVANCED_REVIEW_REQUIRED` respectively, froze durable UNKNOWN, and denied repeat attempts. Normal accepted native CAS, read back commit, refused a duplicate and rejected a stale native CAS. |
| Two receipts | Two genuinely **new** run-specific receipts (not historical #738 receipts), each complete enough to audit exit code, native ref SHA, SQLite reopened state, ACK observability, attempted second effect, source bytes and host. Immutable raw LF UTF-8 plus SHA256; separately runnable fail-closed validator rejects missing/altered or promoted results. | **Two fresh runs observed**, `MacMiniOffice.local` and `Mac-Bedroom.local` via their separate connected Desktop Commander devices. Different run IDs, distinct host-local Git versions, 58/58 authored assertions per host (116 total). Raw receipt bytes pinned below. Verifier `--selftest` passed on **both hosts**, rejecting **12/12** tamper/false-authority mutations on each host. |

## Exact provenance and hashes

- Base stacked PR: [#755](https://github.com/nocturney/velvetos-core/pull/755), head `e065552825d64e9151dca0a53d4b3c7a896ab479`.
- Existing native implementation consumed by the hardened candidate: `scripts/vf_office_v2_604_native_git_crash_reconcile_offline.py`, SHA256 `2bbd81c9c7f59c1b28937286d1c365ca46c0ceb9db96157859f7225e0dd6d632`.
- Hardened CP083 candidate SHA256 (pinned, **not executed end-to-end**): `39b0c918f906980f1ba87c49a03cc6cbf10b4d144b157b3221605a14ad3626b6`.
- New actual fault-runner: `scripts/vf_office_v2_604_cp083_native_lostack_two_receipts.py`, SHA256 `0d38f4e45f1d94a64167b72e0f57ca44efa73a758fc72fe368705294de737251`.
- New fail-closed receipt validator: `scripts/vf_office_v2_604_cp083_native_lostack_receipt_gate.py`.
- Two original raw receipts (LF in JSON seal): `p0-604-cp083-native-lostack-two-receipts-2026-10-18.json` (adjacent to this document).
  - `MacMiniOffice.local`: run `c1467e777e344317959365284ad0492b`; SHA256 `c3dab4f9582f7aa25cdff4ce4e5a85db15e9c9918569011333a7e9e8a71538f0`; 7,497 original UTF-8 bytes; Apple Git 2.54.0.
  - `Mac-Bedroom.local`: run `75abc400aa44432b8c884f08eea88728`; SHA256 `5dbc39e1824b910718bc45344bcffad7845db486bfc534664b7a8b4715035947`; 7,493 original UTF-8 bytes; Apple Git 2.50.1.
- Both observed `Darwin arm64`, Python 3.9.6 and SQLite 3.54.0. Native `git update-ref` and `rev-parse --verify` were real local subprocesses; SQLite journal `delete`, `synchronous=FULL` requested, reopened in new interpreter processes. No GitHub remote was configured or written.

## Reproduction and independent review

From a clean checkout of the **exact PR head** (not a historical #738 head):

```sh
python3 -B scripts/vf_office_v2_604_cp083_native_lostack_receipt_gate.py --selftest
python3 -B scripts/vf_office_v2_604_cp083_native_lostack_two_receipts.py --run local-review
```

The second command creates **fresh local-only** disposable Git/SQLite fixtures, prints a **new** receipt (not the two sealed receipts), then removes its temporary directories. Python 3.9+, native Git and SQLite are needed. It needs no root, guest provisioning, socket service, token or network. The verifier performs only offline file reads and twelve deliberately altered *in-memory* copies; its PASS is author test evidence, **not independent QA**.

## Boundaries that remain OPEN

1. This proof exercises the actual shared `OfflineLab` native Git/SQLite implementation, but **does not execute the new hardened CP083 candidate's full joined path** with Linux `SO_PEERCRED` kernel UIDs and live provider mTLS. The ARM64 machines here run macOS, not a Linux guest. The other workstream owns those gates.
2. ACK injection deliberately discards a worker's stdout at the local test boundary; it is **not a real remote network failure**. Separately, the native child _exited immediately_ before or after the ref mutation without sending any ACK. Neither proves remote GitHub write reconciliation, a protected issuer, a true CAS-vs-provider atomic operation or power-loss durability.
3. The revocation-after-Git case is a **synthetic file-backed provider observation**, not a live etcd revoke. Local Git's `update-ref` cannot atomically commit an etcd transaction. An outsider able to write the raw ref remains out of scope.
4. SHA256 detects changed evidence when pinned to these bytes, but is **not a signature or cryptographic attestation of machine identity**. Device provenance derives from the two authorized remote-execution endpoints; reviewer must corroborate independently. The receipt validator checks the values but is not itself a security review.
5. No legitimate remote GitHub push/ACK loss, autonomous coding workers, production/customer effect, live guest or credential mutation, external independent security review, QA approval or CI result is asserted here. **`security_admission=RED`; merged into main via #764 (9c2f3347); lab-only, SECURITY RED.**

## Reviewer handoff

Verify receipt SHA256s against the original raw LF strings, source pins, six native-case outcomes and explicit denial of every duplicate. Try altering the source, a raw byte, a host/run identity or an UNKNOWN-to-COMMITTED claim; the exact-byte gate must fail closed. Decide **only** the two narrow native-local/receipt subgates. Request full joined Linux guest and provider work as separate evidence before treating CP083 as an admitted chain. The author must **not self-QA or self-merge**; any later integration uses a normal merge commit only, not squash, force-push or admin bypass.
