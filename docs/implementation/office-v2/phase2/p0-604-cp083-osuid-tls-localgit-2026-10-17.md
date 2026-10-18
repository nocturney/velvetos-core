# Office #604 CP083 — joined Linux OS-UID / mTLS / native LOCAL Git

**Date:** 2026-10-17. **Admission:** merged into main via #758 (6cec8e86); lab-only, SECURITY RED. **Owner semantics:** Option A approved on 2026-10-16, implemented here only as a disposable local fixture.

## Purpose / provenance

CP077 used real separate Linux UIDs, mTLS and native local Git but exposed a deliberate late-revoke effect-time race. CP081 added real Raft Txn atomic admission/revocation; CP082 joined CP081 with local bare Git CAS and full-sync SQLite UNKNOWN journaling, but under one Linux UID. CP083 exercises these features **in the same executable local path** with a distinct sink UID and worker UID, without pretending that local Git and etcd form a distributed transaction.

- Base: exact PR #737 41faa31f715e75c062c4e033b1517fbc48df331b, inherited as a separate isolated worktree/branch. No source edits on parent Draft.
- Code: scripts/vf_office_v2_604_cp083_osuid_tls_localgit_lab.py, SHA-256 ff7a648d99b2a4bdda057c0758017b90727c7ee637f660351b9bccaf2f42afe6.
- Evidence: adjacent .json, SHA-256 cc6a576a57b76c6578c54af36c6d3306976cf92ea5814c3f28de7787285f69b0, including TWO ORIGINAL UTF-8+LF raw JSON provider receipts and their SHA-256, independently generated ephemeral provider namespace identifiers.
- Offline immutable gate: scripts/vf_office_v2_604_cp083_osuid_evidence_gate.py, which rejects 8/8 deliberate corruptions and does not start etcd or run native Git.
- Physical execution: MacMiniOffice2.local existing Colima velvet-qa Linux aarch64 guest; pinned official etcd 3.6.15 and etcdctl. A **test-only** root fixture controller drops child process identities to UID 62001 (sink), UID 62002 (worker), and UID 62004 (negative principal); no persistent Linux users, no OS privilege escalation on the host.
- Sink holds its temporary private mTLS key, bare Git and full-sync SQLite journal in a UID-restricted 0700 directory. Worker sees only a Unix socket, whose real SO_PEERCRED UID and exact task case are checked. Only a local synthetic Git ref is changed.

## Results from two fresh provider runs

- **Run 1: 59/59 PASS**; raw receipt SHA-256 45303441866630124d0c66f871b67bba8bcabef2c0416ad137341a5366ee1d98.
- **Run 2: 59/59 PASS**; raw receipt SHA-256 87c5a83b767c29e1d85701469f527b68d5f10201c6bb630864731d51a4c52358.
- **Total 118/118 named assertions** across independent disposable provider instances. Real etcd TLS/RBAC/atomic admission, UID denial of sink key/Git/journal, outsider impersonation denial, native local Git success, reservation-retaining drain, revoke-first denial, mid-effect revoke -> durable UNKNOWN_EFFECT_RECONCILE, lost ACK before and after the local effect, abrupt sink exit after the real Git write, restart freeze persistence, and no blind replay.
- Gate --check PASS and --selftest PASS with **8/8 corruption mutants rejected**.
- First iterations genuinely failed on UID-owned directory traversal, an overly narrow duplicate-after-drain assertion, replay-after-lost-ACK handling, and abrupt-exit stale Unix-socket cleanup. These issues were corrected and rerun; initial failures are **not** counted as PASS.

## Explicit RED limits

1. Root is a disposable LAB issuer controller, **not the protected real Core grant/epoch issuer**.
2. **Remote GitHub write with limited credential custody, idempotency and authoritative remote readback has NOT been tested**; no GitHub remote writes were performed by the native lab.
3. A source-to-worker cryptographic signed claim is NOT joined here; the worker principal is scoped by kernel SO_PEERCRED UID and synthetic exact case. Production review must cover signature and trust boundary.
4. Git LOCAL CAS and etcd Raft transactions remain **different stores**; Option A allows a previously dispatched effect to complete after revoke and requires UNKNOWN freezing.
5. Independent second physical Mac review is not proof of two independent autonomous coding agents; exact-head CI and physical QA must be recorded separately.
6. No production deployment, merge, cloud/IAM changes, paid API, Codex engine, ChatGPT Work, model-executed source worker, real customer, printer or business effect.

## Reproduction

Offline: python3 -B scripts/vf_office_v2_604_cp083_osuid_evidence_gate.py --check and --selftest. Native tests require a disposable Linux ARM64 Colima guest, root test controller, exact-pinned official etcd and etcdctl, and VF604_CP083_DISPOSABLE_GUEST_ONLY=VF604_CP083_EXPLICIT_NO_REMOTE. The guard rejects ambient remote credentials and other hosts.

**Conclusion:** The narrowly scoped *local joined separate-UID provider/effect demonstration* passed, but Office P0 security admission remains RED. merged into main via #758 (6cec8e86); lab-only, SECURITY RED.
