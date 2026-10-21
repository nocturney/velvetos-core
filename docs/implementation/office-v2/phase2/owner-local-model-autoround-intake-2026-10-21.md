# Owner repo-link intake — Intel AutoRound (2026-10-21)

**State:** RESEARCHED / BENCHMARK_REQUIRED / NOT_RUN / authority NONE. **Scope:** source review and future evaluation routing only; no installation or LAB execution.

## Source and identity

- Official project: https://github.com/intel/auto-round
- Source pin: https://github.com/intel/auto-round/tree/c2dbac79c38806859d858aa169f8bad4e74d937b
- Apache-2.0 project license: https://github.com/intel/auto-round/blob/c2dbac79c38806859d858aa169f8bad4e74d937b/LICENSE
- Upstream README at source pin: https://github.com/intel/auto-round/blob/c2dbac79c38806859d858aa169f8bad4e74d937b/README.md

AutoRound is a **weight quantization/optimization tool**, not an LLM inference server, provider-routing gateway, agent runtime, MCP orchestrator, or substitute for Claude/ChatGPT cloud weights. Official README describes W4A16, GGUF, AWQ/GPTQ and other export schemes, and integration with Transformers/vLLM/SGLang; real exporter/runtime coverage must be verified against the selected model/version.

## Canonical placement and owner

- Office v2 Phase 2 canonical registry: `candidate-intel-auto-round`; intake tracking: [#595](https://github.com/nocturney/velvetos-core/issues/595).
- **Use existing** `local-model-inference` comparative evaluation workstream, owned by [#612](https://github.com/nocturney/velvetos-core/issues/612) after its P0 agent-source-to-PR/independent-QA/recovery baseline. Do **not** add a P0 shortlist member, separate scheduler, new gateway lane or production authority.
- Downstream interface: [Phase 3C](../phase3c/README.md) local provider compatibility. Quantization comparisons are **upstream preparation**, distinct from provider gateway/router selection (LiteLLM/TensorZero).

## Bounded proposed benchmark (NOT RUN)

1. **Preflight:** verify idle hardware and explicit GPU/RAM/disk lease, existing Ollama/llama.cpp/Transformers serving baseline, up-to-date upstream dependency/security status, model weights and calibration-data rights, licenses, cache/downloading bounds, network isolation and full teardown. Start on a genuinely available Windows NVIDIA CUDA workstation (RTX 4080 SUPER only if inventory confirms). AMD/ROCm compatibility and native macOS quantization are **unverified**; optional Apple Silicon GGUF/MLX inference comparisons require separate verified export/runtime support.
2. **Baseline:** use the **same licensed open-weight model revision** for FP16/BF16 reference, ordinary existing GGUF/AWQ/GPTQ quantized control, and AutoRound-generated quantization. First do a small 0.6B smoke before attempting representative 3B–8B if VRAM permits. Pin tokenizer, calibration corpus, context, prompt templates, sampling, quant scheme/bit rate, inference engine/backend, device offload and task/evaluation fixtures.
3. **Task outcomes:** compare held-out Hebrew instruction fidelity and RTL output, structured JSON/schema, simulated tool-calling (no side effects), multi-turn factual/task accuracy, and OpenSCAD/3D code-generation fixtures. Include negative/policy controls and independent artifact/test checks. Separate generator correctness from quantization fidelity.
4. **Efficiency and reliability:** record peak and steady VRAM/RAM/disk, quantization time and total cost, cold/warm startup, first-token latency, output tokens/sec, repeated-run variance, context/KV budget, fidelity against FP16/BF16, backend/export load compatibility, restart/teardown and recovery. Same engine required for isolating quantizer gains; compare alternative engines as a separate controlled dimension.
5. **Decision:** score AutoRound versus incumbent prequantized workflows on **quality at comparable resource footprint**, repeatable speed, time-to-prepare, interoperability, security/rights and maintenance burden. Accept only an evidence-backed practical benefit with no policy regression; document NO-GO if the extra quantization stage loses to already-available prequantized weights.

## Gate and boundaries

**WAITING_GATE.** No model download, GPU claim, package installation, service, autorun, API charge, background job, production routing, credentials, P0 worker interruption or live customer data authorized by this intake. Trigger evaluation only after an independently verified #612 baseline, an uncontested resource lease and explicit separate isolated-LAB admission; preserve `NO_NEW_RECURRING_COST` and leave the current serving/routing stack intact.

This is an evaluation candidate, **not** a benchmark result or a recommendation to install in production.
