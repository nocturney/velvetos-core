# P0 — Native owned-process CPU/RSS observation LAB on Windows and Mac

Date 2026-10-09 | Issue [#612](https://github.com/nocturney/velvetos-core/issues/612) | **SYNTHETIC CHILD ONLY, NO MODEL WORKER OR PRODUCTION AUTHORITY**

## Objective

PR #645 supplied five real Qwen/Aider coding latency receipts (44.632–48.576 seconds) but no per-run CPU/RAM/VRAM series. Before touching actual Agent processes, we implemented a tiny bounded, OS-birth-pinned native resource observer in `scripts/vf_office_v2_p0_native_resource_probe_lab.py` and executed it **independently on both actual hosts**.

## Method and real evidence

- Each host created its **own exclusive fresh** `AgentEnvelopeLab/p0-resource-probe-{win,mac}-20261009-a` scratch root and **only one new 12 MiB Python child**. The fixture touched allocated pages, performed a very small bounded CPU loop and waited for `stop.flag`. Its parent owned its exact `Popen` handle.
- Both hosts captured native process identity before sampling via canonical `vf_office_v2_p0_kernel_identity.sample(pid)`: Windows used `Win32_Process.CreationDate`; Mac used psutil's OS process creation time. For **each of six samples**, the observer rechecked `kernel.match` against the original PID/birth identity **before** reading that process's RSS/CPU counters; any PID reuse, identity drift or child disappearance fails closed.
- Windows metrics used read-only `Get-Process -Id <exact-owned-PID>` for WorkingSet64 and cumulative CPU milliseconds; Mac used `psutil.Process(<exact-owned-PID>).memory_info().rss` and `cpu_times`. There was **no global process enumeration** or kill outside the new fixture.
- After sampling the parent signaled only the fixture and verified that child exited, retained a self-hashed report. No model was started and no business state was touched.

| Native readback | Chris Windows | MacMiniOffice.local |
|---|---|---|
| OS identity backend | WINDOWS_CIM_CREATION_DATE | PSUTIL_OS_CREATE_TIME |
| Observed synthetic child PID | 41764 | 59537 |
| Samples per exact owned child | 6 | 6 |
| Peak measured RSS | 32,198,656 bytes (≈30.71 MiB) | 38,584,320 bytes (≈36.80 MiB) |
| First-to-last cumulative child CPU delta | 16ms | 4ms |
| Live owned probe | PASS | PASS |
| Offline independent receipt verification | PASS | PASS |
| 22 offline adversarial controls | PASS | PASS |
| Receipt self-hash | `a872b53f5d560db404cc13d8bdee56f56b571f4c80d11d3213b8c79c5b7703ed` | `5be67076bd3a46cb2c97d062a1fd5a7096b1dc6ed1897cf444fbf815852bb98f` |
| Original raw report SHA256 | `71e9bbb1cd301d8978deb45cf17a8f5dcb22ba5513ece4561dd8d99ede4d6529` | `0a38e8af93e7e6431dca4646a5c9ff6fe9bd7a9febf33d31b7dc94f684bde5d7` |

All six native sample objects and their original receipt seals are preserved in the sanitized `p0-two-host-owned-resource-probe-2026-10-09.json`. The raw report bytes remain in each host's exclusive scratch root. Self-hashes confirm consistency, **not externally signed authenticity**.

## Source pin and safe execution

Original source checkpoint commit `405c7af4862bc11a1de285eb1f221b8f7183448e`, Git source blob `e50ebddae5ccfc7463980958340be34e3b5bef9c`, raw LF SHA256 `a640328463d43ed1ab1b74c9585c1edc7681534aa3ac6928da001fbcb60d6b1e`; baseline main `cdbb557938628938577d698925e0007dc902da65`. A pure `selftest` rejects 21 deceptive/invalid cases plus one positive contract, **22/22**. `verify` checks historic receipt only. Cloud CI **never** invokes the script's `live` or OS process fixture.

## Honest limits and next gate

These are **synthetic memory-fixture RSS/CPU samples**, not Agent/Aider resource usage. The different Python versions/OS environments mean the two peak RSS numbers are **not benchmark rankings**. A six-sample trace does **not** establish true per-model CPU/RAM peaks, memory attribution, GPU VRAM, exact tokens, power, host-wide utilization, sustained throughput, fault recovery, complete orphan exclusion or distributed lease/fencing. Next gated task: attach the same birth-checked sampler to *one newly admitted, explicitly owned model Worker*, produce aligned model receipt/QA and measure CPU/RAM (plus GPU only where independently observable), without creating a background daemon or extra job authority. The current script must not be silently promoted into a production monitoring agent.

No paid APIs, Codex CLI, model invocations, user GUI/CAD/process interruption, credentials, printing, social/customer operations or OS security modifications occurred in this LAB. #604 remains the sole Fleet lease/placement owner.
