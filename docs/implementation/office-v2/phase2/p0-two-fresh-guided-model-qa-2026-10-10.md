# Office v2 #612 — Guided public-spec profile, two new real Mac coding outcomes

**Date:** 2026-10-10 | **Scope:** manual, LAB-only, local Qwen/Aider; **one independent QA PASS, one genuine QA FAIL**. Overall Office 2.0 P0 remains **PARTIAL**.

## Why this is distinct from the preserved 2026-10-09 failures

[PR #650](https://github.com/nocturney/velvetos-core/pull/650) demonstrated that the general coding Worker correctly refused false success from two different real Mac/Qwen tasks, retaining their original `RUNNING` journals. This follow-on does **not** retry either Task Envelope. It introduces a narrowly approved `PUBLIC_SPEC_REMINDER_V1` option at **admission of a future fresh task only**, copying the immutable preparation-only candidate into a NEW source repo/branch/Git base/Task Envelope. The profile is derived solely from **already-public fixture requirements**; the separate hidden QA never appears in the model prompt. A new exact byte comparison in `check` confirms that the prompt can only be the original candidate specification or the original + the exact approved public reminder; hidden QA is also compared against its original fixture bytes. Unexpected profile strings, prompt replacement or hidden-QA drift fail closed.

The previous v1 `slug.py` Worker and #604 fleet scheduling/lease ownership were **not changed**. Original #650 failure audits still reference exact historical Worker SHA256 `c08a8413f59a1924c013adc66f523c897f1e477fae810f2c76127699d4262087`, while new code is checked separately against SHA256 `0099792f8be5d20c4c698a417d83bf5d12d00bfeaeccd92a90aeef81865a2cbb`. This prevents rewriting historical provenance.

## What was actually executed on MacMiniOffice.local

Both tasks were prepared from scratch with the existing `vf_office_v2_p0_diverse_task_fixtures.py prepare/verify`, admitted separately with `vf_office_v2_p0_diverse_local_worker.py admit --prompt-profile public-spec-v1`, and run **once each**, sequentially via the original Worker `run`. Both used the Mac local Ollama `qwen3.5:4b` model digest `7f3251fa6878a78a606bcb3c074283306e5ad2ea411a7774a9dd98a4bc7f2d13`, Aider v0.86.2, budget max attempts = 1, additional paid API cost = 0, fresh branches and native Worker/Aider kernel birth evidence.

| Evidence | Fresh `merge-windows-v1` task | Fresh `canonical-tag-v1` task |
|---|---|---|
| Task suffix | `merge-guided-20261010-a` | `tag-guided-20261010-b` |
| New Git seed base | `d081112707ad55ff9e848a380227223bc75dff63` | `14d67645008a068b2f01aae31ff4c02c749308fa` |
| Edited source | **only** `windows_merge.py` | **only** `canonical_tag.py` |
| Worker outcome | **SUCCEEDED** | **FAIL_CLOSED / FAILED_INDEPENDENT_QA_NO_SUCCESS** |
| Separate QA | **3/3 visible; 12/12 hidden PASS** | Visible exit **1**, hidden exit **1** |
| Independent second readback | Original Worker `verify=PASS` | New separate `audit-failed-qa` and `verify-failed-audit=PASS` |
| Original success receipt | Present, checksum verified | **ABSENT** |
| Original RUNNING journal | Removed **only after** verified success | **PRESERVED** |
| Worker elapsed time | **65.527s** | Not asserted as a successful completed Worker receipt |
| Source result SHA256 | `999f8ae84cbca062a41297b6fadf6703ee69fa8a61e427a8441cd1a169c3b0a0` | `7cadf341335664b89b9dfc40effb127f6315d31429b4759a3c0ab5b6325003fc` |
| Exact original audit/receipt | Raw success receipt SHA256 `f6dac1286bb1fad2ddb525ecf51d3fd86a9149d2a5cc8464f05c5569350cedda` | Failed audit SHA256 `dd538dee3e06e4c50e635f25b823ce23a226a631991cd5a8b4cb07aba4ffbd3f` |

The successful `windows_merge.py` result has self-hashed Worker Receipt `431c9d94ac939c794da794e84175964508e77125397e1fcc36a5a7fdc8862524`, exact independent QA replay from a fresh clone and OS PID/birth pin. The failed `canonical_tag.py` attempt has retained original journal raw SHA256 `316dcd74d082da4c8531a29ab8097ccbf5d753692e24a5f6a23d5312b2df7250`; its immutable read-only audit seal is `24945797067d6177d91b8b1de97b9fbdb0a4a65e1aec593f135b216e2b911227`. It was **never retried, requeued or converted into SUCCESS**.

Original two failed Mac journals from #650 were rehashed again and unchanged: `e909db6a1ab48bd5baaafece671c3a6cf825c6f804b7a273b7314e447fddd89d` and `dbf9fa62bfdf6c9da85586810e30dbc0a6fba4c10e6bd5286419375ba5f8e7a3`. All raw logs, original Task Envelopes, receipts, kernel birth pins and audit files stay on Mac under separate `AgentEnvelopeLab/p0-diverse-...` roots. Sanitized names/hashes/QA results are pinned in the sibling JSON, not the raw model logs. Raw selfhash is a consistency check, **not externally signed attestation**.

## Verification and interpretation

The new profile source was executed from commit `9140b5a87acd2f0bec1ea55a5e591e17ef14b906` after fresh Git state was prepared. **32/32** original Worker pure offline safety contract checks passed on Windows and Mac, Office-specific contracts passed on both, and **118/118** full Windows sensors passed without modifying files. `vf_office_v2_p0_guided_qa_evidence.py` adds **25/25** strict offline positive/negative checks denying false two-task success, false QA, receipt/journal tampering, duplicate task/base, falsely inferred Windows execution, paid/API calls, unsupported lease/recovery, or unproven causal effect.

**Honest outcome:** two new attempts on ONE Mac gave **1/2 success**, not 2/2 and certainly not cross-host acceptance. Historical 0/2 used the default prompt; the new 1/2 used extra public reminders. These are tiny, nonrandomized and potentially different model conditions: **no causal claim that reminders caused the improvement**, no statistically reliable success rate, p95, token accounting, two-host protected coding PR throughput, automatic recovery or distributed fencing. The Windows qwen3.5:9b CAD-shared GPU is still in use, so there is **no new Windows model attempt** in this evidence. #604 remains the sole fleet placement/lease owner, with no extra local scheduler.

Cloud CI tests only offline contracts and existing immutable historical JSON. It never invokes `admit`, `run`, `audit-failed-qa`, Mac model or OS process operations; no Codex CLI or paid services are used. Next actionable gate: independently corrected code quality for `canonical_tag.py` in an **entirely new**, explicitly admitted Task Envelope after separately inspecting that failure; and a separately capacity-gated true Windows task + protected PR/QA when Windows GPU is free.
