# Office v2 #612 — Two different coding task families prepared on two physical hosts

**Date:** 2026-10-09 | **Status:** scoped **PREPARATION ONLY** PASS; **NO model calls, real code edits or coding-worker PR yet**.

This is the first step toward #612's still-open acceptance gate of two genuinely **different** tasks executed by independent local model workers on the two actual hosts. The existing v1 Aider Worker is pinned to `slug.py`; its previously executed source and immutable receipts must not be changed. We therefore built a tiny **preparer/test catalog**, not another Agent, scheduler, live Task Envelope issuer or new autonomous worker.

## Two distinct source problems and independent original host readbacks

| Evidence | Windows Chris | MacMiniOffice.local |
|---|---|---|
| Fixture ID | `canonical-tag-v1` | `merge-windows-v1` |
| Source task | `canonical_tag.py` lower ASCII identifier normalization | `windows_merge.py` merge inclusive ranges with strict invalid input |
| Original local Git base | `9463e189c29f48e7a9a8c956a38e6f9cadcf8f8d` | `336318a6440bbbc5efd6d56fec66007405722923` |
| Distinct task | `p0-diverse-win-canonical-tag-20261009-b` | `p0-diverse-mac-merge-windows-20261009` |
| Actual preparation | PASS | PASS |
| Independent same-host byte/Git/checkpoint readback | **PASS** | **PASS** |
| Visible and hidden QA of intentionally broken source | **FAIL as expected** | **FAIL as expected** |
| Visible + 12 hidden QA of deterministic control solution | **3/3 + 12/12 PASS** | **3/3 + 12/12 PASS** |
| Pure offline adversarial tests | 11/11 PASS | 11/11 PASS |
| Model, paid API calls, production authority | 0 / 0 / NONE | 0 / 0 / NONE |
| Original candidate manifest SHA256 | `92aa42ba0e6795e0b2a2a243d43bf7ed185684611abb40a1cae536fac6e565f6` | `ab9d7c1da5b167b275a732201c2f501ad864db0891421381c9d8e2874e1c58d8` |
| Candidate self-hash | `ae04bb38ed2c3df118b658b04d413a20112899b83cf2b003d3c99191782e1582` | `5e215da8c7fe14eee06fd81bcf07e81b989c6e1ec12edf8efc3a64dd5672782a` |

Both candidate manifests are **`PREPARED_ONLY_NOT_EXECUTABLE_BY_V1_WORKER`**, not canonical v1 Task Envelopes, and they explicitly grant no model/production/fleet authority. The original raw input files, hidden tests, checkpoints and local Git repositories remain solely inside their new, separate `AgentEnvelopeLab/p0-diverse-fixtures-{win,mac}-20261009` directories. Sanitized source/test/prompt/checkpoint hashes, local independent verify claim, Git branch+base, and exact original manifest SHA256 are in the sibling `p0-two-host-diverse-prepared-fixtures-2026-10-09.json`.

## Source and negative findings

- Executed same fixed code source: `scripts/vf_office_v2_p0_diverse_task_fixtures.py` at Git commit `5823591da1072e87c1290de9d3bfdb461b7ea565`, raw LF file SHA256 `2bc85ad0b028c959ba2b958c6184ef682bc68325aca1c6a78a93e49385378af3`; base `main` `4f1cc80537430b5d18bf5747f543118a7ee54887`.
- On initial Windows task `p0-diverse-win-canonical-tag-20261009`, the independent verifier **rejected** (1) native Git path separators `D:/...` vs `D:\...` and (2) implicit Windows CRLF transformation of Python/text source writes. It was a **preparation-only** failed attempt with no model run; original evidence remains untouched. We changed the preparer to use **byte-exact UTF-8 writes** and `Path.resolve` comparisons; prepared new task with suffix `-b`, no reuse or automatic recovery.
- The two fixtures differ in source, test, prompt, hidden QA, Git base, task ID, physical host and branch. Their independent `verify` command read back exact source bytes, clean Git state, branch+commit, prompt/hidden hashes, checkpoint shape/identity and self-hashed candidate. It **did not** execute a model.
- Every cloud/host test of this script uses `selftest` and historical sanitized metadata checks only. `prepare` is explicit and lab-scoped; it never starts model/worker and cannot authorize one.

## Remaining P0 gates

**Still not demonstrated:** independent actual Qwen/Aider Worker execution on these two different targets, two protected coding PRs, sequential merge/postmerge, reliable 1-versus-2 worker throughput, model/host resource peaks or cross-host lease and monotonic fencing. A future bounded generalized Agent/Worker admission must consume each prepared candidate without modifying original v1 Worker and integrate canonical Task Envelope, independent QA, checkpoint, receipt, failure/UNKNOWN controls. #604 exclusively owns fleet/placement/lease. Do not turn candidate `status=PREPARED_ONLY` into execution permission. No Codex CLI, new paid inference, new scheduler/watch, GUI/CAD interruption, credential, customer, social, printer or production write occurred.
