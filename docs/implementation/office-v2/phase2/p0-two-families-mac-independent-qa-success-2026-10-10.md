# Office 2.0 #612 — Two different real coding families, each independently QA-green on one Mac

**Date:** 2026-10-10 | **Status:** scoped **PASS** for *two genuinely different task families on MacMiniOffice.local*. **Not** cross-host dual-worker success, not end-to-end agent-authored PR throughput, not autonomous recovery, and not Office P0 acceptance.

## Context and original evidence

The generic diverse coding Worker was introduced as a separate LAB-only path in PR #650, exposing two *real* failed Aider/Qwen3.5:4B QA outcomes without promoting either to success. PR #651 added an opt-in, immutable `PUBLIC_SPEC_REMINDER_V1` derived solely from the visible task requirements, and produced a new, independently QA-verified `merge-windows-v1` success, while another new `canonical-tag-v1` attempt failed and retained its journal. The subsequent opt-in `PUBLIC_SPEC_STATE_MACHINE_V2` narrows the public tag requirements to the initial first-punctuation-separator state. It is **not** a hidden-QA answer, does not expose the golden source or credential data, and was applied only on admission to a **brand-new** Tag Task Envelope. The original failed Task Envelopes were never replayed.

## Two real model-backed, independently verified successes

| Field | Mac `merge-windows-v1` | Mac `canonical-tag-v1` |
|---|---|---|
| Unique Task Envelope | `p0-diverse-run-mac-merge-guided-20261010-a` | `p0-diverse-run-mac-tag-state-v2-20261010-c` |
| New Git base SHA | `d081112707ad55ff9e848a380227223bc75dff63` | `b078080a31fca74f622ed93bd2c58a7421a51536` |
| Edited path | ONLY `windows_merge.py` | ONLY `canonical_tag.py` |
| Opt-in public prompt profile | `PUBLIC_SPEC_REMINDER_V1` | `PUBLIC_SPEC_STATE_MACHINE_V2` |
| Executed code checkpoint | `9140b5a87acd2f0bec1ea55a5e591e17ef14b906` | `34a505292caab5c0769adc4bfb7fcf78fad7c115` |
| Local Aider/Ollama | Qwen3.5:4B | Qwen3.5:4B |
| Worker Receipt state | **SUCCEEDED** | **SUCCEEDED** |
| Worker reported time | **65.527s** | **58.344s** |
| Fresh independent QA | **3/3 unit, 12/12 hidden PASS** | **3/3 unit, 12/12 hidden PASS** |
| Separate original Worker `verify` | **PASS** | **PASS** |
| Updated source SHA256 | `999f8ae84cbca062a41297b6fadf6703ee69fa8a61e427a8441cd1a169c3b0a0` | `b2ec92fed514a5e0e37aeca31155fe0d04cdfde70a3d46fafeeb9a09b0ef1ccb` |
| Original raw receipt SHA256 | `f6dac1286bb1fad2ddb525ecf51d3fd86a9149d2a5cc8464f05c5569350cedda` | `c2f81cec7419219f942ec74524864a2159ca233759ba643e193cead7ed5087d5` |
| Receipt selfhash | `431c9d94ac939c794da794e84175964508e77125397e1fcc36a5a7fdc8862524` | `2bdb477dc94308e8a8c8d1dff63e5a68843a4d783946d0aaaf93b13c24629e9d` |

Both Task Envelopes have different Git base SHAs, branches, kernel-born native Worker/Aider PIDs and timestamps, model calls (minimum 1, exact number unknown), source hashes and QA receipts. Both consumed a new isolated checkout after the original prepared candidate was byte-pinned and independently verified. They did not touch the main repository or any production services. The success journal was cleared **only after** successful separate Worker verification; neither attempt was rerun.

**Safety readback:** three older failed original Mac journals remain unmodified by exact raw SHA256:
- #650 `merge-windows-v1`: `e909db6a1ab48bd5baaafece671c3a6cf825c6f804b7a273b7314e447fddd89d`.
- #650 `canonical-tag-v1`: `dbf9fa62bfdf6c9da85586810e30dbc0a6fba4c10e6bd5286419375ba5f8e7a3`.
- #651 `canonical-tag-v1` V1 profile: `316dcd74d082da4c8531a29ab8097ccbf5d753692e24a5f6a23d5312b2df7250`, no success receipt.

The full sanitized metadata and original file SHA256s are in the sibling JSON `p0-two-families-mac-independent-qa-success-2026-10-10.json`; raw model logs, originals and QA remain in their separate, exclusive MacMiniOffice.local `AgentEnvelopeLab` roots and are not copied into Git. Self-hashes protect against accidental drift, not externally signed attestation.

## Negative controls and strict limitations

`scripts/vf_office_v2_p0_second_diverse_success_evidence.py` has **25/25 pure offline positive/negative test scenarios** denying false host count, duplicated ID/Git base/target, profile/raw byte/QA tampering, invented token/model usage, unearned reliability, paid API, wrong model, ignored UNKNOWN journal, scheduler/lease, fencing, or production authority. Cloud Office contracts run **only** `verify` and `selftest` and pin the verifier source bytes; CI never executes the real Aider/OS work again.

These are **two different task families on ONE Mac with two different opt-in prompt profiles**. No randomized comparison, no causal evidence that prompt wording alone caused success, no robust success-rate or p95 statistics, no performance guarantee or actual agent-authored PRs for either synthetic coding task. They are not the two physical host proof still outstanding; the Windows NVIDIA GPU is occupied by CAD/Snapmaker, so no 9B coding Worker was started. #604 exclusively owns eventual canonical placement/lease and monotonic stale-owner fencing; this LAB does not implement another scheduler, distributed lease or autonomous UNKNOWN recovery. **Overall P0 remains PARTIAL.** No Codex CLI, remote/paid model, extra API bill, customer/social/printer action, credentials, destructive system operations or background daemon.
