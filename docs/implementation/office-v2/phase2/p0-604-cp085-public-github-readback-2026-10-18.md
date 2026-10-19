# Office #604 — CP085 public GitHub readback, non-authoritative (2026-10-18)

**Admission: merged into main via #758 (6cec8e86); lab-only, SECURITY RED.** Refs #604, #612. #749 and #753 were closed without their own merge commits. This work does not supply an authenticated remote writer, credential custodian, protected Core issuer, signed workload claim or a production release mechanism.

## Narrow goal

Close the *preparatory read-path gap* without requiring a new key, paid service or remote write: obtain a real GitHub branch HEAD through a single credential-free `git ls-remote` call and derive a deterministic, auditable but **non-authoritative** observation. For any public remote SHA — expected, candidate, conflicting or unavailable — preserve `UNKNOWN_EFFECT_RECONCILE`, `frozen=true`, `retry_allowed=false`, `release_allowed=false` and `effect_proven=false`. Never attribute remote authorship or conclude that the lost-ACK writer succeeded merely because a head matches.

## Hard-scoped implementation

- `scripts/vf_office_v2_604_cp085_public_git_readback.py`: fixed public URL `https://github.com/nocturney/velvetos-core.git`; only `refs/heads/lab/...` (no `main`, no arbitrary repo/url), lower-case 40-char SHA, distinct prior/candidate. Single `git ls-remote --exit-code` call, bounded 12 seconds, no shell, no retries, no inherited environment (unknown canaries, GitHub tokens, Python path, SSH agent, Git config). Public read only.
- Strict one-line tab-separated parser rejects wrong ref, malformed, empty, duplicates, mixed/overlarge replies. Any failure refuses without converting absence of evidence into `REMOTE_UNCHANGED`.
- Canonical local JSON observation receipt with exact keys and `frozen` flags, private directory + exclusive create + file/directory fsync. No overwrite, unknown/false-GREEN mutations rejected. **SHA256 is an integrity checksum, not an authentic writer signature; a mutable local owner can replace it.**
- `scripts/test_vf_office_v2_604_cp085_public_git_readback.py`: **32 tests** (no network needed in CI): four possible result classes, no-blind-retry, forbidden authority flag, invalid refs/SHAs, strict parser, single/credential-scrubbed subprocess, timeout/command error, noncanonical/mutated/duplicated receipts, symlink and world-readable directory rejection. Receipt-directory POSIX mode tests (`test_18`, `test_19`, `test_22`, `test_23`, `test_24`, `test_27`, `test_28`, `test_29`, `test_30`, `test_31`, `test_32`) print `SKIP_NON_POSIX` on non-POSIX. Linux and macOS still run them. Modes `0755`, `0750`, `0740`, `0710`, `0720`, `0705`, `0704`, `0701`, and `0702` raise `RECEIPT_DIR_MUST_BE_PRIVATE`. Mode `0700` is accepted. A copied mutation that weakens `st_mode & 0o077` to `st_mode & 0o007` accepts `0750`, `0740`, `0710`, and `0720` and is caught. A copied mask of `0o070` accepts `0705`, `0704`, `0701`, and `0702` and is caught. Removing the check accepts a group-readable directory and an other-readable directory and is caught. `test_30` refuses a symlink used as the receipt parent (`RECEIPT_PARENT_UNAVAILABLE`). Dropping `path.parent.is_symlink()` writes through that link and is caught. `write_private_receipt` still uses `st_mode & 0o077`. Observer cwd checks compare `pathlib` parts. Canonical `check-office-v2-contracts.py` runs all 32 on Linux.

## First live readback: public reference only

- Author host: `Mac-Bedroom.local`, Python 3.12. Single remote read against the then-public lab branch `refs/heads/lab/office604-cp084-nonroot-sink-recovery-20261018` (the #753 head at the time), not a write. #753 later closed; this readback is merged into main via #758 (6cec8e86); lab-only, SECURITY RED.
- Ref: `refs/heads/lab/office604-cp084-nonroot-sink-recovery-20261018`
- Expected old SHA: `85de7e7e42c8e427204a0f32143193d3377597fb`
- Candidate SHA: `313767104158023c365bce9b012588490a56e7ce`
- Real observed head: `313767104158023c365bce9b012588490a56e7ce`.
- Classification: `REMOTE_ADVANCED_REVIEW_REQUIRED`, **not** `COMMITTED_READBACK`. `UNKNOWN_EFFECT_RECONCILE`, frozen true, retry/release false, proven false, remote writes zero.
- Raw local canonical receipt: `p0-604-cp085-public-github-readback-2026-10-18.json`, SHA256 `4f468ddcd4651262d8a0b7f535ac99c70185c128f4cf64061bba9df96528ebcf`. Receipt is 654 bytes, created mode 0600 in private `/tmp` directory then copied to the repository as **non-secret observational evidence**.
- Separately, before implementation, Mac-Bedroom and MacMiniOffice2 each ran sanitized **read-only** `git ls-remote` against the same branch; GitHub PR metadata returned the same head. These three reads target the same GitHub origin and do **not** constitute an independent effect authority or three separate commits.

## Missing admission gates

1. Genuine scoped **remote GitHub writer** with exclusive credential custody, protected branch CAS, authoritative remote readback with issuer signatures and lost ACK; **NOT tested**.
2. Real authenticated protected Core issuer, signed task/workload identity, separate OS-UID Sink, mTLS/RBAC, and Option A revoke/effect causality; **NOT provided** here.
3. Third-party independent security signoff and two fully isolated autonomous Workers; **NOT proved**.
4. Cross-store exactly-once guarantees cannot be inferred from a SHA comparison. Unknown always remains frozen for manual or separately authorized reviewed clearance.

**No new worker, token, paid API, scheduler, production action, merge, deploy or remote effect.**
