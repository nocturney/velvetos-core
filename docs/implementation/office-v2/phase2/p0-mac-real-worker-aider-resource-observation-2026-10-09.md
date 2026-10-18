# Office v2 P0 — Actual Worker/Aider CPU-RSS observation on Mac (LAB-only)

**Date:** 2026-10-09 | **Issue:** [#612](https://github.com/nocturney/velvetos-core/issues/612) | **Scope:** one fresh synthetic Task Envelope with **real local Qwen3.5:4B/Aider inference** on Mac Mini, independent passive observation of two exact OS process identities.

## Why this gate matters

Previous Office P0 work proved actual local coding+QA (five sequential runs), and the two-host OS-owned CPU/RSS sampler independently proved correct native process identity and metric reads. Those did **not** demonstrate sampling CPU/RSS during a **real Aider coding attempt**. This LAB executes one new, uniquely named task with a separate observer. The observer never launches/stops/changes the original Worker or Aider and cannot authorize another attempt, a scheduler, distributed lease, external effect, or production write.

## Procedure actually executed

1. From exact clean code commit `5d8b6613c18b3973344efe193fac139ec9bc458d`, the existing `vf_office_v2_p0_local_model_fixture.py` prepared a fresh synthetic Git branch, `slug.py` unit tests, 12 hidden QA assertions, prompt, Task Envelope and checkpoint for `p0-observed-worker-mac-20261009-01`. Source model digest: `qwen3.5:4b` / `7f3251fa6878a78a606bcb3c074283306e5ad2ea411a7774a9dd98a4bc7f2d13`, Ollama `localhost:11556`.
2. The new passive `vf_office_v2_p0_owned_worker_aider_sampler.py observe` opened its **own fresh**, mutually exclusive observer root and wrote `ready.json`. The original canonical Worker `run` was then launched **separately**, not by the observer.
3. The observer saw the original fsynced `receipt.json.running` and `kernel-pin.json`, checked the canonical Task Envelope/journal/pin binding with `kernel.checked_pin`. For each of **12** samples, it checked native OS **PID + birth time before and after metric reads** for both the Worker and the child Aider process. Mac uses OS-backed psutil `create_time`, `memory_info().rss` and cumulative CPU counters, and no process-name enumeration. No model backend process was sampled.
4. The independent observer exited with `PASS_PINNED_REAL_LAB_WORKER_AIDER_CPU_RSS_OBSERVED`. The original Worker ran to `SUCCEEDED` with real local inference and saved its normal Worker Receipt. Afterward, two separately invoked verification CLIs returned PASS: original Worker `verify` (independent fresh-clone QA, receipt, logs, checkpoint and kernel pin) and observer `verify` (historical report shape/hash), without rerunning the model.
5. The original envelope, Worker Receipt, kernel pin and observer report remain unchanged on the Mac under separately owned `AgentEnvelopeLab/p0-observed-worker-mac-20261009/...-01` and `AgentEnvelopeLab/p0-real-observer-mac-20261009-02`. Exact raw SHA256s are pinned in the sibling sanitized JSON.

An initial **observer-only** attempt failed before any worker/model launch due to missing `import platform`; its own scratch root `p0-real-observer-mac-20261009-01` contains no completed measurement. This was corrected in code commit `5d8b6613`, the pure offline selftest was extended, and the fresh successful observer root `...-02` was used. The original prepared Task Envelope remained untouched/unexecuted until the corrected sampler was ready. **No ambiguous Worker task was retried.**

## Measured results

| Actual metric | Observed value |
|---|---:|
| Independently verified real local coding task | **SUCCEEDED / PASS** |
| Original Worker elapsed `receipt.elapsed_seconds` | **49.241 s** |
| Worker + Aider paired OS-birth-checked samples | **12** |
| Observed peak Worker RSS | **34,930,688 B** (≈33.31 MiB) |
| Observed peak Aider RSS | **172,425,216 B** (≈164.44 MiB) |
| Observed maximum combined Worker+Aider RSS in one sample | **207,339,520 B** (≈197.74 MiB) |
| Worker cumulative CPU delta, first-last sample | **0 ms** |
| Aider cumulative CPU delta, first-last sample | **4,949 ms** |
| Independent visible QA | **3/3** |
| Independent hidden QA | **12/12** |
| Observer model calls and extra paid API spend | **0 / $0** |

The combined RSS value is the **sum of two selected Python processes at the same sample**, not system RAM usage, Ollama inference server memory, GPU/VRAM usage, or a full descendant tree total. The Worker CPU delta rounds to 0 across the brief observed interval; it is not proof of total zero Worker CPU during the 49s task. The intervals do not cover the complete coding process. The single-run observed peak is not a reliable peak upper bound or SLA.

## Source identity and original raw hashes

- Executed source commit `5d8b6613c18b3973344efe193fac139ec9bc458d` (branch `office-v2/p0-live-owned-aider-resource-probe-20261009`). Raw observer source SHA256 `ad52d5ce56f504ac1e6105b4e4cc32801fea6f21cb3104512a2b3a01cd2fcaf7`. Original Worker raw source SHA256 `7b4cb176c9c66351f9658c08589f45ec94d50c2a8b6450fe8e5cb1d8f09d86f7`.
- Original task Git base `17e304738bd05f526b6c29174dd3f6b6cc9b8d9e`; task `p0-observed-worker-mac-20261009-01`.
- Original Worker receipt seal `9de9ff084b1bfd8e5258f7732ad8e2a449681b131143522308e9a4d3b185f1ba`. Original observer receipt seal `06c68d07487b120389601a503089cfd7b050d2a4aa13ec6eab59aff53a5623cb`.
- Raw SHA256s: envelope `b45932d4feae257f0de11329d3f84288ac3e45745301e08ecd91cec012ef0767`; Worker Receipt `0ec632d2fecd772756ddbaf5a0eff5aaf4ef49220fa3bc2ece7475e3e19fdefe`; kernel pin `8c5bc727bea0ee9a4d2c3893370693b437c82f9cc167d61f91ea5f07843ee319`; observer report `6d764e33f210fe207d399919daa073a8e0a4816fdc3e2919859ff50053d4ce28`.
- Exact 12 timestamps, both kernel birth identities, per-process RSS/CPU cumulative counters, immutable identity/budget/QA bindings and scope limits are in the sanitized JSON. Self-hashes are not cryptographic signatures by an external trusted authority.

## Nonclaims and follow-up gate

**Overall P0 remains PARTIAL.** This is one synthetic coding task on **one** Mac, not diverse real-repository PR work, two-host concurrent coding throughput, a statistically stable p95, full model inference CPU/RAM/VRAM accounting, reliable true resource peaks, all orphan exclusion, or autonomous UNKNOWN reconciliation. CPU/RSS collection is read-only and can be re-verified offline; **CI must never invoke `observe`, launch a local model, recover/retry, or change scheduler/production authority**. #604 still owns any canonical cross-host worker lease/fencing, and an actual effect receiver must reject stale owners.

No Codex CLI, paid remote API, credentials, printing, Instagram/WhatsApp, customer operations, production state, or unrelated OS process was touched.
