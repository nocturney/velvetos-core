# Office 2.0 / Issue #612 — Actual model-authored code in a protected PR quarantine

**Date:** 2026-10-10 | **Status:** evidence-only, **NOT production-ready** | **Owner:** Office P0 Task Envelope / independent QA lane; #604 remains the sole fleet scheduling/lease owner.

## New proof beyond the already merged #652 / #655 evidence

Previous work verified Qwen3.5:4B + Aider **actually generated code** for distinct Mac tasks and passed **3 visible + 12 hidden** tests per task. It did not preserve those actual generated source bytes as **reviewable Git PR changes**. This is a **manual, read-only curatorial delivery** of the original code, not a model-controlled Git writer:

- The exact original `canonical_tag.py` from **new successful** Task `p0-diverse-run-mac-tag-state-v2-20261010-c` was byte-copied from MacMiniOffice.local, SHA256 `b2ec92fed514a5e0e37aeca31155fe0d04cdfde70a3d46fafeeb9a09b0ef1ccb`. Original Mac Worker receipt raw SHA256 `c2f81cec7419219f942ec74524864a2159ca233759ba643e193cead7ed5087d5`, embedded receipt selfhash `2bdb477dc94308e8a8c8d1dff63e5a68843a4d783946d0aaaf93b13c24629e9d`; Git seed base `b078080a31fca74f622ed93bd2c58a7421a51536`.
- The exact original `windows_merge.py` from independent successful Task `p0-diverse-run-mac-merge-guided-20261010-a`, SHA256 `999f8ae84cbca062a41297b6fadf6703ee69fa8a61e427a8441cd1a169c3b0a0`; raw Worker receipt `f6dac1286bb1fad2ddb525ecf51d3fd86a9149d2a5cc8464f05c5569350cedda`, selfhash `431c9d94ac939c794da794e84175964508e77125397e1fcc36a5a7fdc8862524`; different seed base `d081112707ad55ff9e848a380227223bc75dff63`.

**Original source bytes were rehashed on Chris Windows and matched the immutable Worker evidence on Mac.** They were neither regenerated nor edited. Both are **quarantined under `docs/implementation/office-v2/phase2/quarantined-agent-sources-2026-10-10/`**, not imported, installed, scheduled or included in an executable production package. Historical original Task Envelopes, original failure/UNKNOWN journals and their raw logs stay untouched on the originating devices.

## A real additional QA gap caught BEFORE promotion

The new offline `scripts/vf_office_v2_p0_model_artifact_pr_gate.py` independently checks static AST and exact source SHA256; executes the original code **only in a disposable test subprocess with restricted Python builtins**, with `-I -B`, timeouts and independent deterministic public-oracle tests. **This is not a secure OS sandbox or proof of isolation against arbitrary malicious model code**; the only executed bytes were vetted and SHA-pinned above. No Ollama inference, Aider, Git push, process kill or external effect is executed by this checker.

| Actual original source | Original independent QA | Added public-oracle QA | Interpretation |
|---|---|---|---|
| `canonical_tag.py` | 3/3 visible + 12/12 hidden PASS | **528/528** deterministic ASCII/Unicode/case/punctuation cases PASS | Good result **for this expanded bounded suite**, not universally correct |
| `windows_merge.py` | 3/3 visible + 12/12 hidden PASS | **256/256** normal integer-interval cases, **9/9** malformed input cases PASS, BUT **one stricter specification counterexample FAILED** | **DO NOT PROMOTE** as conformant to strict endpoint typing |

**Concrete bug in the model-authored source:** the public original specification says an endpoint must have `type(endpoint) is int` (not merely `isinstance(endpoint,int)`). The model produced `isinstance` checks, which admit subclasses. With `class IntSubclass(int): pass`, calling `merge_windows([(IntSubclass(1), 2)])` returns `[(1, 2)]` instead of raising `ValueError`. The original 12 hidden tests only covered bool/float/malformed pairs, not this subclass distinction. This is a verified independent-QA gap, **not** retroactive falsification of the original 15/15 QA results. Source is preserved unchanged, so the new source-level defect remains reproducible and visible in review. Future fixes require a **different new authorized Task Envelope/code revision**, not editing historical model output or retrying UNKNOWN attempts.

## What the protected GitHub PR actually proves and does not

- A human/operator-supervised assembly of **real model-authored, byte-matched source artifacts** into **quarantine-only Git changes** and a **normal protected review/CI/merge flow**. This is a meaningful model-output-to-PR *manual delivery* gate, not autonomous code-agent PR authorship/merge or production write.
- The Office contracts pin the checker byte SHA256 `352c192ebfa9ea6b32739c1185fa06741c68430ed5b183db1c045df94e52c096`. Its historical sanitized JSON pins both Task IDs, model digest `7f3251fa6878a78a606bcb3c074283306e5ad2ea411a7774a9dd98a4bc7f2d13`, original raw Worker receipts, source hashes, independent 528 / 256 / 9 results and exact counterexample. Strict offline `verify` plus **21/21 adversarial selftests** deny altered code, fake QA success, tampered source/receipt pins, hidden bug masking, false automatic model push, or unsupported authority.
- The manifest explicitly sets `production_code_promoted=false`, `model_pr_created_autonomously=false`, `stale_fenced_git_effect_proven=false`, `fleet_lease_proven=false`, `distributed_recovery_proven=false` and `runtime_sandbox_proven=false`.
- There are **zero additional model calls, no Codex CLI, no paid API, no business/Instagram/WhatsApp/customer/printer/GUI writes**. The GPU-bound Windows CAD tools were not interrupted.

**Next #612 gate:** genuinely agent-authored protected PR orchestration with an approved canonical #604 provider lease + monotonic effect receiver fencing, independently checked code/QA, failed/UNKNOWN reconciliation and no duplicate writer. **No such authority has been granted by this PR.** Future addition of a corrected model output must be isolated in a separate new attempt; original evidence remains immutable.
