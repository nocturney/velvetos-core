# P0 coding agent CLI alternatives — discovery / admission (2026-10-08)

Owner: [#612](https://github.com/nocturney/velvetos-core/issues/612); existing fleet scheduler owner: [#604](https://github.com/nocturney/velvetos-core/issues/604). No extra runner or parallel authority is created by research/intake.

## Why this change

The initial P0 offline execution layer is merged in PR #615 and passed independent Windows full-suite postmerge QA. Its pinned Python fixture runner does **not** call a model, qualify as an autonomous coding agent or demonstrate distributed execution.

Direct host readback on 2026-10-08: **Chris Windows** and **MacMiniOffice.local** have no `opencode`, `goose`, `aider`, `ollama`, `codex` or `claude` in current PATH. No local model server was found on the usual Ollama/LM Studio/llama.cpp ports; Mac port 5000 belongs to Control Center, not a model endpoint. Chris RTX 4080 SUPER has 16 GB physical VRAM, Mac has 16 GiB unified memory. Lack of a local model does not imply no other legally usable subscriber-backed provider exists; that is **unverified**. Codex CLI remains prohibited due the owner's separately limited quota.

## P0 candidates queued without changing current shortlist

| Candidate | Documented capability | License | Open gate |
| --- | --- | --- | --- |
| [OpenCode](https://github.com/anomalyco/opencode) | `opencode run`, `--format json`, per-model agent, Windows/Mac; [official automation docs](https://opencode.ai/v2/docs/cli/commands/) | MIT | Installed/version/authenticated provider not verified; no real coding result |
| [AAIF Goose](https://github.com/aaif-goose/goose) | Cross-platform CLI/API, MCP and Ollama/local-model provider; [upstream](https://github.com/aaif-goose/goose/blob/main/README.md) | Apache-2.0 | Noninteractive command contract, tool permissions, model cost and actual result not verified |
| [DeerFlow 2.0](https://github.com/bytedance/deer-flow) | Already in Office Registry; larger multi-agent, memory, sandbox candidate | See #600 | Full real runtime / identical coding fixture untested |
| [Aider](https://aider.chat/docs/llms/ollama.html) | Lightweight CLI with explicit local Ollama backend | See upstream | Additional candidate only; no new Registry row or installation in this PR |

The canonical source inventory remains 68 items; registry grows **92 to 94** without changing the active incumbent / Herdr / Pydantic AI / Mastra shortlist, winner or production authority. Both new entries remain `RESEARCHED`, `NOT_RUN`, `BENCHMARK_REQUIRED`, `authority_role=NONE`. The rule is **competitor-neutral**: compare whole replacement, partial substitution or hybrid, not automatically dismiss a competitor as duplicate.

## Before first model call or worker promotion

1. Pin official binary/package version, hash, license and network/telemetry behavior in an **isolated LAB** (no global installer, no repo production secrets). Validate noninteractive `--help` and version only.
2. Verify a **zero-additional-recurring-spend, permitted inference route** (local model or already authorized entitlement) instead of assuming open-source CLI means free models. Official [Ollama + OpenCode documentation](https://github.com/ollama/ollama/blob/main/docs/integrations/opencode.mdx) recommends **64k+ context**, which may overwhelm limited VRAM and require CPU fallback; benchmark memory and real tool-calling reliability.
3. Route a genuine coding change through the already merged Task Envelope/receipt + existing canonical continuity check, separate Git checkout and independent tests. No generic production filesystem, uncontrolled shell, user desktop, or external effects.
4. Run **the same input/code task** for feasible OpenCode, Goose, incumbent/DeerFlow, record model, throughput, spend, RAM/VRAM, quality, crash semantics, exact PR and post-merge receipt. Select best measured configuration; do not presume OpenCode winner.
5. Leave #604's durable scheduling/concurrency/host-failure experiments to its unique owner and do not start a second fleet.

No external model calls, Codex CLI invocations, system service registrations, profile/production changes or purchases happened during this admission.
