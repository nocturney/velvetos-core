# Office 2.0 standalone candidate tests — 2026-10-19

CLAIM: [#612 comment](https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6261436200).

Source: [#595](https://github.com/nocturney/velvetos-core/issues/595) and the tool notes linked from it.

- Perplexity 10-tool scan, auditor comment [6249011608](https://github.com/nocturney/velvetos-core/issues/595#issuecomment-6249011608), repo copy `docs/implementation/office-v2/phase2/perplexity-10-tool-verification-2026-10-18.md`.
- Auditor smoke receipt [6250342488](https://github.com/nocturney/velvetos-core/issues/595#issuecomment-6250342488).
- ChatGPT-061 memory and CLI note [6250538600](https://github.com/nocturney/velvetos-core/issues/595#issuecomment-6250538600).
- Assurance intake `docs/implementation/office-v2/phase2/owner-assurance-binary-tools-intake-2026-10-14.md`.

This pass installs nothing into the Office console or a dashboard, adds no workflow, and edits no candidate registry. `security_admission` stays **RED**.

**Evidence status: AUTHOR_REPORTED_UNVERIFIED.** The cloud-VM results below are what the author reports. No command log, network log, `sitecustomize.py`, or `netstat` capture is committed, and no reviewer has re-run them. Read each **PASS** as "the author reports PASS". This record grants no runtime, install, or admission authority.

License policy is [#632](https://github.com/nocturney/velvetos-core/pull/632) / `packages/vlicense/GATE.md`. These rows are software. A license is recorded and does not block the smoke. The Israeli-creator stop applies to 3D-print models. SPDX values below are `GET /repos/{owner}/{repo}` at 2026-10-19T06:50Z unless a cell says the license file was read.

## Overlap

**CortexDesk** does not appear in the 62 comments on #595 or in the linked tool notes above. ChatGPT is testing that candidate in parallel. This report does not install it and does not score it.

**Spoolman** (`Donkie/Spoolman`, MIT) is frozen. It was not installed. The 2026-10-18 Chris-Mini-PC smoke stays historical.

## What "standalone now" means

A **yes** row can be smoked on this cloud VM with an isolated venv, `node_modules`, or a downloaded binary: no paid API, no account, no secret, and no listener left on the host. A **spare** row needs a GUI, macOS, Windows, Docker, or an already-running Ollama at `127.0.0.1:11434`. Spare rows were not run, and this record gives no steps for them. See [Spare-machine rows](#spare-machine-rows-not-run-not-authorized). Hosts **Chris** and **Chris-3DPC** are out of scope for this record.

## Candidate table

| Candidate | What it is | License | Standalone now | Minimal plan |
|---|---|---|---|---|
| CrewAI `crewAIInc/crewAI` | Python multi-agent framework | MIT | Import yes. A completion needs local Ollama | venv, `crewai==1.15.28`, import only here. No `kickoff` under this record. A kickoff goes only through the [gated CrewAI runbook](../office-v2/pilot-runbook-crewai.md) |
| AutoGen `microsoft/autogen` | Agentic programming framework. README points new work at Microsoft Agent Framework. GitHub `archived` is false | Docs `LICENSE` CC-BY-4.0. Code `LICENSE-CODE` MIT (file re-read) | Import of `autogen-core` yes. Studio is a server | venv, `autogen-core==0.7.5`, print version. Do not start AutoGen Studio |
| LangGraph `langchain-ai/langgraph` | Graph runtime for agents | MIT | Yes, pure function graph | venv, `langgraph==1.2.16` and `langgraph-checkpoint==4.3.0`, compile a one-node graph |
| Archon `coleam00/Archon` | AI coding harness with a local server | MIT | Spare. Windows `install.ps1` or a server | Not run. Needs its own reviewed runbook |
| UFO `microsoft/UFO` | Windows computer-use agent | MIT | Spare, and blocked | Chris-Mini-PC stops before install. `security_admission` stays RED. 18 advisories on 2026-10-18 had no patched version |
| OpenHands `OpenHands/OpenHands` | Software-agent runtime | MIT | Spare. Docker | Mac-Bedroom, one container, loopback, then remove |
| n8n `n8n-io/n8n` | Workflow automation | Sustainable Use License (`LICENSE.md` re-read). `.ee.` files need an enterprise licence. SPDX `NOASSERTION` | Spare. Docker for current installs | Mac-Bedroom, loopback, then remove |
| Activepieces `activepieces/activepieces` | Workflow automation | MIT Expat outside `packages/ee/` (`LICENSE` re-read). Enterprise licence inside that tree. SPDX `NOASSERTION` | Spare. Docker Compose, Postgres, Redis | Mac-Bedroom, loopback, then remove |
| Windmill `windmill-labs/windmill` | Workflow and UI platform | AGPLv3 by default; Apache-2.0 and proprietary enterprise snippets (`LICENSE` re-read). Community Edition images: free use, no sell, resell, managed service, modify, or wrap | Spare. Docker, or an enterprise Windows worker | Mac-Bedroom community image, loopback, then remove |
| Temporal `temporalio/temporal` | Durable execution server. CLI is `temporalio/cli` | MIT | CLI version and a netns dev server yes | Binary `temporal` v1.9.1. `start-dev` only inside a network namespace, then kill it |
| Microsoft Agent Framework `microsoft/agent-framework` | Successor runtime named by the AutoGen README | MIT | Yes, in-process workflow | venv, `agent-framework-core==1.22.0`, two pure executors |
| Promptfoo `promptfoo/promptfoo` | Prompt and agent eval CLI | MIT | Yes, echo provider, with Node >= 22.22 | `promptfoo@0.124.1`, echo config, run inside a network namespace |
| Pydantic AI `pydantic/pydantic-ai` | Typed Python agent framework | MIT | Yes, `TestModel` | venv, `pydantic-ai==2.57.0`, one `run_sync` |
| LiteLLM `BerriAI/litellm` | Multi-provider LLM client | MIT outside `enterprise/` (`LICENSE` re-read). SPDX `NOASSERTION` | Yes, `mock_response` | venv, `litellm==1.88.6`, `LITELLM_LOCAL_MODEL_COST_MAP=True` before import |
| DBOS `dbos-inc/dbos-transact-py` | Durable Python workflows | MIT | Yes, SQLite system database | venv, `dbos==3.3.0`, one workflow, `DBOS.destroy()` |
| Spoolman `Donkie/Spoolman` | Filament inventory server | MIT | Frozen. Skip | No install |
| Hindsight `vectorize-io/hindsight` | Agent memory service | MIT | Spare. Ollama plus its own process | MacMiniOffice2 only if `127.0.0.1:11434` is already up. Stop the process after |
| Graphiti `getzep/graphiti` | Temporal knowledge graph | Apache-2.0 | Spare. Ollama-compatible clients, usually a graph database | MacMiniOffice2 scratch venv. Stop if it wants Neo4j or a paid key |
| Mem0 `mem0ai/mem0` | Agent memory library | Apache-2.0 | Spare. Documented Ollama LLM and embedder | MacMiniOffice2. Both models must already be on `127.0.0.1:11434`. Do not pull weights |
| Supermemory `supermemoryai/supermemory` | Self-hosted memory app | MIT | Spare. Server | Mac-Bedroom loopback, then stop |
| Letta Code `letta-ai/letta-code` | Coding agent with memory | Apache-2.0 | Spare. Ollama for the LLM path | MacMiniOffice2. Stop if embeddings are not already local |
| Goose `aaif-goose/goose` | Extensible local agent CLI | Apache-2.0 | Version yes. A reply needs Ollama | Linux `--version` here. No `goose run` under this record |
| OpenCode `anomalyco/opencode` | Coding-agent CLI and desktop app | MIT | Version yes. `run` can open a local server and needs a model | Linux `--version` here. No `opencode run` under this record |
| iFixAi `ifixai-ai/iFixAi` | Agent assurance CLI | Apache-2.0 | `--version` yes. `ifixai run` asks for a provider | venv, `ifixai==4.2.0` pinned on any rerun, `--version` inside a network namespace |
| PentAGI `vxcontrol/pentagi` | Autonomous penetration-testing system | MIT, with upstream EULA and service terms called out in the 2026-10-14 intake | No | Do not install. `security_admission` stays RED. No scanner, no Docker socket |
| Ghidra `NationalSecurityAgency/ghidra` | Reverse-engineering toolkit | Apache-2.0 | Spare. JDK 25. This VM has OpenJDK 21 | MacMiniOffice headless hello-world, then quit |
| OpenPost `getopenpost/openpost` | Social post scheduler. Provenance row in comment 6250538600 | AGPL-3.0 | Spare | Not smoked. A scratch clone on Mac-Bedroom may read the README. Stop before any account or post |
| SkillOpt `microsoft/SkillOpt` | Text skill optimizer. Provenance row | MIT | Spare | Not smoked. Scratch venv on MacMiniOffice2. Stop if it calls a paid model |
| NVIDIA SkillEvaluator `NVIDIA/SkillEvaluator` | Agent-skill evaluator. Provenance row | Apache-2.0 | Spare | Not smoked. Same stop as SkillOpt |
| OpenDots aliases | Three different repos in the same comment: `CopilotKit/OpenDots` (MIT), `Anil-matcha/open-dots` (SPDX null), `diggerhq/opendots` (MIT) | See cell | Spare | Not smoked. Do not treat the three repos as one product |
| Laya `NandhaKishorM/laya` | Local decision engine. Provenance row | Apache-2.0 | Spare | Not smoked. Scratch run on MacMiniOffice2 only if the README smoke needs no download and no account |
| Reef | `mousberg/reef` (SPDX null) and `Coral-Protocol/Reef` (SPDX null, empty description) | Unknown | Spare | Not smoked. Identity is still ambiguous |
| Carbon | No source URL in comment 6250538600 | Unknown | No | Do not install |
| Deja Vu | `vshulcz/deja-vu` (MIT, local Go binary) and `focaxisdev/deja-vu` (MIT, Markdown memory) | MIT | Spare | Not smoked. They are different products. A later scratch `--version` on MacMiniOffice is enough |
| herdr `herdrdev/herdr` | Agent terminal multiplexer. Provenance row | Apache-2.0 | Spare. Likely a server | Not smoked. Mac-Bedroom, loopback, then stop |
| useAgent `useagenthq/useagent` | Self-hosted agent control plane. Provenance row | AGPL-3.0 | Spare | Not smoked. Do not point it at a cloud workspace |
| PI-Desktop `vastsa/PI-Desktop` | Local desktop agent. Provenance row | LGPL-3.0 | Spare. GUI | Not smoked. MacMiniOffice only, scratch profile, then quit |
| Icepick `hatchet-dev/icepick` | TypeScript durable-agent library. Provenance row | MIT | Spare | Not smoked. Scratch `npm` install on Mac-Bedroom with an exact pin, no Hatchet cloud token |
| AYON | `ynput/ayon-core` Apache-2.0 and `ynput/ayon-backend` SPDX `NOASSERTION` | Split | Spare | Not smoked. Pipeline server. Do not start it on a DCC machine |

## Cloud VM run (author-reported)

Everything in this section is author-reported. None of it was re-run for review.

Host: Linux x86_64, Python 3.12.3, `node` on `PATH` at the start was v22.14.0. Docker was absent. Work stayed under `/tmp/office2-smoke`. Venvs and binaries were not copied into the repo. Provider keys were unset in every smoke process. `HOME`, `XDG_*`, and `CREWAI_STORAGE_DIR` pointed at that temp tree.

Python smokes loaded a `sitecustomize.py` that replaced `socket.socket.connect` in the Python process. It logged DNS and `connect` calls and raised on a TCP target other than `127.0.0.1`, `::1`, or `localhost`. That file is not committed.

What the guard shows: no Python-level `socket.socket.connect` to a non-loopback address was logged. It does **not** prove egress denial. It is a userland patch in one interpreter. It does not cover `connect_ex`, UDP `sendto`, DNS resolution itself, C extensions or native libraries that open sockets without Python's `socket` module, subprocesses, or code that saved the original `connect` before the patch. It also allows the name `localhost` without checking what that name resolves to. "Net log empty" in the table means only that this log was empty.

CLI smokes ran inside `unshare --net --map-root-user`. A fresh network namespace has no route out, so that is kernel-level isolation for those processes. Python smokes did not run in a namespace. Host `netstat -lntu` after the run matched the listeners that were already there (ports 50052, 26058, 26500, 2375, 5901, 26054, 26053). No `temporal`, `goose`, `opencode`, `promptfoo`, or `uvicorn` process remained.

Installs used direct version pins with no transitive lock or hash check. The iFixAi install was unpinned (see its row). A rerun must pin every direct dependency and is still not a hash-locked install.

| Candidate | Version observed | Command | Result |
|---|---|---|---|
| LangGraph | langgraph 1.2.16, langgraph-checkpoint 4.3.0. pip also installed langgraph-sdk 0.4.8 | `pip install --no-cache-dir 'langgraph==1.2.16' 'langgraph-checkpoint==4.3.0'` then a `StateGraph` that adds 1 | **PASS.** `invoke({"n": 41})` returned `42`. Net log empty. The first print used `langgraph.__version__` and raised `AttributeError` after the assert. The rerun read the version from `importlib.metadata` and printed `result 42` |
| CrewAI | 1.15.28 | `pip install --no-cache-dir 'crewai==1.15.28'` then `import crewai` with telemetry env below | **PASS** for import. Net log empty. `chromadb` was imported. `mcp`, `uvicorn`, and `fastapi` were not. No `kickoff` |
| AutoGen | autogen-core 0.7.5 | `pip install --no-cache-dir 'autogen-core==0.7.5'` then `import autogen_core` | **PASS.** Net log empty. Studio was not started |
| DBOS | 3.3.0 | `pip install --no-cache-dir 'dbos==3.3.0'` then a SQLite workflow | **PASS.** Workflow returned `pong`. Log line named `https://console.dbos.dev/self-host?appname=office2-smoke` and opened no socket. `DBOS.destroy()` ran. Net log empty |
| Pydantic AI | 2.57.0 | `pip install --no-cache-dir 'pydantic-ai==2.57.0'` then `Agent(model=TestModel()).run_sync("ping")` | **PASS.** Output `success (no tool calls)`. A startup banner printed a Logfire URL. Net log empty |
| LiteLLM | 1.88.6 (PyPI latest at the same time was 1.106.0 and was not installed) | `LITELLM_LOCAL_MODEL_COST_MAP=True` then `completion(..., mock_response="pong")` | **PASS.** Content `pong`. Net log empty |
| Agent Framework | agent-framework-core 1.22.0 | `pip install --no-cache-dir 'agent-framework-core==1.22.0'` then Upper then Reverse on `"velvet"` | **PASS.** Outputs `['TEVLEV']`. Net log empty |
| iFixAi | 4.2.0 | `pip install --no-cache-dir ifixai` (unpinned; resolved 4.2.0) then `ifixai --version` inside the netns | **PASS** for version. The install was not pinned, so this row does not reproduce. A rerun uses `ifixai==4.2.0`. `ifixai run` was not used |
| Promptfoo | 0.124.1 | `npm install --no-fund --no-audit promptfoo@0.124.1` then `promptfoo eval` on the echo config inside the netns | **PASS** on Node v22.23.3: `1 passed (100%)`, 0 failed, 0 errors, duration 0s. **FAIL** on the PATH Node v22.14.0: `promptfoo requires a supported Node.js runtime. Detected: v22.14.0. Required: >=22.22.0`. The passing eval did not leave a listener. `promptfoo view` was not started |
| Goose | 1.55.0 | Release asset `goose-x86_64-unknown-linux-gnu.tar.gz` from tag v1.55.0, then `goose --version` inside the netns with `GOOSE_TELEMETRY_OFF=true` | **PASS.** Printed `1.55.0`. `goose run` was not used |
| OpenCode | 1.19.3 | Release asset `opencode-linux-x64.tar.gz` from tag v1.19.3, then `opencode --version` inside the netns | **PASS.** Printed `1.19.3`. `opencode run`, `serve`, and `web` were not used |
| Temporal CLI | CLI 1.9.1, embedded server string `Server 1.32.0, UI 2.54.1` | `temporal_cli_1.9.1_linux_amd64.tar.gz` then `temporal --version` inside the netns | **PASS.** `start-dev` was then run inside a fresh netns whose loopback was brought up with an `ioctl` (`ip` is not installed). It printed `Temporal Server: localhost:7233` and `Temporal UI: http://localhost:8233`. `timeout` killed that namespace (exit 124). Host `netstat` had no 7233, 8233, or 41419, and no `temporal` process remained |

CrewAI import environment: `CREWAI_DISABLE_TELEMETRY=true`, `OTEL_SDK_DISABLED=true`, `CREWAI_TRACING_ENABLED=false`, `ANONYMIZED_TELEMETRY=False`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `DO_NOT_TRACK=1`, `LITELLM_LOCAL_MODEL_COST_MAP=True`.

Promptfoo config (`/tmp/office2-smoke/promptfoo/promptfooconfig.yaml`):

```yaml
description: office2 echo smoke
providers:
  - echo
prompts:
  - "Hello {{name}}"
tests:
  - vars:
      name: office2
    assert:
      - type: contains
        value: office2
```

Eval environment: `CI=1`, `PROMPTFOO_DISABLE_TELEMETRY=1`, `PROMPTFOO_DISABLE_UPDATE=1`, `PROMPTFOO_DISABLE_SHARING=1`, `PROMPTFOO_DISABLE_REMOTE_GENERATION=1`.

DBOS config: `system_database_url=sqlite:////tmp/office2-smoke/work/dbos.sqlite`, `enable_otlp=False`. No Conductor key.

`scripts/office2/run_standalone_smokes.py` is report only. It prints the pin list, the path of this record, `smokes run by this helper: 0`, and the author-reported status. `--json` prints the same report as JSON. `--execute` is always refused with exit 2. No flag or environment variable makes it install, start, or check anything. `python3 scripts/check-all.py` does not execute it. Offline checks: `python3 scripts/office2/test_run_standalone_smokes.py`.

## Spare-machine rows (not run, not authorized)

This record has no executable steps for spare machines. Nothing below is a GO. Each row needs its own reviewed runbook, an owner GO, and the admission, security, and cost gates before anything is installed or started.

- **CrewAI completion (`kickoff`).** The only reviewed path is the gated runbook: [pilot-runbook-crewai.md](../office-v2/pilot-runbook-crewai.md), with the attended checklist [crewai-pilot-attended-run.md](../office-v2/crewai-pilot-attended-run.md) and the [E5 network contract](../office-v2/pilot-e5-network-evidence.md). That path requires every E1-E7 gate to be PASS, a hash-locked offline wheel set, an empty tool list, `memory=False`, and the merged reviewed runner. It is scoped to its named host. Nothing in this record widens that scope to another machine. No ad hoc package install, no inline script, and no placeholder API key.
- **Mem0, Graphiti, Hindsight, Letta Code.** Not run. They need a local model, and some need a graph database or an embedder. No reviewed runbook.
- **Goose `run`, OpenCode `run`.** Not run. Only `--version` was smoked. A model call needs a reviewed runbook.
- **Ghidra.** Not run. Needs JDK 25 and a pinned, checksum-verified download under a reviewed runbook.
- **n8n, Activepieces, Windmill, OpenHands, Supermemory, herdr, Icepick.** Not run. Docker or a server. A runbook must pin image digests or exact package versions, publish loopback only, and use no account or token.
- **Archon.** Not run. The upstream `install.ps1` is an unpinned remote installer and is not a reviewed step. CVE-2026-111322 covered 0.2.13–0.11.1; v0.12.1 was outside that range on 2026-10-18.
- **Provenance-only rows** (OpenPost, SkillOpt, NVIDIA SkillEvaluator, OpenDots, Laya, Reef, Deja Vu, useAgent, PI-Desktop, AYON). Not run. Identity checks stay in the provenance map.
- **UFO: STOP.** `security_admission` stays RED. The 2026-10-18 advisory read found 18 published advisories and no patched version.
- **PentAGI: STOP.** `security_admission` stays RED. Do not clone it.
- **Carbon: STOP.** No source URL.

## Result line

Status: AUTHOR_REPORTED_UNVERIFIED. Cloud smokes the author reports as run: LangGraph, CrewAI import, AutoGen core import, DBOS SQLite, Pydantic AI `TestModel`, LiteLLM mock, Agent Framework workflow, iFixAi version, Promptfoo echo on Node 22.23.3, Goose version, OpenCode version, Temporal version, and Temporal `start-dev` inside a network namespace. Promptfoo on Node v22.14.0 failed its own runtime check. Spoolman was skipped. CortexDesk was left to the parallel ChatGPT pass. UFO and PentAGI stay unrun with `security_admission` RED. No spare-machine row was run, and none is authorized here. The Python network guard was an in-process log and refusal, not proof of egress denial.
