# CortenDesk v1.13.2 native link compatibility patch — source verification

Date: 2026-10-14
Status: **PATCH_GENERATED_AND_VERIFIED / NOT APPLIED / NOT DEPLOYED**
Origin: [Issue #105](https://github.com/marcpope/cortendesk/issues/105)
Relevant client source: [RustDesk 1.5.0 URI parser](https://github.com/rustdesk/rustdesk/blob/1.5.0/flutter/lib/common.dart#L2404-L2410)

## Why this is needed

The installed RustDesk clients are v1.5.0 on Windows and macOS. Upstream CortenDesk v1.13.2 emits native links using `rustdesk://{{ id }}`, which places a custom device ID in URL **authority**. A browser/URI parser may normalize that component, including letter case. RustDesk 1.5.0 tagged source explicitly recognizes `rustdesk://connection/new/<ID>`, taking the device ID from the **path**. The route is verified in source; **we have not yet clicked a link on a real device**.

## Exact source evidence

Tagged [CortenDesk v1.13.2](https://github.com/marcpope/cortendesk/tree/v1.13.2) contains seven legacy `href="rustdesk://{{ ... }}"` usages:

| Blade file | Occurrences |
|---|---:|
| `device-list.blade.php` | 2 |
| `device-detail.blade.php` | 1 |
| `address-book-manager.blade.php` | 2 |
| `active-sessions.blade.php` | 2 |
| **Total** | **7** |

Each source was downloaded outside the VelvetOS worktree to an owner-private Mac research directory, and its Git blob hash was compared with its pinned GitHub v1.13.2 blob. Exact hashes are in `cortendesk-deeplink-review-2026-10-14.json`.

## Patch contents and reproducibility

The review-only generator `tools/rustdesk-pilot/cortendesk_deeplink_patch.py` validates all four source blobs and seven expressions, refuses a different version/shape, and emits a git diff. The fix changes each native link to `rustdesk://connection/new/{{ rawurlencode($<variable>->rustdesk_id) }}`: the PHP function URL-encodes the ID as one path component without dropping case or appending credentials to a URL.

The generated patch is stored at:

`tools/rustdesk-pilot/patches/cortendesk-1.13.2-rustdesk-1.5-deeplinks.patch`

The generator **never applies a patch**, edits upstream source, launches CortenDesk or invokes a remote-control connection.

Verification on MacMiniOffice2:

- Git blob hashes: **4/4 match** tagged upstream source.
- Generator report: **7 links across 4 templates**, source unchanged.
- `git apply --check` on untouched pinned source: **PASS** (read-only; no patch application).
- All four source Git blob hashes after verification: **unchanged**.
- Mac-generated patch and Windows worktree copy: identical SHA-256 `cf838467cc0598dcb1c82782677a1bba37824b7c6bc684b80e1986155bc98276`.
- Existing RustDesk server and clients: **unchanged**.
- Research branch Python test suite (including source overlay contract tests): rerun before review.

## Integration boundaries

This is a candidate CortenDesk **source patch**, not a fix applied to the already-pulled prebuilt OCI image. To take effect, a separately permitted runner must build a patched CortenDesk source image or upstream must publish a release that incorporates the fix. The earlier remote container-execution denial is still in force; do not bypass it. Do not patch or rebuild production software automatically.

The patch covers the default `rustdesk://` URI handler only. A custom-branded client with a different scheme needs a separate handler and must be explicitly tested. The HTML escaping, client handoff, actual connection negotiation and UX on Windows/macOS still require disposable-client acceptance testing; a passing `git apply --check` does **not** establish that connections work.

Upstream CortenDesk is AGPL-3.0; retain upstream attribution and review license obligations if distributing or deploying modifications. Issue #102 (reported SSO password API bypass) and server/relay security review remain separate gates.

Next gate: verify the patch in an independently authorized staging build, run a disposable RustDesk 1.5.0 client with a mixed-case ID, test desktop client link and native web client, and confirm the original working server is unaffected.
