# Office 2.0 standalone depth — 2026-10-19

CLAIM: [#612 depth comment](https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6261903370). The first smoke claim is [#612 comment](https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6261436200).

Source: the PASS rows in [standalone-candidate-tests-2026-10-19.md](standalone-candidate-tests-2026-10-19.md). That record stays the import and version smoke. This file is one offline scenario further, still with no console, dashboard, registry, or workflow edit. `security_admission` stays **RED**.

## Skipped

**UFO** (`microsoft/UFO`) is a Windows GUI computer-use agent. The 2026-10-18 advisory read found 18 published advisories and no patched version. It was not installed. `security_admission` stays RED.

**PentAGI** (`vxcontrol/pentagi`) is autonomous offensive tooling. It was not cloned and not started. A scanner, a host Docker socket, and an exposed callback are outside this smoke.

Spoolman stays frozen. CortexDesk stays with the parallel ChatGPT pass.

## How this was run

Host: Linux x86_64, Python 3.12.3. Fresh venvs under `/tmp/office2-depth/venvs`. The earlier `/tmp/office2-smoke` venvs were not modified. Temporal CLI is the same binary as the first smoke, `/tmp/office2-smoke/bin/temporal` v1.9.1 (embedded server string `Server 1.32.0, UI 2.54.1`).

Each scenario ran inside `unshare --net --map-root-user`. A `sitecustomize` hook refused any TCP connect whose host was not `127.0.0.1`, `::1`, or `localhost`, and appended every connect to a net log. Loopback inside the namespace was brought up with `ioctl` `SIOCSIFFLAGS` because `ip` is not installed. Provider key, token, secret, and password variables were stripped from the child environment. `LITELLM_LOCAL_MODEL_COST_MAP=True` was set before LiteLLM import.

Command:

```bash
OFFICE2_STANDALONE_DEPTH=1 python3 scripts/office2/run_standalone_depth.py --execute
```

Without that variable and `--execute`, the script prints the pins and exits 2. `check-all` does not run it. The recorded run printed `DEPTH PASS [0, 0, 0, 0, 0]`. Host `netstat` listeners after the run were the same set as before it (50052, 26058, 26500, 2375, 5901, 26054, 26053). No `temporal server`, DBOS, or worker process remained.

Pins installed for this pass: `langgraph==1.2.16`, `langgraph-checkpoint==4.3.0`, `langgraph-checkpoint-sqlite==3.1.2`, `dbos==3.3.0`, `temporalio==1.32.0`, `pydantic-ai==2.57.0`, `litellm==1.88.6`.

## Results

| Tool | Scenario | Result | Worth integrating? |
|---|---|---|---|
| LangGraph 1.2.16 + checkpoint 4.3.0 + checkpoint-sqlite 3.1.2 | Three-step graph, SQLite checkpoint, interrupt after step 2, resume in a second `with` block on the same file | **PASS.** Paused `{'n': 12, 'trace': ['a', 'b']}` with next `['step3']`. Reopen saw the same next node. Resume returned `{'n': 112, 'trace': ['a', 'b', 'c']}`. Net log empty | Yes, as a later pilot for checkpointed graphs. The sqlite package is a separate pin from the import smoke |
| DBOS 3.3.0 | Two-step workflow on SQLite. `kill -9` after step 2 had started. A new process launched and recovered | **PASS.** Workflow `e34be9aa-b099-467b-8a23-ba44cf36fa35` returned `onetwo`. Marker was `step1`, `step2-start`, `step2-start`, `step2-done`. Status passed through `ENQUEUED` to `SUCCESS`. Net log empty | Yes, as a later pilot for durable steps. SQLite is the dev database; do not treat this as a production recovery proof |
| Temporal CLI 1.9.1 + temporalio 1.32.0 | `start-dev` on 127.0.0.1 only. Three activities. `kill -9` the first worker during activity `two`. A second worker finished the workflow. Then the server was killed | **PASS.** Marker `one`, `two`, `two`, `three`. Client printed `RESULT one\|two\|three`. Server log named UI `http://localhost:8233` and a metrics port. Those ports were inside the namespace. Host `netstat` did not show 7233, 8233, or the metrics port | Only if a loopback dev server is started and torn down in the same run. Not as a standing listener |
| Pydantic AI 2.57.0 | `Agent` with `output_type=OfferCard` on `TestModel` | **PASS.** Seeded args returned `{'sku': 'shelf-1', 'ready': True, 'note': 'pickup'}`. Net log empty | Yes, for typed test doubles. The unseeded result is not a model judgment |
| LiteLLM 1.88.6 | `Router` with `office-primary` aimed at `http://127.0.0.1:9/v1` and `office-backup` using `mock_response`, `fallbacks=[{"office-primary": ["office-backup"]}]`, `num_retries=0` | **PASS.** Content `pong-from-backup`, model `backup-up`. Net log was only `('127.0.0.1', 9)` | Yes, as a later pilot for fallback routing. The response object is a rough witness |

## What was rough

LangGraph resume is an explicit interrupt. `invoke(None, config)` continues the same thread. Nothing here is a timer or a crash of the process that held the sqlite file open. The saver is `langgraph-checkpoint-sqlite` 3.1.2, which was not in the import-only venv.

DBOS re-ran the in-flight step and did not re-run the finished step. The library log says the SQLite system database is for development and testing and that PostgreSQL is recommended for production. With no conductor key it still logs `https://console.dbos.dev/self-host?appname=office2-depth` and opened no socket. `DBOS.destroy()` on the recovery process shut the threads down. The killed process had no chance to shut down.

Temporal sync activities are refused unless an `activity_executor` is passed (`Activity step is not async so an activity_executor must be present`). The passing activity is `async`. Activity `two` ran twice because the killed attempt did not finish; the retry on the second worker did. `temporal server start-dev --log-format plain` exits immediately: the flag accepts `text`, `json`, or `pretty`. The dev server binds a gRPC port, a UI port, and a random metrics port. The Python connect hook saw the driver's own probes to 7233. The gRPC client sockets are not that Python `socket.connect`. The network namespace is what kept them off the host.

Pydantic AI prints a Logfire setup banner on stderr while observability is off. The banner names `https://pydantic.dev/ai-setup.md` and says `PYDANTIC_AI_NO_BANNER=1` hides it. No socket was opened. `TestModel()` with no `custom_output_args` returned `{'sku': 'a', 'ready': False, 'note': 'a'}` for the same prompt. The structured type checked. The values came from the test double, not from the prompt text.

LiteLLM `Router` deepcopy rejects a `litellm.MockException` stored on a deployment (`MockException.__init__() missing 3 required positional arguments`). The passing failure is a refused loopback port, not an in-memory exception. The winning mock response still reports `HIDDEN_API_BASE https://api.openai.com`. That string was not a connect. The local cost map has to be set before import, same as the first smoke.

## Result line

Five offline depth scenarios passed inside a network namespace: LangGraph sqlite interrupt and resume, DBOS recovery after `kill -9`, Temporal worker recovery after `kill -9` with the dev server torn down, Pydantic AI structured output on `TestModel`, and LiteLLM fallback from a dead loopback primary to a mock backup. UFO and PentAGI were not run. `security_admission` stays RED. Nothing was wired into the console or a dashboard.
