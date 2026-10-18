# Candidate triage batches 1, 2 and 4 (corrected), 2026-10-18

Issue: `nocturney/velvetos-core#595`. This is the repo copy of Cursor's triage comments for batches 1, 2 and 4, with the four rows from Claude's CLQ-8 verdict corrected. Report only: no registry edits, no install, no promotion. KEEP and REJECT are unchanged.

Source comments: [batch 1](https://github.com/nocturney/velvetos-core/issues/595#issuecomment-6248268135), [batch 2](https://github.com/nocturney/velvetos-core/issues/595#issuecomment-6248268285), [batch 4](https://github.com/nocturney/velvetos-core/issues/595#issuecomment-6248268442). QA: [QA verdict (Claude)](https://github.com/nocturney/velvetos-core/issues/595#issuecomment-6248863214) — batch 1 FAIL, batches 2 and 4 PASS. Machine-readable data: `candidate-triage-batches-124-2026-10-18.json`.

Owner clarification applied in the source comments: the #632 Israeli-creator gate is for 3D-printing models only. These rows are software.

## Corrections

Checked against the GitHub REST API on 2026-10-18.

| # | Candidate | Verdict | What changed |
|---|---|---|---|
| 13 | dagger/container-use | KEEP | The 2026-09-21 push is Dependabot branch `dependabot/go_modules/minor-83ac690e78` (`2026-09-21T14:05:01Z`). Default branch `main` last commit is `2026-08-12T16:30:35Z`, 67 days before this check. |
| 14 | danielhanchen/llama.cpp | REJECT | Compare `ggml-org/llama.cpp` `master...danielhanchen:master` returns `status=behind`, `ahead_by=0`, `behind_by=2129`, `total_commits=0`. Reason is now `fork with no own commits (ahead 0, behind 2129 at check time)`. |
| 20 | emilk/egui | KEEP | License text is MIT OR Apache-2.0 (`LICENSE-MIT`, `LICENSE-APACHE`, README). GitHub's SPDX field still says Apache-2.0 alone. |
| 24 | gastownhall/gastown | KEEP | API `pushed_at` is `2026-10-18T00:11:20Z`, so the date is not wrong. That push is Dependabot ([#4928](https://github.com/gastownhall/gastown/pull/4928), [#4929](https://github.com/gastownhall/gastown/pull/4929)), both opened and closed in that minute. Across the 138 branches still present, the newest commit is `main` at `2026-07-23T13:03:02Z`. |

## Batch 1 (candidates 1–15)

| # | Candidate | Verdict | Reason | Source |
|---|---|---|---|---|
| 1 | agent-substrate/substrate | KEEP | Maintained agent-core system (5,445 stars, Apache-2.0, last push 2026-10-18) | https://github.com/agent-substrate/substrate |
| 2 | Astro-Han/karpathy-llm-wiki | KEEP | Agent Skills-compatible LLM wiki for Claude Code, Cursor, and Codex (2,512 stars, MIT, last push 2026-07-23) | https://github.com/Astro-Han/karpathy-llm-wiki |
| 3 | backnotprop/pstack | KEEP | Maintained skills and principles for rigorous AI-assisted engineering with Claude, Codex, and pi (2,158 stars, MIT, last push 2026-10-15) | https://github.com/backnotprop/pstack |
| 4 | earendil-works/pi | KEEP | Registry entry badlogic/pi-mono redirects here; maintained AI agent toolkit with unified LLM API, agent loop, TUI, and coding CLI (116,021 stars, MIT, last push 2026-10-18) | https://github.com/earendil-works/pi |
| 5 | BBuf/AI-Infra-Auto-Driven-SKILLS | KEEP | Active agent skills for LLM-serving benchmarks, profiler triage, and inference stacks; GitHub license API 404 (982 stars, no license file, last push 2026-10-18) | https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS |
| 6 | BerriAI/litellm | KEEP | Maintained AI gateway for 100+ LLMs; LICENSE grants MIT outside enterprise/ (61,465 stars, GitHub SPDX NOASSERTION, last push 2026-10-18) | https://github.com/BerriAI/litellm |
| 7 | cactus-compute/cactus | KEEP | Maintained quantization, kernels, and inference runtime for phones, wearables, and robots (6,127 stars, custom license, GitHub SPDX NOASSERTION, last push 2026-09-26) | https://github.com/cactus-compute/cactus |
| 8 | cactus-compute/needle | KEEP | Maintained on-device automation foundation model with tool calls, ASR, and embeddings (14,075 stars, Apache-2.0, last push 2026-10-17) | https://github.com/cactus-compute/needle |
| 9 | cbrock84/headcount | KEEP | Maintained installable agent-organization skills for Claude Code and ChatGPT (2,067 stars, MIT, last push 2026-09-17) | https://github.com/cbrock84/headcount |
| 10 | charlie947/social-media-skills | KEEP | Public Codex and Claude skills for social writing, research, analytics, and Reel scripting (4,258 stars, MIT, last push 2026-09-15) | https://github.com/charlie947/social-media-skills |
| 11 | collabs-inc/collab-public | KEEP | Agentic development environment on an infinite canvas (3,075 stars, FSL-1.1-ALv2, GitHub SPDX NOASSERTION, last push 2026-08-08) | https://github.com/collabs-inc/collab-public |
| 12 | ctate/3d-model-generator | KEEP | Software app that generates 3D models through the Hyper3D Rodin API; GitHub license API 404 (233 stars, no license file, last push 2026-02-05) | https://github.com/ctate/3d-model-generator |
| 13 | dagger/container-use | KEEP | Coding-agent isolation environments. Repo pushed_at 2026-09-21T14:05:02Z is Dependabot branch dependabot/go_modules/minor-83ac690e78; default branch main last commit is 2026-08-12, 67 days before this check (4,072 stars, Apache-2.0) | https://github.com/dagger/container-use |
| 14 | danielhanchen/llama.cpp | REJECT | fork with no own commits (ahead 0, behind 2129 at check time) (17 stars, MIT, last push 2026-10-16) | https://github.com/danielhanchen/llama.cpp |
| 15 | dbos-inc/dbos-transact-py | KEEP | Maintained database-backed durable Python workflows (1,637 stars, MIT, last push 2026-10-16) | https://github.com/dbos-inc/dbos-transact-py |

Totals: KEEP 14 / REJECT 1 / NEEDS OWNER 0

## Batch 2 (candidates 16–30)

| # | Candidate | Verdict | Reason | Source |
|---|---|---|---|---|
| 16 | debpalash/VoiceStudio | KEEP | Maintained local voice studio for cloning, design, dubbing, and transcription, already on the speech comparison lane (74,008 stars, AGPL-3.0, last push 2026-10-18) | https://github.com/debpalash/VoiceStudio |
| 17 | DeusData/codebase-memory-mcp | KEEP | Maintained code-intelligence MCP that indexes a repo into a knowledge graph; cited vfmem pattern source (46,802 stars, MIT, last push 2026-10-18) | https://github.com/DeusData/codebase-memory-mcp |
| 18 | Edge0-AI/Audio8_TTS | KEEP | Maintained compact text-to-speech model (1,817 stars, Apache-2.0, last push 2026-09-02) | https://github.com/Edge0-AI/Audio8_TTS |
| 19 | emdgroup/maestro | KEEP | Active task orchestrator for a coding agent of choice (7 stars, Apache-2.0, last push 2026-10-18) | https://github.com/emdgroup/maestro |
| 20 | emilk/egui | KEEP | Maintained immediate-mode Rust GUI for native and web, relevant to Control Center UI (31,555 stars, MIT OR Apache-2.0, last push 2026-10-15) | https://github.com/emilk/egui |
| 21 | etcd-io/etcd | KEEP | Maintained distributed key-value store already used by the Office P0 lease work (52,389 stars, Apache-2.0, last push 2026-10-17) | https://github.com/etcd-io/etcd |
| 22 | fishaudio/fish-speech | KEEP | Maintained open-source TTS under the Fish Audio Community License 1.0 (33,245 stars, GitHub SPDX NOASSERTION, last push 2026-10-14) | https://github.com/fishaudio/fish-speech |
| 23 | FlowiseAI/Flowise | REJECT | GitHub archived visual agent builder (archived=true) (55,511 stars, GitHub SPDX NOASSERTION, last push 2026-08-13) | https://github.com/FlowiseAI/Flowise |
| 24 | gastownhall/gastown | KEEP | Named on the #612 executor comparison list. API pushed_at 2026-10-18T00:11:20Z is correct and is a Dependabot push (PRs 4928 and 4929 opened and closed that minute); default branch main last commit is 2026-07-23 (18,403 stars, MIT) | https://github.com/gastownhall/gastown |
| 25 | generalaction/emdash | KEEP | Maintained open-source agentic IDE for parallel coding agents, named on the #612 comparison list (6,024 stars, Apache-2.0, last push 2026-10-17) | https://github.com/generalaction/emdash |
| 26 | getpaseo/paseo | KEEP | Maintained orchestrator for multiple coding agents from desktop and mobile; LICENSE text is Apache-2.0 (21,245 stars, GitHub SPDX NOASSERTION, last push 2026-10-18) | https://github.com/getpaseo/paseo |
| 27 | ggml-org/llama.cpp | KEEP | Canonical maintained LLM inference engine in C/C++ (131,558 stars, MIT, last push 2026-10-18) | https://github.com/ggml-org/llama.cpp |
| 28 | gmh5225/awesome-skills | KEEP | Maintained curated list of agent skills and tools for Claude Code, Codex, Gemini CLI, and Copilot (94 stars, MIT, last push 2026-10-17) | https://github.com/gmh5225/awesome-skills |
| 29 | Hikhakk/higgsfield-mcp-unified | KEEP | Maintained local-first MCP server for Higgsfield image and video models (97 stars, MIT, last push 2026-10-17) | https://github.com/Hikhakk/higgsfield-mcp-unified |
| 30 | huginn/huginn | KEEP | Maintained self-hosted agents that monitor and act on a user's behalf (50,073 stars, MIT, last push 2026-10-18) | https://github.com/huginn/huginn |

Totals: KEEP 14 / REJECT 1 / NEEDS OWNER 0

## Batch 4 (candidates 46–61)

| # | Candidate | Verdict | Reason | Source |
|---|---|---|---|---|
| 46 | openinterpreter/openinterpreter | KEEP | Registry entry openinterpreter/open-interpreter redirects here; maintained coding agent for open models (68,600 stars, Apache-2.0, last push 2026-10-11) | https://github.com/openinterpreter/openinterpreter |
| 47 | raine/workmux | KEEP | Maintained git-worktree and tmux tool for parallel development (2,893 stars, MIT, last push 2026-10-17) | https://github.com/raine/workmux |
| 48 | restatedev/restate | KEEP | Maintained durable-execution platform under BUSL-1.1; #612 names it as the durable-engine role (4,569 stars, GitHub SPDX NOASSERTION, last push 2026-10-18) | https://github.com/restatedev/restate |
| 49 | SaladDay/cc-switch-cli | KEEP | Maintained cross-platform CLI assistant for Claude Code, Codex, and Gemini CLI (5,332 stars, MIT, last push 2026-10-16) | https://github.com/SaladDay/cc-switch-cli |
| 50 | superset-sh/superset | KEEP | Maintained agent workspace for running many CLI coding agents in parallel, under Elastic License 2.0 (15,330 stars, GitHub SPDX NOASSERTION, last push 2026-10-18) | https://github.com/superset-sh/superset |
| 51 | tashfeenahmed/freellmapi | KEEP | Maintained OpenAI-compatible router over free LLM providers; the repo description states personal experimentation only (36,787 stars, MIT, last push 2026-10-18) | https://github.com/tashfeenahmed/freellmapi |
| 52 | Tejashmakwana/motionmaxxing | KEEP | Maintained agent skill that turns video into motion-design-style films (853 stars, Apache-2.0, last push 2026-10-06) | https://github.com/Tejashmakwana/motionmaxxing |
| 53 | temporalio/cli | KEEP | Maintained CLI for Temporal Server, workflows, and activities (388 stars, MIT, last push 2026-10-17) | https://github.com/temporalio/cli |
| 54 | temporalio/temporal | KEEP | Maintained durable workflow service, a comparison candidate beside Restate (23,791 stars, MIT, last push 2026-10-18) | https://github.com/temporalio/temporal |
| 55 | TencentCloud/octop-memory | KEEP | Maintained agent memory for preferences and cross-session context (71 stars, MIT, last push 2026-10-16) | https://github.com/TencentCloud/octop-memory |
| 56 | tester-army/e2e | KEEP | Maintained end-to-end testing framework for web and mobile apps (11,118 stars, Apache-2.0, last push 2026-10-17) | https://github.com/tester-army/e2e |
| 57 | tigerless-labs/autoharness | KEEP | Maintained self-learning skill layer that distills Claude Code sessions into skills (11,135 stars, MIT, last push 2026-10-15) | https://github.com/tigerless-labs/autoharness |
| 58 | tinhtran24/maestro | KEEP | Open-source Go multi-agent coding workbench, a separate repo from emdgroup/maestro (6 stars, Apache-2.0, last push 2026-07-24) | https://github.com/tinhtran24/maestro |
| 59 | tmchow/illo-skill | KEEP | Maintained agent skill for print-style editorial illustrations (406 stars, MIT, last push 2026-09-21) | https://github.com/tmchow/illo-skill |
| 60 | wheresryan22/anatomy | KEEP | Maintained agent skill for isometric illustrations of machines and systems; already receipted as O-VIS-01 (15,494 stars, MIT, last push 2026-10-15) | https://github.com/wheresryan22/anatomy |
| 61 | yetone/magpie | KEEP | Maintained menu-bar model router across coding agents (15,435 stars, MIT, last push 2026-10-18) | https://github.com/yetone/magpie |

Totals: KEEP 16 / REJECT 0 / NEEDS OWNER 0

## Counts

46 rows. KEEP 44 / REJECT 2 / NEEDS OWNER 0. Same totals as the source comments.
