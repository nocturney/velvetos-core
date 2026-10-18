# Cross-chat Oct 8 repository review — immediate P0 accelerators

Owner: [Office Infrastructure Accelerator #612](https://github.com/nocturney/velvetos-core/issues/612). Fleet scheduler/worker placement remains [#604](https://github.com/nocturney/velvetos-core/issues/604); Cua UIA remains #602. This is **not** a new task queue, watcher or production authority.

## Decision and strict evidence boundaries

The user provided nine recent repositories and wanted the recommendations that accelerate the **current** P0 implementation, instead of an endless research backlog. Worktrunk and Context Mode are narrow, complementary utilities; Octop and NVIDIA OpenShell are qualified competing/complementary architectures. Do not replace the incumbent solely on promises. Reuse the validated #615 Task Envelope, SHA-256 artifact receipts, Project State checkpoint, protected PR/CI/merge workflow and existing Restate/Dagu responsibilities.

| Repo | Immediate disposition | Verified 2026-10-08 | Next specific acceptance |
| --- | --- | --- | --- |
| [Worktrunk](https://github.com/max-sixty/worktrunk) | **P0 now**, optional worktree lifecycle candidate | **LAB PASS Windows + Mac**: upstream `v0.80.0` release archive SHA-256; created and listed an isolated Git worktree from an original test repo; untracked file caused removal to fail as designed; after removing only the fixture file, `remove --no-hooks --foreground --yes --no-delete-branch` cleaned child and **preserved branch** | Link this existing ready-made CLI to ONE owned P0 Task Envelope, pinned branch/base, independent verifier, cleanups, negative path/dirty tests, and compare time/resource footprint against native `git worktree`; **no auto merge** |
| [Context Mode](https://github.com/mksglu/context-mode) | **P0 adjacent**, add as an optional OpenCode context filter when baseline available | **LAB PASS Windows + Mac**: isolated NPM `1.0.169` with scripts disabled; local CLI indexed and searched a benign FTS5 Markdown fixture using dedicated `CONTEXT_MODE_DIR`. No globally registered OpenCode plugin | Same OpenCode coding task with plugin on/off, target **at least 30% verified input-token reduction** without correctness, permission or context recovery regressions; compare OpenCode experimental hook behavior and license (Elastic-2.0); never replace canonical Project State |
| [TencentCloud Octop](https://github.com/TencentCloud/Octop) | **P0 competitor only after independent agent baseline** | Research only; AgentTeams Beta, outbound ACP/OpenCode integration documented; no installation, real code task, cross-host or memory benchmark | Same coding fixture and recovery/quality/cost/throughput as standalone OpenCode and the existing Restate/Dagu path; full replacement/hybrid remains eligible; do not create second scheduler |
| [NVIDIA OpenShell](https://github.com/NVIDIA/OpenShell) | **P0.5 isolation pilot** if capacity available | Research only; no local container/sandbox launch or policy drill | Two bounded coding tasks, restrictive file/network controls, intentional denial and restart/resource comparison. Linux/container sandbox does **not** replace native Windows GUI access or agent execution engine |
| [tester-army/e2e](https://github.com/tester-army/e2e) | P1, not a P0 engine | Prior cross-chat review, **no install** | Deterministic Playwright/CI UI postconditions before optional model-guided tests |
| [FreeLLMAPI](https://github.com/tashfeenahmed/freellmapi) | P1 conditional Phase 3C gateway experiment | Prior review, **not installed** | Only test allowed no-added-cost quota/provider behavior if direct P0 inference access needs it; do not assume free SLA or replace model gateway |
| [JustVugg/colibri](https://github.com/JustVugg/colibri) | P2 local inference provider alternative | Prior review, **not installed** | Bench quality/latency/VRAM with current Ollama local model once coding agent baseline exists |
| [agent-substrate/substrate](https://github.com/agent-substrate/substrate) | P2 architecture reference | Prior review, **not installed** | Defer until measured executor/orchestrator gap |
| Storytold ecosystem | Domain-specific later | Prior review, **no install** | Separate PhotoCraft/PdfCraft CLI/MCP source fixture after core agent platform stabilizes |

## Proposed additional comparison lanes, intentionally not frozen yet

The existing **six** Phase 2 shortlists remain unchanged as benchmark sets. Two new candidate-specific comparison lanes are documented without falsely placing utilities in the agent-runtime shortlist:

* `development-worktree-lifecycle`: incumbent **native Git worktree scripts**; candidate **Worktrunk**; acceptance is exact pinned setup, leak-free cleanup, no dirty-data loss, disk/time and branch/PR isolation. Add an actual frozen short-list only once a second credible alternative and same-fixture comparator exist.
* `agent-sandbox-isolation`: incumbent **existing host/checkout policy boundary**; candidate **OpenShell**; compare constrained per-agent filesystem/network/process isolation, denial, restart and measured overhead in independent LAB only. Not a substitute for #604 placement or #612 agent coding.

Context Mode is queued in `memory-context` only for **noncanonical context virtualization**; Octop queued in `agent-runtime` as a full/hybrid candidate. No incumbent/winner or current three active agent challengers changed, and the immutable **68-source import** is intact.

## Machine paths and receipt

Worktrunk Windows executable staged at `D:\Velvet\Tools\OfficeAccelerator\WorktrunkPilot\v0.80.0\runtime\git-wt.exe`; Mac at `/Users/chris/Velvet/Pilots/OfficeAccelerator/WorktrunkPilot/v0.80.0/runtime/worktrunk-aarch64-apple-darwin/wt`. Context Mode Windows staged under `D:\Velvet\Tools\OfficeAccelerator\ContextModePilot\v1.0.169`; Mac under `/Users/chris/Velvet/Pilots/OfficeAccelerator/ContextModePilot/v1.0.169`. Both use separate fixture DB/temporary repo directories with no production writer. No global shell installation or OpenCode plugin enrollment.

Evidence manifest: [p0-ready-made-accelerators-lab-2026-10-08.json](p0-ready-made-accelerators-lab-2026-10-08.json). Exact tests passed but no two-host agent inference coding task, no Context Mode token-saving benchmark and no OpenShell or Octop runtime proof. Do not mark overall P0 green.

## No-drop sequence

1. Keep #612 as the single owner and #604 as the separate fleet owner; no new automation or task authority.
2. Use Worktrunk behind bounded Task Envelope and independent receipts when safe. Explicitly avoid `wt merge`, `--force` removal and unreviewed hooks.
3. First establish **actual** coding-agent baseline using already staged OpenCode and local Qwen3.5 Ollama models; the local model binaries/models were verified/staged in the prior working session but two-host autonomous code PR acceptance is not yet proven.
4. Evaluate Context Mode baseline-on/off and then Octop full/hybrid comparison only if model/tool-call/permission quality passes.
5. OpenShell isolated LAB is optional in parallel with spare resources, not a blocker on model/agent selection; no extra subscription, Codex CLI, WSL disruption, social/customer/printer actions, or production credential exposures.
