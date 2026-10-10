# Office P0 #612 — distinct model-source review + independent metamorphic QA (2026-10-10)

**Status: OFFLINE CANDIDATE REVIEW ONLY.** This is a new read-only evaluation of the already-quarantined original Qwen3.5:4B model output from the successful new Task ID `p0-diverse-run-mac-merge-exact-int-20261010-d`, not a fresh model run, autonomous PR or production promotion.

## Source and evidence pins

- Original model output: `docs/implementation/office-v2/phase2/quarantined-agent-sources-2026-10-10/windows_merge_exact_int_v3.py`, raw SHA-256 `0ec526a84d6a814aecbfc586c237ef59044811f920c0d73640cbf24b76e25479`. **Never rewritten.**
- Original task Git seed base: `d89317730bc9ff5fac95bd064fea710847e1c404`. Original receipt raw SHA-256: `b0cc5ff5e24d33243e65fa7c5f569f7c11bcc275060e76813ed4198e65236fda`.
- Fresh independent check uses `vf_office_v2_p0_exact_int_model_qa_gate.py` as a separately pinned historical prerequisite (original 3 visible + 12 hidden QA, previous 256 ordinary + 11 malformed oracle). It verifies exact source SHA, bounded AST and the original evidence; it never trusts a new manifest to assert its own provenance.
- Public-fixture reconstructed review diff compares `INTERVAL_SOURCE` against the literal model bytes with only `windows_merge.py` in the target allowlist. Its SHA-256 is `8647a9f7eee41ae904883910f64a6d5c6de0e35c92ba2dfde03e72a4608cbd21`. **This is NOT claimed to be the byte-exact diff from the original agent worktree.**

## New independent QA

In a fresh local scratch subprocess, the exact SHA-pinned original source passed **512/512** cases on each of five independent checks across four deterministic seeds: ordinary reference union, permuted input, idempotence, translation invariance, and exact discrete integer coverage. Also passed very large integer endpoints (10^80). The review-bundle `selftest` passed **22/22**, including false-authority, path escape, source pin, receipt, task, base, diff and output tampering refusal.

The checked source is executed with Python restricted builtins in a disposable directory. **This is not an OS security sandbox, malicious-code execution isolation, a full formal proof, or a model-token measurement.**

## Separation of authorship and effect authority

The source was authored by **local Qwen** in a historical Worker run. The review manifest and this PR are **operator-curated engineering artifacts**. The review manifest explicitly forbids any claim of autonomous agent Git/PR authorship, commit/merge permission, source production promotion, canonical #604 lease or physical cross-host fencing. `verify` and `selftest` perform zero Git writes, zero model calls, and zero business effects.

Gate for eventual non-quarantined source use remains a **separate** intentional reviewer decision, protected exact-head PR/CI, and explicit authority contract. No new scheduler, credential change, paid API, replay of FAILED/UNKNOWN, process kill, or customer/CAD/printer/social effect.

Reproduce from repo root: `python -B scripts/vf_office_v2_p0_model_source_review_stress.py verify` and `selftest`. `patch` emits the reconstructed text diff for human review only.
