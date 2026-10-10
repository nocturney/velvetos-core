# Office 2.0 #612 — Actual Mac Aider stdout usage display, NOT exact model token usage

**Date:** 2026-10-10 | **Status:** read-only three-original-Worker LAB evidence; P0 remains PARTIAL.

## Original evidence, with no replay

A **manual read-only** invocation of `scripts/vf_office_v2_p0_aider_display_usage_lab.py observe --mac-lab-root <original AgentEnvelopeLab>` on MacMiniOffice.local inspected three already successful, **separate** Task Envelopes that executed local Qwen3.5:4B through Aider v0.86.2. For every task it checked the exact original raw Worker Receipt SHA256, `SUCCEEDED`, original independent **3/3 visible + 12/12 hidden QA PASS**, actual `stdout.log` SHA256 against its Receipt `stdout_log_sha256`, model digest and reported elapsed time. It extracted exactly ONE final Aider `Tokens:` terminal line from each raw, SHA-verified stdout. The original receipts/logs were not edited, model was not rerun, no Ollama API or client was called, no credentials were fetched.

| Original source task / original output file | Worker elapsed seconds | Aider terminal tokens display (sent / received) | Original stdout SHA256 |
|---|---:|---|---|
| `p0-diverse-run-mac-merge-guided-20261010-a`, `windows_merge.py` | **65.527s** | **1.0k / 1.1k** | `8e6620973b4b636f5880071bce911d856c1cae71a3cae71b03da4de8be7c4aea` |
| `p0-diverse-run-mac-tag-state-v2-20261010-c`, `canonical_tag.py` | **58.344s** | **1.0k / 940** | `752719fe98d38a7cb31094e8f0c8681fd1b6f5da30e0f8209fe0db79a2f4c48b` |
| `p0-diverse-run-mac-merge-exact-int-20261010-d`, `windows_merge.py` **new separate task / profile V3** | **62.586s** | **1.1k / 1.0k** | `769685fd73a80d21961cd1994bd6aeb6a9fd165e08346d25c5cb6f336be675a5` |

The corresponding raw Worker Receipts remain separately byte-pinned at `f6dac1286bb1fad2ddb525ecf51d3fd86a9149d2a5cc8464f05c5569350cedda`, `c2f81cec7419219f942ec74524864a2159ca233759ba643e193cead7ed5087d5`, `b0cc5ff5e24d33243e65fa7c5f569f7c11bcc275060e76813ed4198e65236fda`. All three local model digests are `7f3251fa6878a78a606bcb3c074283306e5ad2ea411a7774a9dd98a4bc7f2d13`. The original Receipt fields `exact_model_calls=null` and `local_model_usage_tokens=null` remain **unknown** even though Aider displays summary strings. The receipt `model_invocations_min=1` is a minimum, **not** proof of exactly one model backend request.

## Correct interpretation

**These are Aider's display strings, not Ollama's exact prefill/decode token telemetry.** Values such as `1.0k` / `1.1k` are abbreviated, potentially rounded; `940` is likewise only the terminal-reported value. Do not sum them into an exact token budget or compute exact tokens/second, cost/token, deterministic runtime percentile or robust p95. Three different synthetic tasks under different public prompt profiles are not repeated identical workloads or a randomized benchmark. The observed successful Worker elapsed times are *individual actual durations*, not a population latency guarantee.

Source `scripts/vf_office_v2_p0_aider_display_usage_lab.py`, executed source file byte SHA256 `0ac71e674c803c0ff26a13c53983e05d5aec01dcec98c69ffbf6ffbea7b4e6a1`, has **strict offline** `verify` and **21/21** adversarial `selftest` modes rejecting invented exact token totals, causal throughput, false p95, changed Aider stdout/receipt SHA, fake second-host execution or production/fencing claims. The source also has a separately, explicitly invoked manual `observe` mode, constrained to the original Mac Task IDs and `AgentEnvelopeLab`; **CI never calls `observe`**. Sanitized original hashes and UI display strings in the adjacent `p0-three-mac-aider-displayed-tokens-2026-10-10.json`, no raw logs or prompts copied to Git.

**Outstanding next #612 metrics:** instrument a future consented **new** Task Envelope and native Ollama API metrics at the model provider boundary (exact prompt/eval counts and durations if supported) plus worker/aider/runner CPU/RAM and VRAM, including model backend timing. Coordinate fresh local resource checks and #604-owned placement lease. Until then do not claim exact token totals, statistically reliable p95, zero-touch recovery, or production readiness. No Codex CLI, paid API, model rerun, customer/social/printer/CAD operations, new scheduler or credentials.
