# CrewAI pilot dependency findings (2026-10-18)

Status of the reviewed runner in `scripts/office_v2_crewai/`: the committed
tree still refuses before any model call. No package was installed from this
change. No model call was made. E6 stays `NOT_VERIFIED` because the public
repo has 12 open issues, and the runbook minimum is 20.

E3 is no longer an unconditional fail. Christian accepted the RED lock at
2026-10-18 16:02 Asia/Jerusalem (issue 612 comment 6250234075), on the basis
of comment 6250224612. The decision is
`scripts/office_v2_crewai/evidence/e3-security-decision.json` and it matches
lock sha256 `121c1bd04eee730b51eb71e49da503b0d0236cdd06d8687a5df792234f78a669`.
Preflight passes E3 only when that file is present and every condition below
is enforced. E1, E2, E5, E6 and E7 still refuse this tree, and E4 is
NOT_OBSERVED, so this tree does not start a pilot.

## E4 sandbox and the 11435 client

Comment 6250312836 (CLQ-16) verified that `import crewai` creates
`<LocalAppData>\\CrewAI\\<name>` through appdirs 1.4.4 `SHGetFolderPathW`.
Setting LOCALAPPDATA does not move that write. `Crew()` then writes
`latest_kickoff_task_outputs.db` there and a lock file under TEMP.
`CREWAI_STORAGE_DIR` must be the absolute path
`D:\\Velvet\\Pilots\\crewai-e4\\sandbox-home\\crewai-storage`. The runner
sets that variable, TEMP, TMP, and the other CLQ-16 paths before import.
A missing value or a path that is not on D: is refused.

LAB-2 (issue 595 comment 6250622621) showed a second write:
`%LOCALAPPDATA%\\CrewAI\\credentials\\secret.key`, from
`token_manager.py`, even with tracing off and `CREWAI_STORAGE_DIR` set.
That path reads `LOCALAPPDATA`, so the runner also sets `LOCALAPPDATA`
and `APPDATA` to sandbox paths. The E4 manifest lists
`AppData\\Local\\CrewAI\\credentials`. A missing row is refused.

The committed before/after manifest, HKCU export diff, no-pilot control
run, and positive db/lock check are NOT_OBSERVED. Nothing was run on Chris.

Comment 6250397852 (CLQ-17) verified that an `ollama/` model uses CrewAI's
native OpenAI-compatible client, whose default is `localhost:11434`. That
port on Chris is the wrong Ollama. The runner passes
`base_url=http://127.0.0.1:11435/v1`, sets `OLLAMA_HOST=127.0.0.1:11435`,
and refuses `is_litellm=True` or any other effective endpoint. It also
sets `Crew(tracing=False)`, keeps the litellm local-cost and telemetry
flags, and does not set `CHROMA_ANONYMIZED_TELEMETRY` or
`TIKTOKEN_CACHE_DIR`. The working directory is the D: sandbox, and a
`.env` there is refused. E5 sets `HTTP_PROXY`, `HTTPS_PROXY` and
`ALL_PROXY` to `http://127.0.0.1:9` with `NO_PROXY=127.0.0.1`.

## Approved local model

Owner approval at 2026-10-18 15:28 IDT, recorded in issue 612 comment
6250120048. The approved endpoint is `http://127.0.0.1:11435` with model
`qwen3.5:9b`, digest
`56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90`.
Port 11434 is not the pilot listener. The provider sends `think: false`.
LAB-2 showed that Ollama's `/v1` endpoint ignores `think: false` and that
`reasoning_effort: "none"` disables qwen3.5 reasoning there. The frozen
model input records `reasoning_effort: "none"`, and the crew LLM passes
that value. It refuses any non-loopback host, any digest other than the
approved digest, and any process that does not have `OLLAMA_NO_CLOUD`
set to `1` or `true`. Remote and paid APIs stay refused.

A completed kickoff saves its text at
`D:\\Velvet\\Pilots\\crewai-e4\\sandbox-home\\crewai-output\\kickoff.md`
and records that path and sha256. The receipt status stays
`NOT_VERIFIED`. Any exception during the run writes a `FAIL` receipt.
On Windows, zero listening ports is proven from the pilot process tree
with Get-NetTCPConnection / Get-NetUDPEndpoint, or `netstat -ano` when
those cmdlets fail. An unproven observation is refused.

## Pins that block the CVE fixes

CrewAI 1.15.28 (`lib/crewai/pyproject.toml` at tag 1.15.28) declares:

- `chromadb~=1.5.9` in the required `dependencies` list (PEP 440: `>=1.5.9`, `==1.5.*`)
- `mcp~=1.28.1` in the same required list (`>=1.28.1`, `==1.28.*`)
- optional extra `tools = ["crewai-tools==1.15.28"]`

`mcp~=1.28.1` does not allow `mcp` 1.30.0. The installed lock pin is
`mcp==1.28.1`, which carries CVE-2026-59951. The fix version 1.30.0 is outside
the pin. A future CrewAI release would have to widen the pin. This runner does
not override it and does not install with `--no-deps`.

`chromadb~=1.5.9` is not an extra. The tools extra is `crewai-tools`, and
excluding that extra does not remove chromadb. `memory=False` also does not
remove it. Comment 6250224612 verified the eager chain: `crewai/__init__.py`
imports `memory/unified_memory.py`, which imports
`rag/embeddings/providers/openai/openai_provider.py`, which imports chromadb.
Omitting the chromadb wheel breaks `import crewai`. chromadb 1.5.9 carries
PYSEC-2026-311, PYSEC-2026-3813, PYSEC-2026-3814 and PYSEC-2026-3815, and no
fix is recorded. Those four advisories are server-side. The post-run check
therefore fails closed on `chromadb.server`, `fastapi`, `uvicorn` and `mcp`
in `sys.modules`. It does not treat the `chromadb` package itself as a
violation, because `import crewai` loads that package. The runner also
refuses the `chroma` CLI and any pilot listening port.

