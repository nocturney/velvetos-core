# Office v2 P0 — Read-only Ollama inference runner correlation on a real Mac coding task

**Date:** 2026-10-09 | **Issue:** [#612](https://github.com/nocturney/velvetos-core/issues/612) | **Scope:** one fresh synthetic real local coding task on MacMiniOffice.local, no production writer, no cross-host fleet lease.

## Purpose

Previously completed P0 LAB proved OS birth-pinned Worker and Aider CPU/RSS sampling, but **not** inference-server memory. This stage independently sampled one native Ollama `serve` process and its child `runner` while a new verified original Worker/Aider Task Envelope was executing a local Qwen3.5:4B coding fix. The passive sampler never launches, stops, configures or retries the Worker, Aider, model or Ollama process.

## Real procedure and outcomes

1. Began with `/api/ps` empty, exact `ollama serve` native PID **99094**, verified OS process birth (`PSUTIL_OS_CREATE_TIME`), one local Ollama endpoint at `127.0.0.1:11556`. Source checkpoint commit `468f070da8d88c113210328b1be7cf8a7fbb9927`, script raw LF SHA256 `6c57e5c4bd06105134aeba6f5c960c0d08e4af605364dd7ca0699d4becefacc8`.
2. Created fresh, isolated Task `p0-ollama-observed-mac-20261009-02` with pinned Git base `ecabd70a292bc11ae4d8009a44502cb42ca1c0c9`, source/test, one-attempt zero-paid-budget envelope, real Aider v0.86.2, model `qwen3.5:4b` with exact digest `7f3251fa6878a78a606bcb3c074283306e5ad2ea411a7774a9dd98a4bc7f2d13`, and continuity checkpoint.
3. Started **only a passive observer** in its own, exclusive `p0-ollama-runner-observer-mac-20261009-b` root; independently read its ready status. Then separately launched the original P0 Worker, whose fsynced `RUNNING` journal and native Worker/Aider kernel pin were read and validated by the observer. The parent OS instance of native `ollama runner` PID **69666** matched the earlier `serve` native identity. The model name/digest in read-only `/api/ps` matched the Task Envelope at each sample.
4. Collected **10** read-only native OS process-birth-pinned `runner` and `serve` RSS and cumulative CPU samples, checking original native birth both **before and after** each metric read. The observed model was not preloaded on admission; an Ollama `/api/ps` request timed out **once** during warmup and was retried read-only under a bounded startup window. No model requests from the observer.
5. Observer completed `PASS_ONE_CORRELATED_OS_PINNED_OLLAMA_RUNNER`; separately invoked historical `verify=PASS`. Original Worker subsequently `SUCCEEDED` in **43.341 seconds**, artifact SHA256 `456f89bec0af23e6287e88956b8b85e992d4926b89e9613238bee7f77302ab45`, independent **3/3 visible + 12/12 hidden** QA. Separately invoked original Worker `verify=PASS` confirmed checkpoint, native pin, model/log artifacts and independent replay. No prior UNKNOWN Task was retried.

| Verified observation | Value |
|---|---:|
| Native runner PID | 69666 (child of Ollama serve 99094) |
| Number of exact model-digest/PID-birth samples | **10** |
| Peak sampled runner resident RAM | **3,687,776,256 B** (~3.69 GB decimal / ~3.43 GiB) |
| Peak sampled Ollama serve resident RAM | **22,429,696 B** (~22.43 MB) |
| Runner cumulative CPU delta over samples | **2,126 ms** |
| First `/api/ps` `size_vram` reported for resident model | **3,953,628,688 B** (~3.95 GB decimal) |
| Ollama startup transient API read timeouts | **1**, read-only bounded retry |
| Original real coding Worker elapsed | **43.341 seconds** |
| Original independent QA | **3/3 unit + 12/12 hidden PASS** |
| Additional paid inference/API spend | **$0** |
| Model calls, process controls or scheduler actions by observer | **0** |

`/api/ps.size_vram` is **Ollama's API-reported loaded-model residency**, NOT independently measured hardware GPU VRAM, and particularly **not dedicated-VRAM consumption on unified-memory Macs**. Runner RSS does not equal a unique physical memory footprint because of shared mappings, and the server+runner are separate processes; do not sum these with other per-process peaks as if each sample occurred simultaneously. Time-series samples are **not** a proven true resource peak or full-lifecycle accounting. Even one loaded model on `/api/ps` **does not prove exclusive client access**; cross-client attribution, CUDA/Metal VRAM use and energy/cost remain unknown.

## Exact original evidence/provenance

- Source code original commit `468f070da8d88c113210328b1be7cf8a7fbb9927`; script SHA256 `6c57e5c4bd06105134aeba6f5c960c0d08e4af605364dd7ca0699d4becefacc8`.
- Original raw SHA256 envelope: `fda549a0feb58b5e03f456720a559e890d37e130eb75d7f99780e7453f6f3fae`.
- Original raw Worker Receipt: `2522204a87f531d53faf97e3ab335066954da5cd40c6d1c751559a871e08f012`.
- Original raw kernel pin: `d0e02c179cbf56807c3f18b9524444fbacc05ae22192bd9b3ea3b4f82d20a116`.
- Original raw observer report: `488aa3bd22ae200b78f40c5e1a321fb81321bb994e4ff2c2ddcf4f962bbabff9`.
- Original Worker self-hash: `3ef20205569c88108191e59d40ee7cf3d823d28a9a0da150d118b43bf66ec02b`.
- Observer report self-hash: `f1d020804841632d16c21766692b1bf9fc4d64e605d1f729b6a798c9916fe263`.
- Sanitized historic 10-sample report and independent QA are in `p0-mac-real-ollama-runner-correlated-resources-2026-10-09.json`; original unchanged bytes and full logs remain in dedicated Mac `AgentEnvelopeLab` roots. Hashes are integrity records, not external digital signatures.

## Fail-closed warmup control

An **earlier, separate** observer-only attempt (`p0-ollama-runner-observer-mac-20261009-a`) exited `FAIL_CLOSED / LOCAL_OLLAMA_API_UNAVAILABLE` while the model was loading. The original distinct task `...-01` continued separately to `SUCCEEDED`, its original Worker `verify=PASS`, and it was **never rerun or automatically recovered**. The observer implementation was then changed to tolerate only transient read-only startup API failures within a bounded 75-second window, with 26/26 adversarial offline cases, and a **fresh Task Envelope ...-02** was launched after the original had completed. Thus no UNKNOWN or completed Task was reused.

## Authority limits and next gates

CI invokes only `selftest` and historical source/hash/shape validation; it **never starts real processes/models, or invokes `observe`**. No Codex CLI, paid API call, production service/config changes, GUI/CAD interruption, social/customer/printer/physical machine effects, new queue/daemon/watch, UNKNOWN recovery or cross-host lease was created. Overall #612 P0 remains **PARTIAL**: user-visible code productivity still needs **two different nonoverlapping real repository changes by workers on two physical hosts**, independent protected PR/CI/serial merges, a reliable multi-run p95, operator time, full CPU/RAM/GPU/VRAM inference resource usage and crash/reconciliation. #604 remains sole canonical cross-host placement/lease/fencing authority.
