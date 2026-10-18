# Office 2.0 — CrewAI pilot runbook (Chris / D: only)

**State:** RUNBOOK_ONLY / NOT_INSTALLED / NOT_RUN / NOT_ADMITTED. **Document owner:** Office 2.0; an attended, separately authorized Windows operator executes any future run. **Updated:** 2026-10-18.

**Authority and dependencies:** [merged three-tool pilot plan, PR #775](../implementation/office-v2/phase2/verified-three-tool-local-pilot-2026-10-18.md) (merge `d101809a88ea68ee4e2790aa3aba2d1fb5c40ea6`), [verified research #595](https://github.com/nocturney/velvetos-core/issues/595#issuecomment-6249011608), [#612 P0 priority](https://github.com/nocturney/velvetos-core/issues/612), and [Phase 2 admission policy](../implementation/office-v2/phase2/admission-policy-v0.md). The plan controls scope and scoring; this document narrows **CrewAI only** to an operator procedure on **Chris**. LangGraph and UFO are **not** authorized by this runbook; UFO remains SECURITY_BLOCKED.

> **This PR writes documentation and a README pointer only.** It does not provision Python, create a venv, install dependencies, create a runner, execute a test, book a host lease, open a port, change a policy, or grant runtime authority. Reading this runbook is **not** a GO decision.

## 1. Hard boundaries (non-negotiable)

1. **Host:** Windows machine **Chris** only, under an approved, least-privileged, non-admin pilot identity. No administrator, SYSTEM, production session, unattended task, second host, or shared P0 worktree.
2. **Filesystem:** every pilot-controlled executable, Python 3.12 distribution, virtual environment, model, imported package, input, output, temporary file, cache, profile, log, receipt and cleanup manifest must resolve to **`D:\Velvet`**. The active pilot is confined still further to **`D:\Velvet\Pilots\OfficeV2-VerifiedTrio`**. No pilot writes, caches, downloads, fallback paths or side effects to **`C:`**, even through `%TEMP%`, `%APPDATA%`, `%USERPROFILE%`, `pip`, bytecode, subprocesses, symlinks, junctions, reparse points or system services. No access to unrelated `D:\Velvet` projects.
3. **Literal C: warning:** ordinary Windows may write event logs, Prefetch, Defender state, profiles or paging data on its system drive even when the working directory and venv are on D:. A D:-located venv **alone does not prove “nothing on C:”**. If the strict zero-C:-effects requirement cannot be enforced **and independently observed across the pilot process tree and attributable OS helpers**, the verdict is **BLOCKED_STORAGE / NO_GO; do not run on Chris**. This runbook neither silently relaxes that requirement nor instructs anyone to modify the system volume. A separately reviewed containment design and owner decision would be required to change it.
4. **No authority / business surfaces:** strictly no Instagram, Meta, WhatsApp, social publishing, customer identities or data, orders, payment systems, bank/billing, external mail or messages, printers/CAD commands, production sources of truth, **Fleet/SYSTEM**, #604 placement/leases or #602 Cua control. No secrets, tokens, cookies, local password stores, `.env`, OpenBao/ZITADEL/OPA credentials or production browser profiles.
5. **No tools or execution expansion:** CrewAI may classify and summarize **human-curated offline issue text** only. Its agent tool list must be **empty**: no `crewai-tools`, CodeInterpreter, SandboxPython, arbitrary code/shell, Python tool, URL/RAG/scraper, browser, MCP, plugin, file mutator or GitHub API. Inputs are data, never executable instructions. No autopush/auto-merge/auto-scheduler or new recurring spend.
6. **Network:** no public/LAN listener, no WAN egress, no telemetry/cloud fallback, no package fetch, no remote inference or paid API. Prefer **zero listeners**. If a local model is essential, its runtime, weights, loopback transport and identity must have a separate bounded security approval, remain within the D: containment, and be monitored; no implied exemption for `127.0.0.1`. Unknown connection/listener => STOP.
7. **Priority:** #612 independently verified coding-worker / two-host / QA-recovery work comes first. A live P0 lease, resource contention or uncertainty about host availability means **PARKED_CAPACITY**. This document does not preempt Cursor, Claude or other authorized work.

## 2. Intended workspace and source material (not created here)

All paths below are **proposed future paths**; no path is provisioned by this documentation PR:

| Purpose | Required path / rule |
| --- | --- |
| Approved Python 3.12 interpreter | e.g. `D:\Velvet\Runtimes\Python312\python.exe`; use its **verified absolute path**, never `py`, a PATH fallback or a C: installation |
| Pilot root | `D:\Velvet\Pilots\OfficeV2-VerifiedTrio` |
| Offline sanitized input and gold sheet | `...\inputs` (immutable to the runner) |
| CrewAI runner / locked dependencies (future, separate PR) | `...\crew\runner`, `...\crew\locks` |
| **Python 3.12 venv** | `D:\Velvet\Pilots\OfficeV2-VerifiedTrio\.venv` (and its `Scripts\python.exe`, `Lib\site-packages`, scripts and caches all on D:) |
| Per-attempt scratch / outputs | `...\crew\runs\<attempt-id>` |
| Pilot-only profile / temporary / caches | `...\crew\home`, `...\crew\tmp`, `...\crew\cache` |
| Sanitized CrewAI evidence / rollback manifest | `...\receipts` |
| Graph persistence smoke (future separate admission) | `D:\Velvet\Pilots\OfficeV2-VerifiedTrio\graph\checkpoints.sqlite` — persistent SQLite and its journals/WAL/SHM stay under `graph\` |
| Graph smoke receipts (future separate admission) | `D:\Velvet\Pilots\OfficeV2-VerifiedTrio\graph\receipts\` — sanitized smoke, replay, verification and rollback evidence |

The offline fixture is a human-reviewed, dated export of **at least 20 genuine open `nocturney/velvetos-core` issues** (including #612 and #595 context), with ID, title, state, labels, timestamp, URL and minimum needed text. Keep a hash-locked original, a handwritten/reference answer sheet, and a **separate** contradictory/unsupported adversarial fixture. Remove secrets, customer information and unrelated private material **before** the runner sees it. A stale export is not a live GitHub status check.

## 3. Entry gate — every row must be explicitly PASS

| Gate | Evidence the future operator and independent reviewer must see | On missing/FAIL |
| --- | --- | --- |
| E1. Authorization | This docs PR independently QA-approved and merged **plus a separate owner-approved runtime/installation scope**, named operator, time window and recorded GO; Phase 2 admission evidence retained | NOT_AUTHORIZED |
| E2. Chris capacity | Fresh #612 lease/resource observation; #604 Fleet and #602 Cua scopes untouched; no active P0 or other shared worktree conflict | PARKED_CAPACITY |
| E3. Locked supply chain | Exact compatible, transitive **hash-locked offline** package set and Python **3.12.x**, pre-reviewed package licenses, hashes and current CVE/reachability scan. Follow the merged #775 security floors but do not mistake dated candidate pins for an installed, resolver-verified lock. The no-tools path is independently verified; `crewai-tools` absent | BLOCKED_SECURITY |
| E4. D:-only containment | Python executable, venv, working directory, subprocesses, dynamic DLL/package paths, profile, environment-based caches, logs, model runtime and output roots are canonicalized under the approved D: roots. Enforcement covers reparse/junction escapes and all writable child processes. Negative denial checks confirm that `C:` and out-of-root paths **cannot be written**, with no real forbidden write. File/process audit coverage and pilot-only rollback mechanism are demonstrated; attribution of OS-side writes is reviewed | BLOCKED_STORAGE |
| E5. Network and identity | Restricted identity, effective deny-by-default outbound/inbound rules, zero unauthorized listeners/connections, no usable credentials or production login, empty agent-tool registry; no elevated services. Record rules *as observed*, do not configure production firewall from this runbook | BLOCKED_SECURITY |
| E6. Immutable offline fixture | At least 20 issue IDs match the reviewed source; separate negative fixture; input and gold-sheet SHA-256 and schema recorded; no live repository/API fetch | NOT_VERIFIED |
| E7. Guardrails | Operator has working **kill/stop** for *pilot-owned* process tree only, prior host/process/filesystem baseline, D: receipt sink, 10-minute hard timeout **per attempt**, pre-approved CPU/RAM cap and explicit cost ceiling **zero additional spend** | NO_GO |

**Special fail-closed consequence for Chris:** if Windows system-drive behavior makes E4 unprovable, **record BLOCKED_STORAGE and stop at preflight**. Do not perform a “best effort” CrewAI run, change `C:`, mount a new system environment, disable OS security services, or assert a false guarantee.

### 3.1 Exact 2026-10-18 pins; dependency-hash lock is a future entry requirement

The **exact prospective direct pins** for a separately approved Windows/Python 3.12 offline lock are:

```text
crewai==1.15.28
langgraph==1.2.16
langgraph-checkpoint==4.3.0
langgraph-checkpoint-sqlite==3.1.2
langgraph-sdk==0.4.8
langsmith==0.14.11
```

These six direct versions do **not** assert a dependency-resolved, compatible, installed or SHA-256 hash-locked environment. The merged [#775 plan](../implementation/office-v2/phase2/verified-three-tool-local-pilot-2026-10-18.md) and its [direct-only manifest](../implementation/office-v2/phase2/requirements-verified-three-tool-pilot.txt) predate the LangSmith pin and comment the remote SDK as optional. This runbook records the exact SDK version without authorizing a remote SDK/server; a future approved implementation must reconcile the manifest/selected packages with the full compatible transitive lock, without silently selecting optional integrations. [PyPI release evidence: CrewAI](https://pypi.org/project/crewai/1.15.28/), [LangGraph](https://pypi.org/project/langgraph/1.2.16/), [checkpoint](https://pypi.org/project/langgraph-checkpoint/4.3.0/), [SQLite checkpoint](https://pypi.org/project/langgraph-checkpoint-sqlite/3.1.2/), [SDK](https://pypi.org/project/langgraph-sdk/0.4.8/), [LangSmith](https://pypi.org/project/langsmith/0.14.11/).

**Future lock acceptance:** independently resolve all transitive packages and preserve a Python-3.12/Windows-compatible lock with **SHA-256 hashes for each exact selected wheel/artifact**, including a trusted D:-local offline wheelhouse manifest, reviewed licenses, vulnerability scan and package import location. Reject an incompatible combination, hash mismatch, missing artifact, unpinned transitive, unapproved source build or index/network dependency. No resolver, download, lock-file creation, install or import is done by this documentation PR. The six lines above are **not** an executable installation manifest.

**CrewAI tool/memory policy:** `crewai-tools` is **entirely excluded** (not even the optional comment in the historical candidate manifest is an installation instruction for this run). Do not use/import `CodeInterpreterTool`, `SandboxPython`, `allow_code_execution` (even as a deprecated configuration parameter), `code_execution_mode`, shell/exec tools, browser, RAG/URL tools, plugins or arbitrary code. crewai-tools 1.14.0 removed CodeInterpreterTool and deprecated agent code-execution parameters. The Crew must explicitly set **`memory=False`**, keep agent tool arrays **empty**, and use **short, stable ASCII agent roles** (for example, `Triage` and `Reviewer`). [CrewAI issue #3236](https://github.com/crewAIInc/crewAI/issues/3236) describes long role-derived Windows memory folder names; it was closed as not planned, and this pilot has no independently accepted fix evidence for the issue.

**Visual Studio Build Tools are NOT preapproved.** Treat them only as a native-build **fallback** after a separately reviewed dependency resolution proves no usable, trusted compatible wheel exists. The normal Build Tools installation writes to **C:** and conflicts with the strict no-C: gate. Stop with **BLOCKED_STORAGE** and obtain **separate explicit approval from Christian**, with its own risk, confinement and rollback review, **before any C: installation**. Do not use that fallback under this runbook; an owner approval request is not a waiver of the current C: prohibition.

### 3.2 Telemetry/tracing disabled **before** any library import

All four variables below must be set in the **restricted child-process environment before the first import** of `crewai`, `langgraph`, `langsmith`, OpenTelemetry or any transitive library. Record their effective values from the child (without logging secrets):

| Variable | Required value |
| --- | --- |
| `CREWAI_DISABLE_TELEMETRY` | `true` |
| `OTEL_SDK_DISABLED` | `true` |
| `CREWAI_TRACING_ENABLED` | `false` |
| `LANGSMITH_TRACING` | `false` |

In **any separately admitted LangGraph smoke**, also enclose actual graph execution in **`with tracing_context(enabled=False)`** (LangSmith context manager), with the four environment flags still in place. Block inherited telemetry endpoints and provider credentials. Flags are defense-in-depth, **not** a network-control substitute: OS-enforced egress and listener denials, plus independent monitoring, remain required. If any flag was set after import, is not effective, or egress/trace export is attempted, **NO_GO/STOP**, with no post-hoc claim of privacy.

### 3.3 Two-part smoke contract for a **future separately authorized** execution

The sole allowed Python 3.12 virtual environment is **`D:\Velvet\Pilots\OfficeV2-VerifiedTrio\.venv`** (never a C: environment, PATH fallback, global interpreter or `crew\.venv`). The future operator records the exact interpreter path and SHA-256, six specified direct pins as relevant to the admitted dependency lock, verified full lock/artifact hashes, pre-import flag values and OS deny monitors **before** either smoke. Both smoke activities remain **NOT_RUN** under this documentation PR.

1. **CrewAI import smoke:** launch a new restricted process with only the approved venv interpreter, then `import crewai`; verify the installed CrewAI version is exactly `1.15.28`. Require **zero** accidental CrewAI tools, persistent memory initialization, telemetry, network calls, listening sockets, C: writes or paths outside the sandbox. An import-only PASS is not approval for model inference or CrewAI tasks.
2. **LangGraph persistent-checkpoint smoke (separately admitted):** instantiate **`StateGraph(int)`** with one deterministic integer-changing node and **`SqliteSaver`** attached to the on-disk path **`D:\Velvet\Pilots\OfficeV2-VerifiedTrio\graph\checkpoints.sqlite`** (including any SQLite journal/WAL/SHM in the same `graph\` subtree). With a unique `thread_id`, actually invoke the compiled graph to **write** a known changed integer state and checkpoint. Capture the checkpoint ID and post-write state/hash, **close the checkpointer/SQLite connection**, end that process, then **open a fresh connection in a new process** to the same D: database and `thread_id`, read the last persisted checkpoint and verify the **exact post-change integer** and checkpoint identity. An in-memory read or same-connection read **does not count**. All graph invocations use `with tracing_context(enabled=False)`.
3. **Fail-closed readback and receipts:** wrong/missing `thread_id`, absent/corrupt/mismatched checkpoint, inability to prove write/close/reopen, unapproved connection, telemetry, unknown process or path escape => **SMOKE_FAIL/NO_GO** without retry or result fabrication. Keep sanitized import evidence and **all graph smoke/checkpoint/reopen/rollback receipts under `D:\Velvet\Pilots\OfficeV2-VerifiedTrio\graph\receipts\`**; record attempt/thread/checkpoint IDs, source/lock/wheel hashes, state-before/after/reopened values, SQLite file and sidecar hashes, process termination, monitoring observations, and independent reviewer. No source script, SQLite file, receipt or environment is produced **now**.

This smoke is a **specification**, not a runtime authorization. It does not grant LangGraph/UFO production rights, network or service listeners, model download, scheduling, or new effect ownership.

## 4. Future attended operator sequence — never executed by this PR

The steps are **gated instructions** for a later reviewed execution change, not a command to run the pilot now.

1. **Record the booking and exact baselines.** Capture operator, explicit owner authorization, #612 lease status, Chris host ID, Windows build, UTC timestamp, approved source/lock SHA, Python executable hash, filesystem/process/network baseline, expected cost and chosen CPU/RAM ceilings. Stop if another worker already owns the host.
2. **Verify pre-provisioning, without installing anything ad hoc.** A separate approved implementation must have placed a genuine **Python 3.12.x** interpreter and a venv built **only** at `D:\Velvet\Pilots\OfficeV2-VerifiedTrio\.venv`, with a trusted, offline, hash-verified lock and reviewed read-only CrewAI runner. Check that the venv interpreter reports Python 3.12, its `sys.executable`, `sys.prefix`, `sys.path` and resolved package locations do not escape D:. Reject `py -3.12`, global Python, editable site-packages, implicit dependency installs or on-the-fly downloads.
3. **Use the restricted pilot context only.** The process starts with working directory under the CrewAI root; `TEMP`, `TMP`, `TMPDIR`, `HOME`, `USERPROFILE`, `APPDATA`, `LOCALAPPDATA`, Python bytecode/cache controls, PIP/UV/HF/model caches and all framework-specific storage/log locations must point inside the approved D: subtree **and actually be honored**. Confirm **all four §3.2 telemetry/tracing flags are present before any import**, with inherited tracing endpoints disabled; flags cannot replace egress denial. No user site-packages, credential inheritance, shared Windows profiles, browser sessions, roaming profiles or system-wide configuration. Verify effective writes with the pre-approved monitor; environment strings alone are not evidence. If resetting an environment variable breaks Windows behavior, STOP rather than fall back to C:.
4. **Prove the negative controls before running the model.** Verify that the pilot identity cannot write to C: or escape the subtree (including junctions), cannot invoke unapproved tools or access credentials, and cannot connect to unapproved network destinations or bind a listener. Use a reviewed **non-mutating/blocked-at-policy** probe; do **not** create a forbidden test file. Record monitor coverage, denied decisions and zero real violations. Any monitor blind spot = NO_GO.
5. **Freeze inputs.** Check offline issue-export/gold hashes; confirm at least 20 issue IDs with #612/#595 context, and check redaction. All issues are untrusted text, including embedded “instructions”. No GitHub token or API call is made by CrewAI.
6. **Invoke only the future independently reviewed no-tools runner via the venv absolute interpreter.** The invocation contract is `<D:-venv-Scripts-python.exe> <reviewed-D:-runner> --input <immutable-D:-snapshot> --output <unique-D:-attempt-dir>`. **No executable runner is delivered by this PR; do not invent one or run an unreviewed CLI.** Require `memory=False`, short stable agent roles, no `crewai-tools`, `CodeInterpreterTool` or `allow_code_execution`, an empty tool registry, bounded deterministic task instructions, an approved offline inference path (if one exists), a unique attempt ID, and deny all implicit egress. The output is a Hebrew Markdown issue summary plus issue→blocker/owner/next-action table, each entry pointing to the exact input issue row/URL; mark unsupported data UNKNOWN/NEEDS_REVIEW.
7. **Observe and stop on first violation.** Monitor process and child tree, C: and out-of-root write attempts/effects, file manifest, socket state, memory/CPU, operator intervention and elapsed time. A hard attempt deadline is **10 minutes**, not a target runtime. Stop on any condition in §5; do not auto-retry.
8. **Score the frozen data, not a live claim.** For an admitted run, use at least **5** attempts (including a cold attempt) and one independent adversarial-input check. Require **20/20** issue IDs supported by the snapshot; **zero** fabricated IDs, statuses, deadlines or assignments; ≥**90%** of a preselected 20-fact human-reviewed sample correctly sourced; contradictions/unsupported content labelled UNKNOWN; and zero unauthorized effects. Capture p50/p95 time, CPU/RAM peak and attended minutes; compare only against the same-input human/incumbent baseline. Every negative test must be denied. One failed safety gate ends the series.
9. **Tear down and independently inspect.** Perform §6 even after PASS_TASK_ONLY, hash and preserve sanitized receipts, compare post-state to baseline, have an independent QA reviewer assess the evidence. **No automatic promotion**, queue rewrite, merged artifact, or production activation follows a task score.

## 5. Immediate STOP / fail-closed rules

**Stop before any model call** when the entry gate is missing, exact §3.1 pins/hashes or §3.2 pre-import flags are unverified, the applicable §3.3 smoke for the separately admitted lane has not passed, the Python/venv/runner source is unknown, host lease is contested, any required file resolves outside D:, the C:-write monitoring/deny control is incomplete, the security scan is stale or the fixture contains secrets.

**Kill only the pilot-owned child process tree, mark FAIL (or BLOCKED_SECURITY / BLOCKED_STORAGE / PARKED_CAPACITY), and begin rollback immediately** on: attempted or observed C: write; path escape/reparse redirection; secret exposure; any unexpected socket, outbound contact, listener or telemetry; tool/shell/browser/GitHub mutation; production/customer/Instagram/payment/Fleet/SYSTEM touch; privilege change; unknown child process; prompt-induced policy violation; CPU/RAM cap or 10-minute timeout; changed source hash; new relevant high/critical advisory; corrupted output/evidence; operator veto.

If attribution, monitors, process termination, artifacts or cleanup cannot be proven, mark **RESTORE_REQUIRED / NOT_VERIFIED** — never PASS. Do not continue, rerun automatically, dismiss a denied-write alert, or attempt a compensating production operation.

## 6. Full pilot-only rollback and postflight

1. **Contain:** stop/terminate **only** the tracked pilot process tree and isolate the pilot identity. Confirm no pilot children, watchers, services, scheduled tasks, listeners or connections remain. Do not kill/reset #612 workers, Office services, Windows OS helpers or Fleet/SYSTEM.
2. **Preserve evidence first:** freeze input/output/runner and lock hashes; seal redacted stdout/stderr, access-denial traces, process/network observations, failure time and operator decision in `...\receipts`. Do not copy secrets or raw customer data into receipts. Record any missing evidence explicitly.
3. **Revoke pilot-specific capability:** remove/revert **only** pilot-scoped ACL grants, account/session leases, temporary network/firewall exceptions and local-model pilot approvals against the recorded before-state. Never broadly reset the host firewall, production credentials or shared users. If a rule cannot be attributable, stop and request owner recovery.
4. **Remove ephemeral pilot state within its manifest:** after receipt retention, delete/quarantine **only** manifest-owned per-attempt scratch, caches, disposable outputs and (if created solely for this pilot under a separately authorized implementation) its D:-local venv/runner/weights. If a separately admitted graph smoke ran, preserve sanitized `graph\receipts\` and database/sidecar hashes before deleting only manifest-owned `graph\checkpoints.sqlite` plus journal/WAL/SHM files, subject to the approved retention window; never erase unowned state. Do not delete the immutable source evidence until its retention policy permits; do not touch unrelated `D:\Velvet` folders. Unknown ownership => quarantine/no deletion.
5. **Prove restore:** compare before/after hashes of immutable fixture, approved repo/worktrees, lock and machine configuration; ensure zero pilot processes/connections, no auto-start/worker/scheduler, no persistent permissions, no stray storage and no changes to production or P0 leases. Independently inspect the C: audit. **Any C: write, unexplained host drift or unverifiable cleanup blocks rollback PASS.** Mark RESTORE_REQUIRED with exact difference and escalate for separately approved remediation; do **not** search or delete arbitrary C: files.
6. **Close:** append a sanitized rollback outcome and reviewer identity to the receipt. Only a verified exact-baseline restore may be `ROLLBACK_VERIFIED`; a clean task result without rollback proof is **NOT_VERIFIED**.

No production cutover was authorized, so there is **nothing in production to “roll back”**. This procedure restores solely the disposable pilot footprint; a discovered production mutation is a security incident, not a successful pilot teardown.

## 7. Receipt — required durable evidence, no fabricated PASS

One immutable, sanitized **per-attempt receipt** plus a **postflight/rollback receipt** under `D:\Velvet\Pilots\OfficeV2-VerifiedTrio\receipts` (schema/producer in a *future approved implementation*, not created here). At minimum record:

| Group | Required receipt fields |
| --- | --- |
| Identity and gate | `attempt_id`, UTC start/end, operator + independent reviewer, Chris host/build, approval link, #612 lease observation, admission gate E1–E7 PASS/FAIL/NOT_VERIFIED, task/pilot status, reason |
| Reproducibility | merged plan/source commit, reviewed runner full SHA and SHA-256, Python **3.12.x** absolute executable path + SHA-256, venv root, installed exact versions and transitive lock/digests, security scan/advisory timestamp, model/runtime identity and digest if used |
| Safety posture | six exact prospective direct pins and verified transitive SHA-256 lock when admitted; `memory=False`, short roles, zero `crewai-tools`/CodeInterpreter/deprecated code-exec flags, observed pre-import four telemetry variables, tracing context, zero-egress monitor, no Build Tools C: exception |
| Graph smoke (if separately admitted) | `graph\checkpoints.sqlite` and SQLite sidecar locations/hashes; `StateGraph(int)` write, close and **new-process reopen**, thread/checkpoint IDs, exact expected and persisted integer, `tracing_context(enabled=False)` observations and sanitized `graph\receipts\` hashes; otherwise `NOT_RUN` |
| Scope and input | sandbox canonical root, workspace manifest, environment-path map **without secret values**, input/gold SHA-256, snapshot date, 20+ issue IDs, adversarial fixture hash; no raw credential/customer payload |
| Execution and safety | process and child IDs, tool registry proved empty, resource ceiling/observed peaks, elapsed time, CPU/RAM, human minutes, cost (= 0 additional), listener/egress observations, C: denied/observed-write counts, out-of-root denial, unexpected child/tool/secret incidents, timeout/abort reason |
| Result | output paths and SHA-256, issue-by-issue source references, fabricated-ID/status/deadline counts, 20-fact review numerator/denominator, negative-control result, PASS_TASK_ONLY / FAIL / BLOCKED_SECURITY / BLOCKED_STORAGE / PARKED_CAPACITY / NOT_RUN / NOT_VERIFIED |
| Teardown | before/after process, filesystem and firewall/ACL comparison; pilot-scoped changes reverted; D:-only cleanup manifest and evidence retained; C: audit conclusion; `ROLLBACK_VERIFIED` or `RESTORE_REQUIRED`; signed human and independent QA verdict with timestamp |

**Receipt invariants:** a successful import or an in-memory graph query is not a durable SQLite close/reopen receipt. Hashes refer to *actual observed bytes*, not predicted outputs. Missing hashes, monitors, reviewer, exact interpreter path, C: proof or rollback evidence => **NOT_VERIFIED**. A documentation/CI PASS cannot be recorded as a runtime PASS. No secrets in receipt bodies; publish only redacted metadata through a later approved evidence flow.

## 8. Exit, ownership and next gate

- **Christian:** separately approves runtime scope/resource window and any containment redesign; authorizes no production rights by approving this document.
- **Attended Chris operator (future):** verifies all entry gates, runs an independently reviewed implementation if admitted, monitors and executes stop/rollback.
- **Cursor / implementation owner (future separate PR):** may propose offline runner, hash-locked dependency/venv provisioning and evidence producer; **this runbook does not ship them**.
- **Independent auditor / QA:** reviews actual gates, exact artifacts, monitors, receipt and rollback; signs PASS/FAIL independently from the PR author.
- **ChatGPT:** documents procedure and README pointer; cannot independently QA or merge its own PR.

**Exit today:** `RUNBOOK_ONLY / NOT_RUN`. The next authorized step is **independent exact-head documentation QA**; only later may an owner approve a separate security-reviewed runtime PR and a free Chris lease. CrewAI task PASS, when eventually proven, would still **not** equal Phase 2 LAB admission, runtime promotion, #612 P0 completion or permission to operate Instagram, payments, customers, secrets or Fleet/SYSTEM.