## Egress hardening

Issue 612 comment 6250954627. The runner still does not call a model, and the
E3 lock sha and approved versions are unchanged. `CREWAI_DISABLE_TRACING` is
not set, because that switch does not exist in crewai 1.15.28.
`TIKTOKEN_CACHE_DIR` stays forbidden.

Before `import crewai` the runner writes
`crewai-storage\.crewai_user.json` as
`{"first_execution_done":true,"trace_consent":false}` and, after the run,
requires those exact bytes. A missing file or `trace_consent: true` is a
refusal. A changed file is a failure.

It also refuses an installed `litellm`, `tiktoken`, `posthog`,
`crewai_tools`, or `fastapi` (`BLOCKED_SECURITY`) and treats those names as
forbidden modules after the run. The constructed agents must have
`from_repository is None`, empty tools, and no MCP or knowledge. The crew
must have `memory=False` and `tracing=False`. `from_repository="x"` is the
ZDI-26-706 / CVE-2026-92206 mutation.

`Path.home()` and `tempfile.gettempdir()` must resolve inside the sandbox.
On Windows, a wrong `USERPROFILE` is a refusal even when `HOME` is the
sandbox. After the run these files must be absent:
`.config\crewai\settings.json`, `%TEMP%\crewai_settings.json`,
`.\crewai_settings.json`, and `.cache\chroma\telemetry_user_id`.

`e3-supply-chain.json` maps PYSEC-2026-311/3813/3814 to CVE-2026-45829,
CVE-2026-45830 and CVE-2026-45833. `fastapi` is recorded as absent from the
lock. crewai-tools CVE-2026-2275/2285/2286/2287 are N-A. mcp CVE-2026-52869
and CVE-2026-59950 are not affected at 1.28.1. CVE-2026-59951 stays RED.
ZDI-26-706 is present in the pin and unreachable.

## LAB-4 rehearsal

Issue 612 comment 6251061341. Still no model call and no machine run.
The E3 lock sha and approved versions are unchanged.

Ollama 0.40.6 `/api/show` has no digest. The provider reads
`/api/tags` and matches the model name. A `/api/show` body is a mismatch.

The Windows listener script passes `Generic.List` values through
`.ToArray()`. Forbidden modules are checked before that observation, so a
listener failure cannot hide `chromadb.server`, `fastapi`, `uvicorn`, or
`mcp`.

`apply_telemetry` checks `OLLAMA_HOST` and the proxy before it fills absent
values. A wrong value is refused. The provider also refuses an Ollama
listener on `0.0.0.0` or `::` for port 11435. A missing bind observation is
unproven. The check does not open a socket.

`crewai` 1.15.28 `crewai_core.lock_store.lock` writes
`tempfile.gettempdir()/crewai:{md5}.lock`. On Windows the colon is an NTFS
alternate-data-stream separator, so the call creates a 0-byte file named
`crewai`. CPython skips `TEMP`/`TMP` when that directory does not exist, and
a SYSTEM process then uses `C:\Windows\Temp`. The runner creates the sandbox
temp directories before import and refuses `C:\Windows\Temp\crewai` after
the run.

Both tasks interpolate `{issue_rows}`. Kickoff text that says no rows were
provided, or whose table cells are only `N/A` / `UNKNOWN`, fails.

A preflight model refusal is stored as `model_status` and as the receipt
reason. A FAIL after kickoff keeps the kickoff.md sha256. The receipt
records the listener count and source.

`KillHarness.socket_timeout` enforces the 600s budget and caps each
`urlopen` at the time remaining, or 30s. `/api/chat` sends
`options.temperature` 0.0. A non-empty `PYTHONPATH`, or a `sitecustomize`
outside the interpreter prefix, is refused.

`--sandbox` defaults to the E4 root and must stay on `D:` under `D:\Velvet`.

## Listener portability

Issue 612 comment 6251194655. On macOS the listener check uses
`lsof -nP -a -p <pid> -iTCP -sTCP:LISTEN`. A header with no rows, or lsof
exit 1 with empty stdout and stderr, is a proven zero. A missing `lsof`,
stderr, or any other status is unproven. Linux still reads `/proc/net/tcp`.
Anything that is neither Windows, macOS, nor Linux fails closed.

`scripts/office_v2_crewai/evidence/**/*.reg` and `**/*.json` are
`text eol=lf`. The sensor requires that rule for every suffix in the
evidence directory, so a Windows checkout with `core.autocrlf=true` does
not turn `hkcu-after.reg` into CRLF.

## Lock identity

The Chris lock file is `requirements-locked.txt`, sha256
`121c1bd04eee730b51eb71e49da503b0d0236cdd06d8687a5df792234f78a669`, with 154
hash-pinned wheels. The recorded scan is still RED. The owner decision accepts
that residual risk only with the conditions above. The committed files are
`scripts/office_v2_crewai/evidence/e3-supply-chain.json` and
`e3-security-decision.json`. A different lock sha, a missing condition, or a
guard that accepts a violation keeps E3 at `BLOCKED_SECURITY`.

## Open-issue fixture

`gh issue list` for open issues on `nocturney/velvetos-core` returned 12
issues, including 612 and 595. The frozen export is those 12 issues, an answer
sheet of 20 facts, and one adversarial fixture. It does not pad with closed
issues or pull requests, and it contains no title, SHA, or URL from
`velvetos-velvet-factory`. The manifest stores sha256 of those three files.
