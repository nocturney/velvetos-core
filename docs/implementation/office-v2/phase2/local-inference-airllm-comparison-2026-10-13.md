# AirLLM (lyogavin/airllm) — local model streaming challenger intake

**As of:** 2026-10-13 | **Status:** RESEARCH ONLY; NOT INSTALLED / NOT BENCHMARKED / NO HOST LEASE

**Canonical candidate:** `candidate-intake-lyogavin-airllm` in `candidate-registry-v0.json`  
**Owner/receipt:** [Office v2 intake issue #595](https://github.com/nocturney/velvetos-core/issues/595)  
**Evaluation workstream:** `local-model-inference` (same lane as the existing local-model research route; the separate `local-llm-inference` label is folded in. Phase 2 research; future isolated LAB subject to Office P0 and fleet/worker resource gates. AirLLM stays off the P0 shortlist.)  
**Primary source:** https://github.com/lyogavin/airllm  
**Upstream latest reviewed:** v4.0.0, https://github.com/lyogavin/airllm/releases/tag/v4.0.0

## Capability and accurate scope

AirLLM is a Python **LLM inference and streamed LoRA** library. It streams layer/expert weights through limited VRAM from disk / host memory. It is *not* a coding agent, TTS engine, printer pipeline, an orchestrator, a general acceleration layer, or proof that a model can serve interactively on a small GPU.

Upstream claims 70B inference around 4 GB VRAM and extraordinarily large MoE models on limited VRAM, but these are **peak VRAM claims**, not usable throughput or low disk/RAM requirements. For Kimi K3 2.8T, the author's release reports **292 seconds per generated token**, approximately **1.56 TB checkpoint storage**, and **900 seconds process initialization** on an RTX 6000 Ada. These numbers show capability at extreme memory ratios, not an operational online service.

Upstream v4.0.0 also claims streamed LoRA training under 6 GB for a specific model and pinned dependencies; this is an independent research path, not proof of cheap or timely training.

## Counter-evidence and operational concerns

- [Windows NVIDIA issue #364](https://github.com/lyogavin/airllm/issues/364), filed 2026-09-10: a reporter measured 114.5 seconds for four output tokens (28.6 s/token) on a **3B** model with a 16 GB RTX 5060 Ti and local NVMe. This is *one user report*, not a universal bound or a result reproduced on our machines.
- [Compression-speed issue #330](https://github.com/lyogavin/airllm/issues/330), filed 2026-08-04: a user reports 4-bit/8-bit compression ran slower (and peak memory higher) than uncompressed baseline on their tested hardware, despite the README's legacy "up to 3x speedup" marketing. Benchmark rather than assume.
- [Windows AMD issue #301](https://github.com/lyogavin/airllm/issues/301): reported ROCm/Windows `generate()` issues and slow token generation; no AMD host promotion without separate compatibility proof.
- Layer streaming can be dominated by storage, system memory, transfer overhead and Python/runtime operations **for every token**. A 4 GB VRAM figure alone does not show feasibility for real conversational workloads.
- Huge checkpoints can require both original and layer-split copies until cleanup. Do not download until verified disk headroom, host lease, model rights, dependencies, and a teardown path are approved.
- Platform and library versions may differ by model architecture. Pin exact `airllm`, `torch`, `transformers`, tokenizer, model revision, attention and CUDA/ROCm dependencies in a LAB manifest; avoid disturbing existing Python stacks.

## Baseline and competing architectures — no incumbent veto

**Existing/previously documented** local LLM tooling includes an Ollama/loopback inference path and an historical `qwen3.5:9b` Studio model on the Chris host. This is **not a fresh live health or GPU occupancy claim**. Read-only inventory must identify currently installed `Ollama`, `llama.cpp`/GGUF, MLX/Mac backends if present, and related runtimes, rather than presume availability.

Evaluate AirLLM against the *best feasible incumbent or alternative* for the same task:

1. `Ollama` / `llama.cpp` with quantized models and controlled CPU/GPU offload.
2. Existing Transformers/PyTorch path and feasible offload/quantization where useful.
3. MLX-family inference on verified Apple Silicon hosts when model/host matches.
4. AirLLM streamed layers or experts as a specialized oversize-model fallback.

Do **not** treat model quantization and weight streaming as equivalent quality, but compare both task outcome and operational cost, explicitly recording the quality/precision tradeoff. AirLLM may replace a **component**, coexist as a fallback for infrequent offline work, or lose to quantized/offloaded serving. It is not an Office-v2 system replacement.

## Admission and test plan

**Phase SP-0 — NOW, read-only, no GPU spend:**
- Verify repo release/license, current upstream issues and model-specific Hugging Face checkpoints/revisions.
- Deduplicate against the canonical registry and the per-machine Capability Manifest.
- Inventory known installed inference runtimes/hardware from approved read-only evidence; label host/process/resource state VERIFIED NOW vs HISTORICAL vs UNKNOWN.
- Choose a realistic, permitted **oversize** open model (tentatively 27B or 32B, **not downloaded yet**), after disk/RAM/model-license gates. Reserve disk for both original and split forms.

**Phase SP-1 — deterministic fixture and method preparation, no GPU:**
- Prepare identical representative local workflows: 3D parametric-code reasoning, code review/edit planning, Hebrew+English mixed technical instruction, and long-context document extraction; use synthetic inputs only.
- Specify metrics: first-token latency, generated tokens/s, total wall time, cold-start, memory/GPU high-water marks, RAM, temp+persisted disk, I/O throughput, task accuracy, crashes and repeatability, setup/rollback, recurring cost.
- Where the serving model differs in precision/architecture, separate architecture/weights effects from runtime efficiency; compare equivalent model revision/precision where possible, and include the practical best quantized alternative.
- Establish maximum experiment storage/runtime budget and a safe `delete_original` policy only after verifying a non-destructive restore/download plan.

**Phase SP-2 — gated isolated LAB only:**
- Require explicit host GPU/CPU/disk lease and avoid preempting [Office P0 #612](https://github.com/nocturney/velvetos-core/issues/612) and [fleet #604](https://github.com/nocturney/velvetos-core/issues/604).
- Isolated environment/venv; pinned immutable model revision, no public listener, no production secrets/customer data, no printer/publishing authority, no paid APIs or subscription.
- Run same-fixture benchmarks against at least one **currently verified** existing/competitor path. Capture signed/dated receipts and exact host/device/dependency info. Windows Linux/WSL use is a *candidate approach*, not an authorization to install/change OS.
- Tear down the environment; prove no incumbent service/network/listener or resource allocation changed.

**Phase SP-3 — decision:**
- Record comparative scorecard and select: component replacement; optional offline fallback; hybrid; deferred with evidence; or benchmarked-and-lost. Do not invent a universal percentage threshold.
- No production route, orchestrator replacement or auto-activation until required Office security, resource and rollback gates are explicitly met.

## Intake integrity and gates

Source: user-supplied repo link on 2026-10-13. **Not yet verified locally**. No deployment, model download, API charges, worker preemption, privileged bridge, new server, write to printer, or publishing is authorized by this research record. The record itself is the source review of the existing auto-placeholder.

This manual branch/PR creates a **durable recorded candidate**. It does **not** close the unrelated open requirement under [#595](https://github.com/nocturney/velvetos-core/issues/595) for an automated in-chat URL → registry/queued lane intake bridge. Preserve the 68 original source IDs, all historical candidate IDs, and existing shortlists.

### Sources (upstream evidence, not our benchmark)

- https://github.com/lyogavin/airllm
- https://github.com/lyogavin/airllm/releases/tag/v4.0.0
- https://github.com/lyogavin/airllm/releases/tag/v3.1.0
- https://github.com/lyogavin/airllm/issues/364
- https://github.com/lyogavin/airllm/issues/330
- https://github.com/lyogavin/airllm/issues/301
