# Mozilla AI llamafile — source-pinned local inference intake (2026-10-14)

**State:** `RESEARCH_ROUTED_NOT_EXECUTED` · **Candidate:** `candidate-mozilla-ai-llamafile` · **Canonical target:** Phase 2 Candidate Registry → Phase 3C local inference-provider comparison under [#612](https://github.com/nocturney/velvetos-core/issues/612), not a new gateway or scheduler. No LAB execution or production change.

## Source facts and limitations

- Owner-supplied [llamafile](https://github.com/mozilla-ai/llamafile), researched at immutable [HEAD `a3ccf098ed9c7c77687f5430b0143156d3bcc45a`](https://github.com/mozilla-ai/llamafile/tree/a3ccf098ed9c7c77687f5430b0143156d3bcc45a); official [v0.10.6 release](https://github.com/mozilla-ai/llamafile/releases/tag/0.10.6) published on 2026-09-15.
- Source license: Apache-2.0; model weights, binary redistributions and dependencies need independent rights verification. See pinned [README](https://github.com/mozilla-ai/llamafile/blob/a3ccf098ed9c7c77687f5430b0143156d3bcc45a/README.md), [API](https://github.com/mozilla-ai/llamafile/blob/a3ccf098ed9c7c77687f5430b0143156d3bcc45a/docs/api.md), [supported platforms/GPU](https://github.com/mozilla-ai/llamafile/blob/a3ccf098ed9c7c77687f5430b0143156d3bcc45a/docs/support.md), [security](https://github.com/mozilla-ai/llamafile/blob/a3ccf098ed9c7c77687f5430b0143156d3bcc45a/docs/security.md).
- Local GGUF / llama.cpp-based inference with portable file delivery. Server exposes OpenAI-compatible and Anthropic-compatible endpoints. NVIDIA CUDA on Windows and Apple Silicon Metal are described by upstream, **not verified on our hosts**. GPU silently falling back to CPU is a concrete test risk.
- Windows model-embedded executables above 4GB are not supported; compare larger models using external GGUF weights. v0.10.x compatibility, GPU modules and security features require current release-specific checks.
- `whisperfile` is a separate speech-to-text program; optional voice follow-up only after a separate task gate.

## Place in the existing execution path

1. Registry entry: `candidate-mozilla-ai-llamafile`, `RESEARCHED / BENCHMARK_REQUIRED / NOT_RUN / NONE`; registry 131 → 132. The original 68-source import and historical 82-ID prefix stay fixed.
2. Typed route: `local-model-inference`, owner [#612](https://github.com/nocturney/velvetos-core/issues/612), Phase 3C [local-provider semantic contract](../phase3c/README.md), `WAITING_GATE`. This is **not** an additional LiteLLM/TensorZero `model-routing` contender or an `agent-runtime` entry; the P0 shortlist remains unchanged.
3. Evaluate partial Ollama **component replacement** or portable **hybrid/fallback** only after comparative evidence. No reason to reject due to overlap.

## Future benchmark — NOT RUN

- **Unlock:** prove the existing #612 zero-new-cost OpenCode/Ollama local source-to-PR/independent QA/recovery baseline and Phase 3C incumbent/provider routing baseline; prove a free isolated host/VRAM lease that does not interrupt any in-flight worktree, GPU or session. No Codex CLI or new paid model API.
- **Pin** identical licensed model/weights/quantization, version, prompt, context, tool-call schema, sampling and GPU offload across Ollama and llamafile. Record actual release artifact SHA; researched source HEAD alone does not pin a downloadable executable.
- **Exercise** `/health`, `/v1/models`, `/v1/chat/completions` and applicable Anthropic `/v1/messages` with identical synthetic allowed/denied tool and fallback semantics. Server tool-calling is **not tool authorization**: all client execution uses canonical VelvetOS policies; no live effect credentials.
- **Measure** cold/warm latency, output tokens/sec, quality of response and tool calls, context reliability, CPU/GPU/RAM/VRAM/disk, confirmed GPU offload vs CPU fallback, startup/shutdown/crash/recovery, Windows external-GGUF limitation, reproducibility, security, incremental cost and rollback on an accepted Windows RTX 4080 SUPER or Apple Silicon host.
- **Outcome:** standard scorecard and receipts, only then evidence-based admission/rejection/fallback decision. No new service, autostart, daemon, public listener, production gateway selection or promoted authority.

`NO_NEW_RECURRING_COST` and existing approval/effect policy stay binding. This is research and a test gate, not installation or permission to deploy.

[Machine-readable pinned intake receipt](owner-local-inference-llamafile-intake-2026-10-14.json).
