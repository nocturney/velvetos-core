# Office 2.0 standalone candidate tests — 2026-10-19

CLAIM: [#612 comment](https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6261436200).

Source: [#595](https://github.com/nocturney/velvetos-core/issues/595) and the tool notes linked from it.

- Perplexity 10-tool scan, auditor comment [6249011608](https://github.com/nocturney/velvetos-core/issues/595#issuecomment-6249011608), repo copy `docs/implementation/office-v2/phase2/perplexity-10-tool-verification-2026-10-18.md`.
- Auditor smoke receipt [6250342488](https://github.com/nocturney/velvetos-core/issues/595#issuecomment-6250342488).
- ChatGPT-061 memory and CLI note [6250538600](https://github.com/nocturney/velvetos-core/issues/595#issuecomment-6250538600).
- Assurance intake `docs/implementation/office-v2/phase2/owner-assurance-binary-tools-intake-2026-10-14.md`.

This pass installs nothing into the Office console or a dashboard, adds no workflow, and edits no candidate registry. `security_admission` stays **RED**.

License policy is [#632](https://github.com/nocturney/velvetos-core/pull/632) / `packages/vlicense/GATE.md`. These rows are software. A license is recorded and does not block the smoke. The Israeli-creator stop applies to 3D-print models. SPDX values below are `GET /repos/{owner}/{repo}` at 2026-10-19T06:50Z unless a cell says the license file was read.

## Overlap

**CortexDesk** does not appear in the 62 comments on #595 or in the linked tool notes above. ChatGPT is testing that candidate in parallel. This report does not install it and does not score it.

**Spoolman** (`Donkie/Spoolman`, MIT) is frozen. It was not installed. The 2026-10-18 Chris-Mini-PC smoke stays historical.

## What "standalone now" means

A **yes** row can be smoked on this cloud VM with an isolated venv, `node_modules`, or a downloaded binary: no paid API, no account, no secret, and no listener left on the host. A **spare** row needs a GUI, macOS, Windows, Docker, or an already-running Ollama at `127.0.0.1:11434`. Those steps are written below and were not run. Hosts **Chris** and **Chris-3DPC** are out of every step.

## Candidate table

| Candidate | What it is | License | Standalone now | Minimal plan |
|---|---|---|---|---|
| CrewAI `crewAIInc/crewAI` | Python multi-agent framework | MIT | Import yes. A completion needs local Ollama | venv, `crewai==1.15.28`, import only here. Completion steps are for MacMiniOffice2 |
| AutoGen `microsoft/autogen` | Agentic programming framework. README points new work at Microsoft Agent Framework. GitHub `archived` is false | Docs `LICENSE` CC-BY-4.0. Code `LICENSE-CODE` MIT (file re-read) | Import of `autogen-core` yes. Studio is a server | venv, `autogen-core==0.7.5`, print version. Do not start AutoGen Studio |
| LangGraph `langchain-ai/langgraph` | Graph runtime for agents | MIT | Yes, pure function graph | venv, `langgraph==1.2.16` and `langgraph-checkpoint==4.3.0`, compile a one-node graph |
| Archon `coleam00/Archon` | AI coding harness with a local server | MIT | Spare. Windows `install.ps1` or a server | Chris-Mini-PC. Loopback only, then stop. See spare steps |
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
| Goose `aaif-goose/goose` | Extensible local agent CLI | Apache-2.0 | Version yes. A reply needs Ollama | Linux `--version` here. `goose run` steps are for MacMiniOffice |
| OpenCode `anomalyco/opencode` | Coding-agent CLI and desktop app | MIT | Version yes. `run` can open a local server and needs a model | Linux `--version` here. `run` steps are for MacMiniOffice |
| iFixAi `ifixai-ai/iFixAi` | Agent assurance CLI | Apache-2.0 | `--version` yes. `ifixai run` asks for a provider | venv, `ifixai==4.2.0`, `--version` inside a network namespace |
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

## Cloud VM run

Host: Linux x86_64, Python 3.12.3, `node` on `PATH` at the start was v22.14.0. Docker was absent. Work stayed under `/tmp/office2-smoke`. Venvs and binaries were not copied into the repo. Provider keys were unset in every smoke process. `HOME`, `XDG_*`, and `CREWAI_STORAGE_DIR` pointed at that temp tree.

Python smokes loaded `sitecustomize.py` that logged DNS and `connect`, and raised on any TCP target other than `127.0.0.1`, `::1`, or `localhost`. CLI smokes ran inside `unshare --net --map-root-user`. Host `netstat -lntu` after the run matched the listeners that were already there (ports 50052, 26058, 26500, 2375, 5901, 26054, 26053). No `temporal`, `goose`, `opencode`, `promptfoo`, or `uvicorn` process remained.

| Candidate | Version observed | Command | Result |
|---|---|---|---|
| LangGraph | langgraph 1.2.16, langgraph-checkpoint 4.3.0. pip also installed langgraph-sdk 0.4.8 | `pip install --no-cache-dir 'langgraph==1.2.16' 'langgraph-checkpoint==4.3.0'` then a `StateGraph` that adds 1 | **PASS.** `invoke({"n": 41})` returned `42`. Net log empty. The first print used `langgraph.__version__` and raised `AttributeError` after the assert. The rerun read the version from `importlib.metadata` and printed `result 42` |
| CrewAI | 1.15.28 | `pip install --no-cache-dir 'crewai==1.15.28'` then `import crewai` with telemetry env below | **PASS** for import. Net log empty. `chromadb` was imported. `mcp`, `uvicorn`, and `fastapi` were not. No `kickoff` |
| AutoGen | autogen-core 0.7.5 | `pip install --no-cache-dir 'autogen-core==0.7.5'` then `import autogen_core` | **PASS.** Net log empty. Studio was not started |
| DBOS | 3.3.0 | `pip install --no-cache-dir 'dbos==3.3.0'` then a SQLite workflow | **PASS.** Workflow returned `pong`. Log line named `https://console.dbos.dev/self-host?appname=office2-smoke` and opened no socket. `DBOS.destroy()` ran. Net log empty |
| Pydantic AI | 2.57.0 | `pip install --no-cache-dir 'pydantic-ai==2.57.0'` then `Agent(model=TestModel()).run_sync("ping")` | **PASS.** Output `success (no tool calls)`. A startup banner printed a Logfire URL. Net log empty |
| LiteLLM | 1.88.6 (PyPI latest at the same time was 1.106.0 and was not installed) | `LITELLM_LOCAL_MODEL_COST_MAP=True` then `completion(..., mock_response="pong")` | **PASS.** Content `pong`. Net log empty |
| Agent Framework | agent-framework-core 1.22.0 | `pip install --no-cache-dir 'agent-framework-core==1.22.0'` then Upper then Reverse on `"velvet"` | **PASS.** Outputs `['TEVLEV']`. Net log empty |
| iFixAi | 4.2.0 | `pip install --no-cache-dir ifixai` (resolved 4.2.0) then `ifixai --version` inside the netns | **PASS** for version. `ifixai run` was not used |
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

`scripts/office2/run_standalone_smokes.py` is the pin list and the connect guard. `python3 scripts/check-all.py` does not execute it. Running it with no flag exits 2 and installs nothing.

## Spare-machine steps (not run)

Do these on one machine at a time. Scratch directory only. Unset `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_API_KEY`, and `LANGSMITH_API_KEY` before the process starts. After each server test, stop the process and confirm its port is gone. Never use Chris or Chris-3DPC.

### MacMiniOffice2 — local Ollama completions

Preflight, every tool in this section:

```bash
curl -sS --max-time 3 http://127.0.0.1:11434/api/version
```

Expected: a small JSON version object. Connection refused, a bind on `0.0.0.0`, or port `11435`: **STOP**. Do not start Ollama. Do not pull a model. Do not download weights.

CrewAI, scratch `~/Velvet/candidates/20261019/crewai`:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --no-cache-dir 'crewai==1.15.28'
export CREWAI_DISABLE_TELEMETRY=true OTEL_SDK_DISABLED=true CREWAI_TRACING_ENABLED=false
export ANONYMIZED_TELEMETRY=False HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export CREWAI_STORAGE_DIR="$PWD/storage" HOME="$PWD/home"
mkdir -p "$CREWAI_STORAGE_DIR" "$HOME"
python - << 'PY'
from crewai import Agent, Crew, LLM, Task
llm = LLM(
    model="qwen3.5:9b",
    base_url="http://127.0.0.1:11434/v1",
    api_key="local",
    custom_openai=True,
)
agent = Agent(role="Triage", goal="Reply with the single word pong", backstory="local", llm=llm, tools=[], memory=False)
task = Task(description="Reply with the single word pong", expected_output="pong", agent=agent)
crew = Crew(agents=[agent], tasks=[task], memory=False)
print(crew.kickoff())
PY
```

Expected: the text `pong`, and no TCP connection except `127.0.0.1:11434`. If `qwen3.5:9b` is not already loaded, **STOP**. Do not add `crewai-tools`.

Mem0, Graphiti, Hindsight, and Letta Code use the same preflight and the same scratch parent. One venv each. Point only at `http://127.0.0.1:11434`. If the tool asks for Neo4j, a hosted embedder, or an API key, **STOP** and record `BLOCKED_LOCAL_DEPENDENCY`. Stop any process the tool spawned before leaving the machine.

### MacMiniOffice — Goose, OpenCode, Ghidra

Goose, empty directory `~/Velvet/candidates/20261019/goose`. Same Ollama preflight. Binary from the v1.55.0 Linux or macOS asset that matches the machine, or the copy already used for `--version` if this is a repeat on Linux.

```bash
export GOOSE_TELEMETRY_OFF=true GOOSE_TELEMETRY_ENABLED=false
export OLLAMA_HOST=http://127.0.0.1:11434
goose run --no-session --provider ollama --model qwen3.5:9b -t "Reply with the single word pong"
```

Expected: `pong` on stdout. Working directory stays the empty scratch dir. Do not pass a recipe from GitHub.

OpenCode, empty directory `~/Velvet/candidates/20261019/opencode`. Same Ollama preflight. v1.19.3 asset for that OS.

```bash
opencode run --pure --dir "$PWD" -m "ollama/qwen3.5:9b" "Reply with the single word pong"
```

Expected: `pong`. Do not pass `--auto`, `--mdns`, or a hostname other than `127.0.0.1`. After it exits, confirm nothing is still listening. If `run` opens a local server, stop that process before leaving.

Ghidra: this cloud VM is OpenJDK 21.0.10. The 2026-10-14 intake names Ghidra 12.1.4 and JDK 25. On MacMiniOffice, install a user-local JDK 25, download the official 12.1.4 zip into the scratch dir, compile a local `int main(void){return 0;}` program, and run `support/analyzeHeadless` on that binary only. Quit the GUI if it opens. Expected: a headless log that names the binary and a zero exit. Remove the scratch project after. Do not point it at anyone else's firmware.

### Mac-Bedroom — one Docker stack at a time

No Docker was present on the cloud VM, so these were not started. On Mac-Bedroom, `docker version` must succeed. Publish `127.0.0.1` only. One stack, then `docker compose down` and a port check, before the next.

- n8n current image, port `127.0.0.1:5678`. Expected: local HTTP responds, then the port is gone.
- Activepieces with its documented Postgres and Redis, loopback ports only. Expected: local HTTP responds, then the ports are gone.
- Windmill community image, loopback only. Expected: local HTTP responds, then the port is gone.
- OpenHands with Docker, loopback only. Expected: local HTTP responds, then the container is gone.
- Supermemory, herdr, and Icepick only if their README smoke is loopback and needs no token. Otherwise **STOP**.

### Chris-Mini-PC — Windows, then stop

Archon: scratch `D:\Velvet\candidates\20261019\Archon`. Follow upstream `install.ps1` only inside that directory. If the server starts, the bind is `127.0.0.1`. Request one local health URL. Stop the process. `netstat` must not show the Archon port. A bind on `0.0.0.0` is a failed test: stop it immediately. CVE-2026-111322 covered 0.2.13–0.11.1; v0.12.1 was outside that range on 2026-10-18. That history is why the bind stays loopback.

UFO: **STOP.** `security_admission` stays RED. The 2026-10-18 advisory read found 18 published advisories and no patched version on any of them. Do not `pip install`, do not start Galaxy, MCP, or a WebSocket server, and do not drive the desktop.

PentAGI: **STOP.** Do not clone it onto a spare machine in this test. A scanner, a host Docker socket, and an exposed callback are outside this smoke.

## Result line

Cloud smokes that ran: LangGraph, CrewAI import, AutoGen core import, DBOS SQLite, Pydantic AI `TestModel`, LiteLLM mock, Agent Framework workflow, iFixAi version, Promptfoo echo on Node 22.23.3, Goose version, OpenCode version, Temporal version, and Temporal `start-dev` inside a network namespace. Promptfoo on Node v22.14.0 failed its own runtime check. Spoolman was skipped. CortexDesk was left to the parallel ChatGPT pass. UFO and PentAGI stay unrun with `security_admission` RED.
