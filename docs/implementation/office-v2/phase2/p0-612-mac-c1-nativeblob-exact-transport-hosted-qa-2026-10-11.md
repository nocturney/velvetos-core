# Office 2.0 #612 — Mac Qwen4B C1 byte-exact GitHub transport and independent hosted QA

**2026-10-11 · source-only model history, new native connector Git archive and new PR-scoped hosted QA.** This is NOT blanket #612 P0 admission. It does not change #604 credential ownership, protect against Docker daemon/kernel compromise, install a scheduler, start Windows Sandbox, or execute generated Python on either physical workstation.

## Why this matters

Earlier Mac B1 generated a syntactically admitted public function but could not enter hosted QA: the Mac original was **536 bytes** and ended with `)`, while its previous UTF-8 GitHub text archive had **537 bytes**, ending with an added LF. SHA256 raw-source admission correctly failed. That archived B1 branch and source remain unchanged. The subsequent **separate Mac C1** one-shot Qwen3.5:4B generation was recorded locally and never executed; the original model explicitly ignored a prompt asking for a terminal LF.

This new path transfers the **already-generated C1 original source**, not B1, using only approved first-party connected GitHub actions: `create_blob(content=base64,encoding=base64)`, inspect the returned Git blob SHA via GitHub, `create_tree` based on the current main tree, `create_commit`, `update_ref` with exact expected SHA and `force=false`. No Windows or Mac Git push credentials, alternate remote Git writes or model retries were used.

## Original source and independently verified exact-byte archive

| Invariant | Observed |
| --- | --- |
| Source host / user | MacMiniOffice.local / chris UID501 |
| One-shot existing local model | `qwen3.5:4b`, digest `7f3251fa6878a78a606bcb3c074283306e5ad2ea411a7774a9dd98a4bc7f2d13` |
| Task | `p0-mac-qwen4b-tag-byteexact-20261011-c1` |
| Original Mac generation time | 11.029 seconds, prompt-eval 452, completion 122 tokens |
| Original source SHA256 | `084d446873fb871ad444f7704b7868b72e599829b9da6e0a2fca0f972d4dae6a` |
| Original source byte length | **480**, last byte decimal **41** `)`, **no trailing LF** |
| Host native `git hash-object` | `7ec37475b86cabe728b95be37e38e984a74e6264` |
| GitHub native Base64 `create_blob` + GET | SAME Git blob SHA `7ec37475b86cabe728b95be37e38e984a74e6264`, exact **480** bytes, last byte **41**, no LF |
| Quarantined branch archive | `docs/implementation/office-v2/phase2/quarantined-new-model-sources-2026-10-11/mac-qwen4b-tag-byteexact-c1.py.txt` |
| Original Mac request receipt | `b1f19feaa6b3fcb9eaeb3e8d1a8ae84027b9b8d3f56980fcfb0a7aed5e0a2dfe` (original local file SHA256) |
| Original local C1 model response | `1c9df1b94f071c015e944fb9c1f5189f37538c896c5682c96577da1907c658af` |
| New model calls for this archive | **0** |
| Generated Python executed on physical Mac/Windows hosts | **FALSE** |

Provenance: `p0-612-mac-qwen4b-c1-nativeblob-hostedqa-2026-10-11.json`. The original source is placed in the existing `*.py.txt -text !eol` quarantine rule. GitHub's native blob SHA is a Git SHA1 over `b'blob 480\\0' + original bytes`, and was independently recomputed by host `git hash-object`; the SHA256 separately pins raw bytes. The exact source bytes have now been fetched from the new Git branch and independently read back on BOTH physical hosts. This is NOT source-authenticity evidence about model weights or an attestation of the model itself; it is byte identity of the recorded source.

## Host-only selftest: source *read*, never execute

`scripts/vf_office_v2_p0_hosted_mac4b_c1_nativeblob_qa.py selftest` reads the bytes but **never imports or executes** generated Python, does not create Docker guests, and makes no Git writes. Its 29 static checks pin original source size, SHA256, Git SHA1, no-LF, AST-only review, public benchmark fixture, one-shot manifest, altered bytes and forged manifest denials, and eight forbidden Docker flags. It reuses existing trusted `vf_office_v2_p0_hosted_new_source_review_lab.py` and `vf_office_v2_p0_hosted_container_boundary_lab.py`.

Original source is `canonical_tag`, a public `canonical-tag-v1` fixture with 3 visible and 12 withheld test cases. **The model was never given the hidden cases.** The source appears valid but behavioral QA must be independently measured, never inferred from AST or a human visual read.

Physical QA before PR (independent fresh, clean clones of the same branch):
- Chris Windows: original C1 `480` bytes, SHA256 match, **29/29 STATIC PASS**, no local source execution.
- MacMiniOffice.local: original C1 `480` bytes, SHA256 and `git hash-object` match, **29/29 STATIC PASS**, no local source execution.

## *Only* hosted PR execution admission

`.github/workflows/office-p0-hosted-mac4b-c1-nativeblob-qa.yml` requests `permissions: {}`, runs on GitHub-hosted `ubuntu-24.04`, job timeout 8 minutes, and checkout `persist-credentials: false`. The first step is static only. The `run` path denies all non-hosted/non-PR contexts and verifies no persisted checkout credentials before container operations.

Generated source is copied **byte-identically** into a fresh temporary test tree and can execute **only** inside an inspected, digest-pinned immutable Python 3.11 Docker image; `--network=none --read-only --cap-drop=ALL --user=65534:65534 --security-opt=no-new-privileges:true --pids-limit=32 --memory=256m --cpus=1 --ipc=none`; exactly one public read-only fixture mount, isolated tmpfs, no docker.sock, no Git token or real secrets, bounded subprocess timeouts and forced guest cleanup. The fixture, hidden test SHA and independent `qa_inner` isolation negatives are reused from the existing protected main implementation, not regenerated by the model.

The hosted job **must** show source SHA256, 3/3 visible and 12/12 hidden tests and denial of network, host synthetic canary, privilege escalation, write access, and exportable credentials before reporting PASS. A failing Docker guest/QA is an actual **FAIL**, not a reason to normalize the original code or auto-retry the original model. GitHub Actions may use included CI minutes; no paid model API inference was invoked.

## Required outcomes and remaining blockers

- **Before protected CI:** byte identity **PROVEN**, static AST/29 offline controls **PASS** on both hosts, behavioral model QA **PENDING**, autonomous agent **NOT PROVEN**. The source/manifest intentionally retain the original pre-QA state.
- **After CI, if successful:** this *single exact source* passed one independent hosted isolated QA pass. This is not a general code safety proof, a stable multi-sample success-rate estimate, a continuous worker, or an autonomous GitHub PR created by a model.
- **Security not unlocked:** physical workstation execution of model-generated Python remains DENIED pending true isolation; original #604 Windows Sandbox user-Session1 attended witness is not proven; signer and Docker daemon separation / stale-owner native Git ref denial / unknown-ACK reconciliation remain RED.
- **Future work:** use this exact **connector-native Base64 blob + optimistic fast-forward ref** admission for independently authorized, provenance-pinned *new* quarantined sources, not the previous explicitly blocked B1 rewrite. Only promote after independent QA, protected exact-head PR CI and exact-main postmerge full suite. No Codex CLI, paid inference, live customer/printer/social effect, production writer or new scheduler.
