# Office 2.0 / ChatGPT-060 - CrewAI pilot E5 network evidence

**State: SPEC_AND_OFFLINE_SENSOR_ONLY / NOT_RUN_ON_CHRIS / E5_NOT_ADMITTED.**
Owner: Office 2.0, independent QA required. Date: 2026-10-18. This PR
adds a bounded observer, NOT a firewall, network sandbox, GO, or model run.

## Authority, scope and hard decision

- [Owner E3 decision, #612 comment 6250234075](https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6250234075): E3 `ACCEPT RISK WITH CONDITIONS`, **not** E5 approval. CrewAI 1.15.28 with chromadb 1.5.9 / mcp 1.28.1 stays restricted: `memory=False`, no knowledge/RAG/MCP/crewai-tools, empty tools, no loaded chroma server/fastapi/uvicorn/mcp module after run. No `chroma` CLI. Repeat import/no-load check on the actual Windows lock. A pilot-owned listening port is prohibited even on loopback.
- [Reviewed runner PR #789](https://github.com/nocturney/velvetos-core/pull/789) owns E1-E7 preflight and task behavior; this script must not bypass a missing E5 or fabricate runner authorization. [Existing CrewAI runbook](pilot-runbook-crewai.md) controls Chris, least privilege, D:-only containment and especially E4's independently observed **zero C: effects**. E4 remains RED if that cannot be demonstrated, irrespective of an E5 receipt.
- Attended execution only on Windows host **Chris**, under `D:\Velvet\Pilots\OfficeV2-VerifiedTrio`, 10-minute maximum, no host-wide installation, no network/firewall configuration change, no GitHub/model action in CI, no SYSTEM/admin/Fleet, and no writes to C:. Preserve #612 P0 resource leases. This repository change does **not** run the pilot.

## Endpoint policy (exact and conservative)

Use `Get-CimInstance Win32_Process` (`ProcessId`, `ParentProcessId`, `CreationDate`) to select the newly launched pilot PID and observed descendants, recording `pid`, `parent_pid` and UTC `created_at_utc` for each member. At each phase sample **both** unfiltered Windows network tables, `Get-NetTCPConnection` and `Get-NetUDPEndpoint`, then keep only endpoints whose `OwningProcess` belongs to the validated pilot tree. This excludes the **separate** Ollama server listener, even if it resides on `127.0.0.1:11435`.

**Process ancestry is an independent E5 gate.** The Windows collector validates the CIM chain before it reads sockets. A tree larger than 4096 members fails `PROCESS_TREE_TOO_LARGE`. A nonempty sample whose root is absent fails `TREE_ROOT_MISSING`. A root whose parent is inside the tree, or any visited cycle, fails `PROCESS_TREE_CYCLE`. A missing parent fails `PROCESS_TREE_ORPHAN`. A child CIM birth earlier than its parent fails `CHILD_CREATED_BEFORE_PARENT`. The root's CIM `CreationDate` must match the process-handle `StartTime` within 0.01 seconds or the sample fails `ROOT_PID_BIRTH_MISMATCH`. That tolerance assumes the two clocks share FILETIME precision; a mismatch fails closed. After the TCP/UDP queries the collector re-queries CIM and fails `PROCESS_IDENTITY_CHANGED_DURING_SAMPLE` if a member's UTC birth changed or the PID disappeared. Only then are validated members added to the stop-list. A descendant whose parent has already exited is an orphan and fails closed.

The offline evaluator is the single one in `scripts/vf_office_v2_crewai_e5_network.py`. A nonempty snapshot must contain `root_pid`, and every PID must have an acyclic `parent_pid` chain to that root. An orphan, a cycle, or a missing root emits `INVALID_TREE_ANCESTRY`. A TCP owner that is not in the recorded PID set emits `TCP_OWNER_NOT_IN_TREE` (UDP: `UDP_OWNER_NOT_IN_TREE`). The same PID with a different `created_at_utc` across snapshots emits `PID_REUSED_OR_IDENTITY_CHANGED`. An empty during tree emits `ROOT_NOT_OBSERVED_DURING`. A missing `process_tree` emits `INVALID_SNAPSHOT_SHAPE`. A non-numeric PPID emits `INVALID_TREE_MEMBER`. That evaluator does not emit the collector reason codes above, and it does not compare child and parent birth times. Birth ordering and the root-parent-outside-tree check stay collector gates. **Any ambiguity fails the sample.** This uses Windows CIM, never Linux `/proc`.

| Observation in pilot process tree | Verdict |
| --- | --- |
| Any TCP state `Listen`, including `127.0.0.1` | **FAIL** |
| Any TCP remote other than literal `127.0.0.1:11435`, including LAN, public IP, IPv6, `127.0.0.1:11434`, unconnected/unknown remote `0.0.0.0:0` | **FAIL** |
| Any bound UDP endpoint, including loopback | **FAIL** (UDP has no `Listen` TCP state, but can receive datagrams) |
| Missing `before`, `during`, `after`, missing root observation during, failed network/CIM query, unverified PID reuse, timeout, nonzero exit, lingering child, malformed timestamps/evidence | **FAIL** |
| Complete bounded sample sequence with none of the above | `PASS_SAMPLED_NOT_ENFORCEMENT` **only**; never pilot GO |

The **before** sample is taken before launch and filtered to the as-yet absent process tree (normally empty). The **during** array is sampled immediately after launch, then repeatedly at 100-1000 ms intervals while the process is live. The **after** sample is taken after exit or attempted owned-process termination, including any surviving tracked descendants. Snapshot times and process birth times are UTC (`Z`). A policy violation initiates termination of *verified owned* PIDs, never Ollama or unrelated host processes. No blind kill by PID without checking creation time.

**Critical evidence limitation:** discrete `Get-Net*` snapshots can miss very brief sockets, descendants that spawn and exit between polls, endpoints whose ownership is hidden by the OS, and unobserved escaped descendants. A positive snapshot result **cannot prove** that no listener or prohibited connection ever existed, or that effective deny-by-default OS controls are installed. An independent reviewer must separately verify effective restricted-identity firewall/WFP deny rules and event/ETW-level coverage for the entire tree (or an equivalently enforced containment), including denied connection/bind tests. Fail **BLOCKED_SECURITY / NO_GO** on any coverage gap. Never interpret `PASS_SAMPLED_NOT_ENFORCEMENT` as satisfying all of E5 by itself.

## Reviewed operator procedure (future; NOT an authorization)

1. First record E1 owner GO and current E2 capacity, E3 actual locked imports and conditions, E4 effective D:-only containment with OS-side C: write attribution, E6 immutable fixture, E7 pilot-only bounded stop, no credential inheritance, and effective inbound/outbound network **deny-by-default** for the pilot identity. Failure of any gate stops the run; do not start the evidence wrapper. Verify exact SHA-256 of the reviewed scripts and executable and stage **all** dependencies/sources, Python/venv, writable temp, receipt directory and home inside the approved D: subtree, with no reparse points.
2. In a preapproved attended PowerShell console, point all paths below to the **reviewed staged copies** under `D:\Velvet\Pilots\OfficeV2-VerifiedTrio`. The arguments are the reviewed runner command line; do not invent new flags or invoke it before runner E1-E7 preflight can actually pass. The following is a shape example **only**, not a runnable approval or a scheduled workflow:

   The collector admits `WorkingDirectory` equal to `$p` and any directory under `$p`. A sibling prefix such as `D:\Velvet\Pilots\OfficeV2-VerifiedTrioX`, or a `..` path that normalizes outside `$p`, is `OUT_OF_PILOT_ROOT_PATH`. The E4 sandbox root stays `D:\Velvet\Pilots\crewai-e4\sandbox-home` and is not an E5 working directory. The reviewed runner returns process exit 0 only after a post-guarded kickoff whose receipt is still `NOT_VERIFIED` / `AWAITING_INDEPENDENT_REVIEW`. Every refusal returns nonzero. This validator still requires integer `exit_code` 0 and records `PILOT_EXIT_NOT_ZERO` otherwise.

   ```powershell
   $p = 'D:\Velvet\Pilots\OfficeV2-VerifiedTrio'
   & "$p\scripts\collect-crewai-e5-network.ps1" `
     -PilotExecutable "$p\.venv\Scripts\python.exe" `
     -PilotArguments 'REVIEWED_RUNNER_ARGUMENT_LINE' `
     -WorkingDirectory "$p\crew" `
     -ValidatorPython "$p\.venv\Scripts\python.exe" `
     -ValidatorScript "$p\scripts\vf_office_v2_crewai_e5_network.py" `
     -EvidencePath "$p\receipts\e5-snapshots.json" `
     -ReceiptPath "$p\receipts\e5-receipt.json" `
     -SampleIntervalMs 250 -MaxSeconds 600
   ```

3. The PowerShell collector **starts only the specified D:-root executable** with `Start-Process -PassThru`, snapshots TCP/UDP for the tracked PID tree, immediately refuses observed listeners/other remotes/UDP, bounds runtime, and stops only matched pilot-owned PIDs on failure. It writes ASCII-compatible UTF-8 no-BOM JSON snapshot bytes to the D: evidence path. The D:-venv Python **stdlib-only** validator `scripts/vf_office_v2_crewai_e5_network.py` independently evaluates every recorded snapshot and writes `e5-receipt.json` with verdict, UTC start/end/evaluation times, source-byte SHA-256, explicit error codes, and SHA-256 of the canonical receipt JSON **excluding** its `sha256` field (`sort_keys=True`, compact separators, ASCII). This self-hash detects accidental drift, not forgery; preserve and independently witness exact bytes. Missing receipt is FAIL. Neither tool reads or writes C: intentionally; Windows incidental C: effects are a separate mandatory E4 blocker.
4. Independent reviewer binds the received evidence/receipt hashes to the actual pilot process start/exit, reviewed runner commit/lock and attempt ID (in the separate run ledger); verifies network prevention/ETW and C: audit observations, confirms no forbidden imports were loaded under owner E3 conditions, and applies E5 verdict **only with** the OS controls. Never commit real runtime receipts, environment secrets or process-level data to this public repository. No automatic resumption on unknown outcome.

## Offline regression and acceptance

`scripts/check-crewai-e5-network.py` runs in `scripts/check-all.py` via the DOMAIN sensor registry. It feeds synthetic pre/during/post fixtures directly to the **same** stdlib validator and subprocess CLI, checks the canonical receipt self-hash, and proves fail-closed mutants: `Listen`, non-loopback remote, wrong Ollama port, missing **any** phase, UDP bind, missing collector proof, lingering child, root not seen, bad UTC, failed process, non-scalar root PID, and detached or cyclic trees (`INVALID_TREE_ANCESTRY`). It also proves PID reuse across snapshots (`PID_REUSED_OR_IDENTITY_CHANGED`), a TCP owner outside the recorded PID set (`TCP_OWNER_NOT_IN_TREE`), a missing `process_tree` (`INVALID_SNAPSHOT_SHAPE`), a non-numeric PPID (`INVALID_TREE_MEMBER`), and a during tree that does not contain `root_pid` (`INVALID_TREE_ANCESTRY`). It proves a sampled PASS for a valid three-generation descendant tree. The sensor statically verifies the collector is ASCII/LF without BOM and contains Windows CIM PID/PPID/CreationDate ancestry, the 0.01-second root-birth check, post-network identity recheck, and TCP/UDP observation paths. CI never uses Windows cmdlets, starts Ollama, creates network sockets or claims a live E5 PASS. Post-merge, separately authorized attended Chris evidence is still required.

## Result and rollback

**Current:** `CODE_AND_OFFLINE_NEGATIVE_FIXTURES_ONLY / CHRIS_NOT_RUN / E5_BLOCKED_UNTIL_OS_ENFORCEMENT_AND_INDEPENDENT_EVIDENCE`. If observations fail, stop owned descendants, preserve the immutable D: snapshot/receipt and the failing reason; keep the prior pilot state, do not retry a possibly unknown model call automatically. Removal is limited to the newly staged collector/validator copies and scratch receipts under the pilot D: root after retaining audit evidence. No changes to OS firewall, services, production, C:, or #604/#602 work.
