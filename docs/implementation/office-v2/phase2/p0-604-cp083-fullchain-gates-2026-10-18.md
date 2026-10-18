# CP083 hardened candidate full-chain evidence map — 2026-10-18

**STATUS: SECURITY RED, full chain NOT admitted.** References: [issue #604](https://github.com/nocturney/velvetos-core/issues/604), [owner acceptance gates](https://github.com/nocturney/velvetos-core/issues/604#issuecomment-6248051067), [Draft #749](https://github.com/nocturney/velvetos-core/pull/749), [Cursor Draft #755](https://github.com/nocturney/velvetos-core/pull/755), [CP084 Draft #753](https://github.com/nocturney/velvetos-core/pull/753).

This document specifies **which actual observations would close each gate**. It is not independent QA or a request to bypass a blocked safety control. Any future provider/UID execution must be separately authorized in a genuinely disposable guest; the local harness must not touch production, credentials, customer systems, printers or remote GitHub refs.

## Exact source basis / non-overlap

- #749 HEAD **85de7e7e42c8e427204a0f32143193d3377597fb**. Its [hosted Core Sensors run 39113651581](https://github.com/nocturney/velvetos-core/actions/runs/39113651581) passed, but static/Linux socket CI does NOT validate the full joined chain.
- Cursor owns fix requests **1–3** on #755. Current #755 HEAD **e065552825d64e9151dca0a53d4b3c7a896ab479**; candidate source SHA256 **39b0c918f906980f1ba87c49a03cc6cbf10b4d144b157b3221605a14ad3626b6**. [Exact-head Core Sensors CI run 39115774912](https://github.com/nocturney/velvetos-core/actions/runs/39115774912) reports check-all success. This PR does not change any of Cursor's client socket platform/peer guards, ACK deadlines, response allowlist, tests, or child SAFE_ENV policy.
- #753 (CP084) covers **same-UID**, synthetic-provider local Git and SQLite recovery tests. It does NOT provide the distinct-kernel-UID + native etcd mTLS joined run.
- The old sealed #738 CP083 59+59 receipts belong to the **previous** source; they must not be recycled as evidence for #755.
- The dedicated vf-cp083-quarantine guest reported **Operation not permitted** for unprivileged user namespace, and guest provisioning was blocked by safety controls; it was stopped. Do not evade controls or run a Cursor worker using host credentials.

## Seven executor acceptance gates

| Gate | Exact evidence to close | Status |
| --- | --- | --- |
| **1. Disposable Linux ARM64 guest, no host secrets** | Fresh guest kernel/arch and namespace readback, exact untouched /proc/self/mountinfo captured and hashed; independent host-path comparison showing no host HOME/SSH/cloud credential mounts, no inherited ambient secrets, authorized guest-only fixture controller, cleanup and guest shutdown. A self-reported boolean cannot prove absence of mounts. | **OPEN / BLOCKED** by guest provisioning safety control. |
| **2. Different kernel UIDs and bounded socket** | Real process getresuid() and connected Unix SO_PEERCRED confirming sink 62001, worker 62002, attacker 62004 and guest-only controller 0; failure before any request bytes for wrong UID, symlink target and unauthorized task; positive verified-sink control; 2s whole inbound frame and 3s whole ACK deadlines; actual DAC denies worker direct TLS key, Git and SQLite journal reads. | **OPEN for hardened HEAD**. Linux synthetic socket suites exist on #755, not joined separate principals. |
| **3. Real SHA-pinned etcd 3.6.15 mTLS/RBAC + Option A** | Approved disposable guest records real native etcd SHA256 **117cc09981c0f1eb378e7520be6969756c2d6a762f376944e53f7bc9800c0c59**, etcdctl **de07257495499384f91f028dbc0c8e0394e0bd572b728ac486bbadbfa1cdf275**, exact CA/CN+RBAC roles, forbidden cross-namespace direct put, native lease/revision/Txn. Revoke-first DENY and admit-first DRAINING must be read back with reservation held and no stale-owner effect. | **OPEN for joined new-candidate run**. Historical provider success does not transfer. |
| **4. Native LOCAL Git CAS + SQLite UNKNOWN, joined** | Real bare Git update-ref expected-old-SHA and independent ref before/after; durable SQLite journal, ACK loss before/after actual write, revoke-after-effect, abrupt sink crash and restart. Observe UNKNOWN_EFFECT_RECONCILE frozen, refused duplicates/no blind retry and no unintended second write under the same real OS-UID/provider run as steps 2–3. | **OPEN joined**. CP084 #753 proves narrower same-UID/synthetic-provider paths. |
| **5. Two fresh tamper-evident receipts** | TWO new runs on exact #755 candidate bytes, new distinct provider prefixes, each original one-line UTF-8 LF 59-check receipt plus separately preserved fresh guest preflight with raw mount/kernel/UID/certificate-provider readbacks. Pin four artifact SHA256s to an immutable reviewed commit; retain command/time/exit/revision readbacks privately without keys. | **OPEN**. Offline verifier introduced in this PR can accept and byte-check future receipts; it cannot produce live ones. |
| **6. Independent full-chain security QA / mutations** | A different reviewer claims and inspects the **actual exact SHA and full dependency diff**, independently witnesses/replays both new native receipts; tests stale/revoked owner, forged UID, wrong ref, delayed/lost ACK, provider/sink failure, duplicate and tampered artifacts with authoritative readback. Publish QA verdict with commands, SHA and evidence. | **OPEN**. Author synthetic tests are not QA; #749/#755 client-specific reviews are not full-chain review. |
| **7. Draft PR + hosted CI** | Separate scoped Draft PR, normal history, full current commit SHA and stacked base; hosted Core Sensors check-all successful **on that exact SHA**, Linux socket tests executed without skips, independent QA claimed. | **PARTIAL**. CI is known green on #749/#755 exact heads. A future full-chain delivery requires its own head/CI; CI success alone does not make admission GREEN. |

## Separate remote/production gates — do not conflate

| Gate | Proof that must be supplied later |
| --- | --- |
| **P1 protected Core issuer + cryptographic claim** | Core-controlled signing principal and independently authenticated host/worker/task/GPU/ref/generation/nonce; replay, source, expiry and rotation negative evidence. Root synthetic fixture is never a protected Core issuer. |
| **P2 exclusive restricted-credential remote GitHub sink** | Approved narrow actual credential at sole sink, no worker token, legitimate remote GitHub ref/commit/tree readback, racing writer and lost ACK/HTTP uncertainty, reconciliation and effective revocation Option A serialized with admission. Native local Git CAS is not a cross-store GitHub lease fence. |
| **P3 two real physical-host autonomous coding workers** | Separate scoped, credential-limited execution on two actual hosts; real separate code PRs, independent QA, fault recovery, no reused single-host agent identity. Read-only cross-host QA is not throughput proof. |
| **P4 protected review/admission controls** | Explicit independent security approval and required branch review rules; no self-approval, deploy or READY promotion from green tests. |

## This PR — offline NEW-candidate evidence consistency checker only

New files:

- scripts/vf_office_v2_604_cp083_candidate_evidence_gate.py
- scripts/test_vf_office_v2_604_cp083_candidate_evidence_gate.py (32 synthetic author regression tests, including a CRLF receipt line, a CR byte inside the JSON, hardlink refusal, anchored parent open, guest/manifest CR or duplicate-key refusal, an overflowing exponent, self-issued receipts refused as host attestation, and a POSIX mutation that still refuses a hardlink after the nlink check is dropped)

Run unit negatives with Python 3:

    python3 -B scripts/test_vf_office_v2_604_cp083_candidate_evidence_gate.py

When two approved joined runs actually produce receipts, place them under an evidence directory with a manifest.json of schema **velvetos.office-v2.604.cp083.candidate-fullchain-receipts.v1**. Manifest contains candidate_commit_sha, candidate_source_sha256, security_admission=RED, production_authority=false, real_protected_core_issuer=false, independent_security_review_completed=false, remote_github_writes=0, and exactly two runs. Each run has run_id, receipt_path, receipt_sha256, guest_path and guest_sha256. Guest observation schema is **velvetos.office-v2.604.cp083.guest-preflight-observation.v1**, including kernel method, Linux ARM64, distinct UIDs, pinned etcd hashes, mountinfo checksum, no-host-home and no-ambient-credentials observations. All artifact paths are relative to the manifest, never symlinks/traversals. Preserve the original raw LF receipts. A receipt whose only line ends in CRLF is refused. A CR byte inside the JSON of an otherwise one-line LF receipt is refused.

Run offline consistency check only **after** evidence exists:

    python3 -B scripts/vf_office_v2_604_cp083_candidate_evidence_gate.py --manifest /approved/guest-evidence/manifest.json

Absent evidence, source drift, malformed/duplicate JSON, missing cases, old #738 receipt/prefix, SHA mismatch, wrong UID fields, unpinned etcd, unsafe path and any GREEN/production/QA claim **FAIL CLOSED**. The result intentionally says **OFFLINE_BYTE_CONSISTENCY_ONLY_NOT_RUNTIME_QA** and security_admission **RED**. The 32 synthetic unit cases use invented fixtures ONLY to exercise the verifier, **never** as proof of a guest/full-chain execution. A hardlinked receipt is refused. Artifact bytes are read through directory fds (`O_NOFOLLOW`). A missing or zero `O_DIRECTORY` fails closed as `SKIP_NON_POSIX` before the open. On POSIX the directory fd still includes `O_DIRECTORY`. Guest and manifest JSON refuse a CR byte. `refuse_host_attestation` rejects the byte-consistency result as host attestation. Evidence bytes, including a native SQLite journal and the lost-ACK evidence JSON, must be one regular file with `st_nlink == 1` (`HARDLINK_ALIAS_REFUSED`, `NONREGULAR_FILE`). The lost-ACK gate `main()` is what performs that read. Wire request and ACK frames use that same decoder (`decode_wire_frame`): one LF-terminated object, no CR, no duplicate key, no NaN, Infinity, or overflowing exponent, and no second frame. The live candidate pin moved with that decoder. The lost-ACK envelope still records parent sha `39b0c918f906980f1ba87c49a03cc6cbf10b4d144b157b3221605a14ad3626b6`. GAP_6 stays an expected failure in `scripts/test_vf_office_v2_604_cp083_chatgpt069_negatives.py`. The pinned identity helper and the sealed native Git/SQLite source are unchanged. The provider-revoke versus `update-ref` ordering is unchanged.

**Critical limitation:** An artifact hash stored beside its own artifact is byte consistency, not an authenticated signature; both can be rewritten. A self-declared guest observation is not runtime provenance. Independent reviewer must verify kernel, guest mounts, exact host/source/build, original stdout and complete command/provider evidence **outside the author's manifest** before closing steps 1–6.

Delivery discipline: CLAIM precedes the branch/PR, independent reviewer requested with **QA please @ full SHA**; the author neither QA-reviews nor merges their own PR. Any later authorized merge must be a merge commit, **never squash, force-push, or --admin**.
