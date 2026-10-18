# First attended CrewAI pilot on Chris (ChatGPT-064)

**State: docs-only operator checklist; NOT a runtime GO, NOT a pilot result.**
For Christian and the independent security reviewer. Attend from a **non-admin, non-SYSTEM Windows PowerShell 5.1** session on **Chris** only, not Chris-3DPC. No tools, memory, knowledge, RAG, MCP, plugins, browser, shell-agent tools, live issues, private data, paid APIs, cloud model, unattended execution, scheduling or production effects. All pilot-controlled artifacts stay under **D:\Velvet**; the existing governed stage root is **D:\Velvet\Pilots\OfficeV2-VerifiedTrio**. No pilot-attributable C: write, including OS-side effects.

Sources: [original strict runbook](pilot-runbook-crewai.md), [current E1-E7 board](NEXT.md#2-priority-1--first-bounded-crewai-pilot-e1e7), [#612 decisions and receipts](https://github.com/nocturney/velvetos-core/issues/612), [E3 risk acceptance](https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6250234075), [E5 observation contract](pilot-e5-network-evidence.md), [LAB-4 on Chris-3DPC](https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6251061341).

## 0. Before any invocation: seven gates and code dependencies

- [ ] **Staged runner is merged #799 (`f3dd4e4c`) or a later reviewed descendant that still matches this contract, independently QA-reviewed**: [hardening PR](https://github.com/nocturney/velvetos-core/pull/799). Its LAB-4 repairs use the **GET /api/tags** model digest instead of /api/show and .ToArray() for a Generic.List on PowerShell 5.1. Inspect the staged commit, not an older PR head. [#789 runner](https://github.com/nocturney/velvetos-core/pull/789), [#795](https://github.com/nocturney/velvetos-core/pull/795) and [#797 ancestry](https://github.com/nocturney/velvetos-core/pull/797) are separately merged code predecessors. A merged code fix is not an attended-run authorization.
- [ ] **Re-verify two snippets in this checklist against the staged merged runner.** `apply_telemetry(dict(os.environ), SANDBOX_ROOT)` in section 1.3 is a two-argument call, and section 1.4 passes `--sandbox`. Both are on the merged runner. A match to a pre-merge head is not enough.
- [ ] **Refresh source-of-truth E1-E7 state at attempt time:** [board](NEXT.md#2-priority-1--first-bounded-crewai-pilot-e1e7) and [#612](https://github.com/nocturney/velvetos-core/issues/612). Record board timestamp and each independent evidence/approval URL. Do not transpose the board's dated status into a current PASS. All seven require actual PASS:
  - **E1 authorization:** separately recorded Christian one-run GO, named operator, time window, merged docs and approved exact scope; prior model-only approval is not this GO.
  - **E2 capacity:** fresh Chris lease, CPU/RAM headroom and no #612 P0, #604 Fleet or #602 Cua contention.
  - **E3 security:** Christian's conditional acceptance applies only to 154 hash-locked offline wheels, SHA-256 **121c1bd04eee730b51eb71e49da503b0d0236cdd06d8687a5df792234f78a669**, CrewAI 1.15.28, no tools/memory/knowledge/MCP/server, forbidden-import checks and independent review. The underlying vulnerability scan remains RED; no general waiver.
  - **E4 containment:** reviewed, enforced and independently witnessed absence of C: or out-of-D: writes for the whole process tree and OS helpers, negative controls, true paths, before/after manifests, HKCU and attribution. Setting TEMP or a D: venv is NOT proof.
  - **E5 network:** restricted identity; only approved local Ollama **127.0.0.1:11434** (Christian, 2026-10-18 20:41 IDT; port 11435 is refused); zero pilot listeners/UDP. **NEEDS_CHRISTIAN (open owner decision): deny-by-default outbound and inbound.** Periodic socket samples and `PASS_SAMPLED_NOT_ENFORCEMENT` are not that enforcement. An independent whole-tree monitor, including brief sockets, is still required and is not supplied by this checklist.
  - **E6 offline inputs:** at least **20 genuinely open public issues** including #612 and #595, dated immutable SHA manifest, human gold facts and adversarial fixture. The #789 snapshot had 12. The current committed fixture keeps those public rows and adds 8 synthetic rows so the file count is 20. Those synthetic rows are not a live public snapshot and are not an attended-run GO. Never use the synthetic_passing_bundle() test fixture to manufacture gates.
  - **E7 limits:** independently tested owned-PID stop, baseline and D: receipt sink, 600-second hard deadline, explicit CPU/RAM limit and **zero incremental spend**.
- [ ] **Stop before a real model call if any NEEDS_CHRISTIAN item below is unresolved.** Items 1–3 describe the merged runner. Items 4 and 5 stay open owner decisions:
  1. **Server-bind handoff — the provider collects netstat; English output required.** `runner.main()` has no `--binds` flag and forwards `binds=None`. That default is not always **OLLAMA_BIND_UNPROVEN**. At the model-call boundary the provider calls `collect_ollama_binds()` itself and then `assert_ollama_bind()` before `/api/tags` or `/api/chat`. On Windows the trusted binary is `C:\Windows\System32\netstat.exe -ano`, started with subprocess `PATH` limited to that binary's directory. Parsing requires English netstat text (`Active Connections` / `LISTENING`). A missing binary, a non-English locale, or unparseable text fails closed as **OLLAMA_BIND_UNPROVEN**. Section 1.2 Get-NetTCPConnection is still a separate manual observation and is not injected into the runner. Do not fake the list or use LAB-4 shims. The approved bind is **127.0.0.1:11434** only. Port **11435** is refused. A wildcard `0.0.0.0` bind is refused. Independent E5 evidence remains necessary. Deny-by-default network stays the open owner decision in the E5 gate above.
  2. **Process exit contract — merged runner.** A post-guarded completed kickoff whose receipt stays **NOT_VERIFIED / AWAITING_INDEPENDENT_REVIEW** returns runner exit **0**. Preflight refusals, failed guards, and exceptions return **2**. E5 requires integer `exit_code` **0** and otherwise records **PILOT_EXIT_NOT_ZERO**. Do not accept a nonzero exit as a workaround, and do not weaken the E5 rule. Exit **0** is not a reviewer PASS. Exit 0 plus those receipt states is the completed-unreviewed shape. Exit 2 is a refusal or a failure.
  3. **Pilot roots — two roots, both stay.** E4 `assess_evidence()` requires the sandbox index equal **D:\Velvet\Pilots\crewai-e4\sandbox-home**. The E5 stage root stays **D:\Velvet\Pilots\OfficeV2-VerifiedTrio**. Exact equality with that stage root is admitted, including `WorkingDirectory = $P` (the root without a trailing slash). A sibling suffix and a `..` segment still fail **OUT_OF_PILOT_ROOT_PATH**. Do not relocate either root and do not invent a subdirectory to bypass admission. No ad hoc change to hardcoded roots.
  4. **NEEDS_CHRISTIAN (open owner decision) — C: write denial and the 600-second watchdog.** Process env redirect and the Windows-temp-crewai spot check are not OS-wide C: write denial. An in-process socket timeout and a sampled Stop-Owned are not a Job Object and not an independent external whole-tree watchdog. Christian must designate who supplies audited effective C: denial/ETW attribution and reliable owned-tree termination on Chris within 600 seconds. An approval or spot check does not replace that evidence. This item stays open.
  5. **NEEDS_CHRISTIAN (open owner decision) — retries stay 0.** Code contains no finite retry counter and no classification authorizing repeats. #797 [QA note](https://github.com/nocturney/velvetos-core/pull/797#issuecomment-6251271710) warns that a normally exiting process may be marked FAIL because a PID identity recheck races exit. That race result is still FAIL, not an implied retry. Authorized retries remain **0**. Only a fresh documented decision by Christian and the independent reviewer can authorize manual repeats; see section 4. This item stays open.

The [LAB-4](https://github.com/nocturney/velvetos-core/issues/612#issuecomment-6251061341) synthetic-gate exercise was **on Chris-3DPC, not Chris**; it did not prove the Chris pilot. The three-dimensional PC also exhibited fatal WHEA machine-check reboots. Do not use it as a surrogate.

## 1. Attended Windows PowerShell 5.1 procedure

**Execution barrier:** The read-only and no-CrewAI-import checks below may be used only by the separately authorized operator. The section 1.4 model kickoff is a command **shape for future reviewed use**, never permission to bypass missing gates or NEEDS_CHRISTIAN items. All locations must already be staged/verified on D: by a separate approved procedure. No package installs, cloning, model launch or host firewall changes here.

### 1.1 Identify Chris, least privilege, exact staged code

~~~powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1) { throw 'STOP: require Windows PowerShell 5.1' }
if ($env:COMPUTERNAME -ne 'Chris') { throw 'STOP: wrong host' }
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($identity.IsSystem) { throw 'STOP: SYSTEM forbidden' }
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'STOP: elevated identity' }
$P = 'D:\Velvet\Pilots\OfficeV2-VerifiedTrio'
$Repo = Join-Path $P 'repo'
$Py = Join-Path $P '.venv\Scripts\python.exe'
$Runner = Join-Path $Repo 'scripts\office_v2_crewai\runner.py'
$Collector = Join-Path $Repo 'scripts\collect-crewai-e5-network.ps1'
$Validator = Join-Path $Repo 'scripts\vf_office_v2_crewai_e5_network.py'
# $Input is a PowerShell automatic variable. The staged inputs directory is $InputDir.
$InputDir = Join-Path $P 'inputs'
$Evidence = Join-Path $P 'receipts\crewai-gates'
$ReceiptRoot = Join-Path $P 'receipts'
$Model = Join-Path $Repo 'scripts\office_v2_crewai\model\approved-local-ollama.json'
$Sandbox = 'D:\Velvet\Pilots\crewai-e4\sandbox-home'
foreach ($item in @($Repo,$Py,$Runner,$Collector,$Validator,$InputDir,$Evidence,$ReceiptRoot,$Model)) {
    if (-not (Test-Path -LiteralPath $item)) { throw ('STOP: staged path absent: ' + $item) }
}
$identity.Name
$env:COMPUTERNAME
& $Py -B -c 'import sys; print(sys.version); print(sys.executable)'
if ($LASTEXITCODE -ne 0) { throw 'STOP: interpreter failed' }
& git -C $Repo status --porcelain
if ($LASTEXITCODE -ne 0) { throw 'STOP: git failed' }
& git -C $Repo rev-parse HEAD
if ($LASTEXITCODE -ne 0) { throw 'STOP: HEAD unknown' }
Get-FileHash -Algorithm SHA256 -LiteralPath $Py,$Runner,$Collector,$Validator,$Model
~~~

**Expect:** an actual non-admin/non-SYSTEM Chris identity, Python 3.12.x executing from the approved D: venv, a **clean** staged Git tree, and exact file hashes and commit matching the independently reviewed staged runner (merged #799 `f3dd4e4c`, or a later reviewed descendant of that contract). Compare to admission receipts (do not use an unreviewed SHA). A missing path, unexpected commit, C: fallback or privileged session means **STOP**, not a workaround. The E4 sandbox root and the E5 stage root stay distinct. `WorkingDirectory = $P` is the stage root and is admitted. Do not relocate either root.

### 1.2 Read E1-E7 source receipts and verify the Ollama listener/digest

~~~powershell
foreach ($name in @('e1-authorization.json','e2-capacity.json','e3-supply-chain.json',
                    'e3-security-decision.json','e4-containment.json',
                    'e5-network.json','e7-guardrails.json')) {
    $file = Join-Path $Evidence $name
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw ('STOP: evidence missing: ' + $name) }
}
foreach ($name in @('manifest.json','issues.json','answer-sheet.json','adversarial.json')) {
    if (-not (Test-Path -LiteralPath (Join-Path $InputDir $name) -PathType Leaf)) {
        throw ('STOP: input missing: ' + $name)
    }
}
$listen = @(Get-NetTCPConnection -LocalPort 11434 -State Listen -ErrorAction SilentlyContinue)
if ($listen.Count -lt 1) { throw 'STOP: Ollama listener absent' }
if (@($listen | Where-Object { $_.LocalAddress -notin @('127.0.0.1','::1') }).Count -ne 0) {
    throw 'STOP: Ollama non-loopback/wildcard bind'
}
foreach ($pidValue in @($listen | Select-Object -ExpandProperty OwningProcess -Unique)) {
    $proc = Get-CimInstance -ClassName Win32_Process -Filter ("ProcessId=" + $pidValue)
    if ($null -eq $proc -or $proc.ExecutablePath -notlike 'D:\Velvet\*') {
        throw 'STOP: listener executable not proven under D:\Velvet'
    }
    $proc | Select-Object ProcessId,ExecutablePath
}
$tags = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -Method Get -TimeoutSec 10
$selected = @($tags.models | Where-Object { $_.name -eq 'qwen3.5:9b' })
if ($selected.Count -ne 1 -or
    $selected[0].digest -ne '56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90') {
    throw 'STOP: model digest/name mismatches owner approval'
}
$selected | Select-Object name,digest
~~~

**Expect:** all reviewed E1-E7 evidence files exist and match independent gate proofs (existence by itself is NOT admission). Windows shows Ollama bound only to local loopback **127.0.0.1:11434** (optionally also ::1), owned by the approved D:-binary, and exactly **qwen3.5:9b** with SHA-256 digest **56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90**. Use **/api/tags**, not LAB-4's /api/show. If it is absent or mismatched **STOP**, do not start unreviewed Ollama, relocate the model, open 11435, widen the bind, or substitute a different digest. The provider collects that bind evidence itself with `C:\Windows\System32\netstat.exe -ano` and a subprocess PATH limited to `C:\Windows\System32` (section 0 item 1). This Get-NetTCPConnection sample is not injected into the runner. A missing binary, a non-English locale, or unparseable text is **OLLAMA_BIND_UNPROVEN**. A wildcard `0.0.0.0` bind stays refused. Port 11435 stays refused.

### 1.3 No-CrewAI-import preflight using exact reviewed Python functions

~~~powershell
$paid = @('OPENAI_API_KEY','ANTHROPIC_API_KEY','GEMINI_API_KEY','OPENROUTER_API_KEY',
          'GROQ_API_KEY','AZURE_OPENAI_API_KEY','COHERE_API_KEY')
$inherited = @($paid | Where-Object { [Environment]::GetEnvironmentVariable($_, 'Process') })
if ($inherited.Count -gt 0) { throw ('STOP: paid credential env names: ' + ($inherited -join ',')) }
if ($env:PYTHONPATH -or $env:PYTHONHOME -or $env:PYTHONUSERBASE -or $env:TIKTOKEN_CACHE_DIR -or
    $env:CUSTOM_TIKTOKEN_CACHE_DIR -or $env:CHROMA_ANONYMIZED_TELEMETRY) {
    throw 'STOP: forbidden environment override'
}
if ($env:OLLAMA_HOST -and $env:OLLAMA_HOST -ne '127.0.0.1:11434') { throw 'STOP: inherited OLLAMA_HOST' }
$proxyWant = @{
    HTTP_PROXY = 'http://127.0.0.1:9'
    HTTPS_PROXY = 'http://127.0.0.1:9'
    ALL_PROXY = 'http://127.0.0.1:9'
    NO_PROXY = '127.0.0.1'
}
$block = [Environment]::GetEnvironmentVariables('Process')
foreach ($key in @($block.Keys)) {
    $upper = ([string]$key).ToUpperInvariant()
    if ($proxyWant.ContainsKey($upper)) {
        $present = [string]$block[$key]
        if ($present.Trim().Length -gt 0 -and $present -ne $proxyWant[$upper]) {
            throw ('STOP: inherited proxy mismatch: ' + $key)
        }
    }
}
$env:OLLAMA_NO_CLOUD = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:VF064_REPO = $Repo
$env:VF064_INPUT = $InputDir
$env:VF064_EVIDENCE = $Evidence
$env:VF064_MODEL = $Model
$probe = @'
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(os.environ["VF064_REPO"]) / "scripts"))
from office_v2_crewai.runner import apply_telemetry
from office_v2_crewai.preflight import evaluate
from office_v2_crewai.contract import SANDBOX_ROOT
try:
    # Two-argument call matches the merged runner. Re-verify against the staged commit.
    env = apply_telemetry(dict(os.environ), SANDBOX_ROOT)
    result = evaluate(Path(os.environ["VF064_INPUT"]),
                      Path(os.environ["VF064_EVIDENCE"]), env,
                      Path(os.environ["VF064_MODEL"]))
    print(json.dumps(result, sort_keys=True, indent=2))
    sys.exit(0 if result["ok"] else 2)
except Exception as exc:
    print("PREFLIGHT_EXCEPTION: " + str(exc))
    sys.exit(2)
'@
# -I matches the merged runner. This probe is not the final isolation gate.
& $Py -I -B -c $probe | Tee-Object -FilePath (Join-Path $ReceiptRoot 'crewai064-preflight.txt')
$preflightExit = $LASTEXITCODE
if ($preflightExit -ne 0) { throw 'STOP: E1-E7 or model config refused' }
~~~

**Expect:** JSON with exactly E1-E7 **PASS**, model_status **CONFIG_ACCEPTED_NO_CALL**, missing_gates empty, model_calls **0** and ok true. Nonzero/exception means STOP and preserve printed per-gate reasons. Before the probe, a present non-empty `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, or `NO_PROXY` (any case spelling) that is not the exact tripwire is **STOP**. The runner refuses that value (`E5_PROXY_MISMATCH`) and does not overwrite it. The tripwire is `http://127.0.0.1:9` for the three proxy variables and `127.0.0.1` for `NO_PROXY`. Absent proxy names may be filled later. `PYTHONPATH`, `PYTHONHOME`, and `PYTHONUSERBASE` in the process are **STOP** before the probe. The committed fixture has 20 rows, including 8 synthetic count rows, so this file's E6 count check passes. That is not a live public snapshot, and real E4/E5 enforcement is not supplied by this command. This is deliberately read-only to CrewAI (it does **not** import crewai or call any model); it **still** executes Windows Python and therefore must not be run until E4's zero-C: containment is enforced. E1-E7 PASS is necessary but not sufficient while the section 0 NEEDS_CHRISTIAN items remain open. **This probe is not the final isolation gate.** `evaluate()` does not call `assert_interpreter_isolated`. `runner.execute` does that real check and refuses a process that was not started with `python -I`. A probe `ok: true` can still be followed by `PYTHON_ISOLATION_REFUSED`. That code, with `PYTHONHOME_REFUSED`, `PYTHONUSERBASE_REFUSED`, `USERCUSTOMIZE_REFUSED`, and `PTH_REFUSED`, is in the section 2 table.

### 1.4 Future admitted invocation with the Windows E5 collector (NOT authorized yet)

**STOP HERE** if any gate or NEEDS_CHRISTIAN item is unresolved. The following exact PowerShell 5.1 syntax is the *reviewed command interface*. It is not an attended-run authorization and it is not a GO. The E5 stage root and the E4 sandbox root stay where they are. Never invoke the runner directly or use synthetic gates to skip the collector.

~~~powershell
$Attempt = Join-Path $P ('crew\runs\crewai064-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $Attempt -ErrorAction Stop | Out-Null
# --sandbox is on the merged runner. Re-verify this argument against the staged commit.
# -I must precede the runner script. E5 PilotArguments does not insert it.
$RunnerArgs = ('-I "{0}" --input "{1}" --output "{2}" --evidence "{3}" --model-config "{4}" --sandbox "{5}"' -f $Runner,$InputDir,$Attempt,$Evidence,$Model,$Sandbox)
$Collect = @{
    PilotExecutable = $Py
    PilotArguments = $RunnerArgs
    # Exact stage-root equality is admitted. $P has no trailing slash.
    WorkingDirectory = $P
    ValidatorPython = $Py
    ValidatorScript = $Validator
    EvidencePath = (Join-Path $Attempt 'e5-snapshots.json')
    ReceiptPath = (Join-Path $Attempt 'e5-receipt.json')
    SampleIntervalMs = 250
    MaxSeconds = 600
}
& $Collector @Collect
$collectorExit = $LASTEXITCODE
foreach ($name in @('e5-receipt.json','attempt-receipt.json','postflight-receipt.json')) {
    $receiptPath = Join-Path $Attempt $name
    if (-not (Test-Path -LiteralPath $receiptPath -PathType Leaf)) {
        throw ('STOP: receipt absent: ' + $name)
    }
    Get-Content -LiteralPath $receiptPath -Raw
}
if ($collectorExit -ne 0) { throw 'STOP: E5 collector/runner unsuccessful; examine receipts' }
~~~

**Expect after the still-open NEEDS_CHRISTIAN items are closed by a recorded owner decision:** uniquely named D: attempt directory, E5 before/during/after process-tree TCP+UDP snapshots within **600 seconds** (the in-process socket timeout and a sampled stop are not the open 600-second external watchdog), E5 SHA-bound receipt, and reviewed-runner attempt-receipt.json and postflight-receipt.json under `$Attempt`. The canonical kickoff file is **D:\Velvet\Pilots\crewai-e4\sandbox-home\crewai-output\kickoff.md**, not a file under `$Attempt`. Receipts record that path and its SHA-256. Preserve and hash it there. The runner never autonomously marks the task PASS: a completed kickoff stays **NOT_VERIFIED / AWAITING_INDEPENDENT_REVIEW** and returns exit **0**. Exit 0 is not a reviewer PASS. Preflight refusals, failed guards, and exceptions return **2**, and E5 then records **PILOT_EXIT_NOT_ZERO**. Do not accept a nonzero exit as a workaround. #797 may also conservatively FAIL on an ordinary exit; that remains FAIL. Preserve both separate verdicts; never relabel a FAIL as PASS or treat a failed command as permission to rerun. **PASS_SAMPLED_NOT_ENFORCEMENT** is *not* effective OS network prevention or an E5 GO.

## 2. Interpret every FAIL/BLOCKED: runner and preflight

Read **identity.gates**, **identity.gate_reasons**, **identity.model_status**, **identity.reason**, **execution.abort_reason**, **result.status** and **teardown** together from attempt-receipt.json. A top-level reason alone can hide several failed gates. Code families below are **literal values from preflight.py, provider.py, sandbox.py, usage_guard.py, crew_build.py, kill_harness.py, e4_evidence.py, receipt.py on the merged runner (PR #799, `f3dd4e4c`) and current main**. A suffix after colon identifies the failed environment key/path; a trailing star identifies a generated reason family. Do not assume these static descriptions grant runtime authority.

**Action legend:** **STOP** = no model/retry, retain all D: receipts and ask owner/security reviewer; **REVIEW** = have the responsible owner correct a code/evidence defect in a separately approved/reviewed change and obtain new GO, never improvise on Chris; **REPORT** = independent review of ambiguous normal-exit or unexpected exception; **RETRY** = presently not permitted (section 4).

### E1-E7 preflight reasons

| Reason code(s) | Meaning; response |
| --- | --- |
| E1: AUTHORIZATION_EVIDENCE_ABSENT; AUTHORIZATION_FIELDS_ABSENT; OWNER_GO_ABSENT | Missing named task-run approval/fields/merged docs. **STOP; Christian approves separately.** |
| E2: CAPACITY_EVIDENCE_ABSENT; LEASE_OBSERVATION_ABSENT; CAPACITY_FLAG_ABSENT | Fresh Chris lease, no-worktree-conflict or Fleet/Cua separation unproven. **STOP; coordinator resolves conflict.** |
| E3: LOCK_EVIDENCE_ABSENT; LOCK_IDENTITY_MISMATCH; SCAN_NOT_THE_RECORDED_RED_RESULT | Conditional 154-wheel exact lock/RED scan absent or changed. **STOP; security reviewer.** |
| E3: SECURITY_DECISION_ABSENT; SECURITY_DECISION_NOT_ACCEPTED; SECURITY_DECISION_LOCK_MISMATCH; SECURITY_DECISION_ADVISORIES_INCOMPLETE; SECURITY_DECISION_IDENTITY_ABSENT; SECURITY_DECISION_BASIS_MISMATCH | Recorded owner risk decision, advisory set, lock SHA or provenance mismatch. **STOP; do not silently upgrade packages.** |
| E3: SECURITY_DECISION_CONDITIONS_ABSENT; SECURITY_DECISION_CONDITION_*; CONDITIONS_NOT_ENFORCED | Required no-tools/no-memory/no-MCP conditions absent/mutated/not enforced. **STOP; independent security REVIEW.** |
| E4: CONTAINMENT_EVIDENCE_ABSENT; CONTAINMENT_SCHEMA_REFUSED; CONTAINMENT_NOT_OBSERVED; CONTAINMENT_COMMENT_MISMATCH; LOCALAPPDATA_REDIRECT_REFUSED | E4 index/observed containment provenance absent/invalid; LocalAppData env redirection is not OS isolation. **STOP; security REVIEW.** |
| E4: MANIFEST_BEFORE_ABSENT; MANIFEST_AFTER_ABSENT; MANIFEST_NOT_OBSERVED; MANIFEST_SCHEMA_REFUSED; MANIFEST_PROFILE_SOURCE_REFUSED; MANIFEST_PATH_MISSING | Required before/after profile path inventory, observation, schema or real Windows profile source unproved. **STOP.** |
| E4: MANIFEST_CREWAI_PROFILE_WRITE; MANIFEST_TOKEN_CREDENTIALS_WRITE; MANIFEST_CHANGED | Unauthorized CrewAI credentials/profile/state or unexpected manifest mutation. **STOP, preserve C: evidence; security REVIEW.** |
| E4: CONTROL_RUN_ABSENT; CONTROL_RUN_STARTED_PILOT; CONTROL_DURATION_MISMATCH; CONTROL_ALLOWLIST_UNFIXED; CONTROL_NOISE_OVERLAP | No-pilot control absent/not comparable, or noise overlaps candidate writes. **STOP; independently reconstruct audit.** |
| E4: HKCU_BEFORE_ABSENT; HKCU_AFTER_ABSENT; HKCU_DIFF_ABSENT; HKCU_NOT_OBSERVED; HKCU_EXPORT_MISMATCH; HKCU_DIFF_NONEMPTY | HKCU snapshots absent/invalid/different; cannot prove registry containment. **STOP.** |
| E4: POSITIVE_CONTROL_ABSENT; POSITIVE_EXIT_NONEMPTY; POSITIVE_DB_ABSENT; POSITIVE_LOCK_ABSENT; POSITIVE_DB_NOT_ON_D; POSITIVE_LOCK_NOT_IN_TMP | Pilot storage positive control did not produce safe D:-local DB/lock with clean exit. **STOP.** |
| E5: NETWORK_EVIDENCE_ABSENT; NETWORK_FLAG_ABSENT; PILOT_LISTENER_PRESENT; PAID_CREDENTIAL_INHERITED; OLLAMA_HOST_REFUSED; LLM_ENDPOINT_MISMATCH | Network policy/listener, credential or endpoint assertion missing or violated. **STOP; security REVIEW.** |
| E5: E5_PROXY_ABSENT[:name]; E5_PROXY_MISMATCH:name | Dead proxy on 127.0.0.1:9 or NO_PROXY=127.0.0.1 absent or altered. **STOP; resolve inherited conflict in reviewed environment.** |
| E6: MANIFEST_ABSENT; MANIFEST_FILES_ABSENT; MANIFEST_ROW_INVALID; MANIFEST_NAME_REFUSED; MANIFEST_TARGET_ABSENT; MANIFEST_HASH_MISMATCH; PRIVATE_REPO_MATERIAL | Offline SHA manifest absent/unsafe/tampered or contains private-factory material. **STOP; independently review, redact, rehash.** |
| E6: FIXTURE_FILE_ABSENT; ISSUE_LIST_ABSENT; ISSUE_ROW_INVALID; ISSUE_NOT_OPEN; ISSUE_URL_REFUSED; ISSUE_NUMBER_ABSENT; REQUIRED_ISSUE_ABSENT; INSUFFICIENT_OPEN_ISSUES | Export missing, non-public, not genuinely open, missing #612/#595 or fewer than 20. **STOP; curate real reviewed public rows, no synthetic IDs.** |
| E6: ANSWER_SHEET_INCOMPLETE; ADVERSARIAL_FIXTURE_ABSENT; LIVE_FETCH_NOT_DENIED | 20-fact answer reference/negative fixture or offline-only declaration absent. **STOP.** |
| E7: GUARDRAIL_EVIDENCE_ABSENT; TIMEOUT_OR_COST_CAP_ABSENT; GUARDRAIL_FLAG_ABSENT; TELEMETRY_FLAG_ABSENT | Missing 600 s deadline, zero cost, kill/baseline/sink or pre-import telemetry controls. **STOP.** |

### Overall status, runtime refusals and FAIL codes

| Code(s) | Meaning; response |
| --- | --- |
| NOT_AUTHORIZED; PARKED_CAPACITY; BLOCKED_SECURITY; BLOCKED_STORAGE; NO_GO | Gate states that forbid starting; security/storage/capacity/owner action respectively. **STOP**. The E3 security scan remains RED even when a *condition-specific* risk decision exists. |
| NOT_RUN; PREFLIGHT_CLOSED; PREFLIGHT_REFUSED; MODEL_CONFIG_REFUSED | Refused before task; inspect gate_reasons **and** identity.model_status. **STOP/REVIEW**, not retry. |
| NOT_VERIFIED; AWAITING_INDEPENDENT_REVIEW | Input/task may finish but has no independent result verdict. **REPORT** to reviewer; never translate to PASS. |
| FAIL; PILOT_LISTENER_UNPROVEN | Post-kickoff or observation exception; inability to prove no pilot listeners. #799 addresses one PS5.1 .ToArray() bug but other observation failures can exist. **STOP/REPORT**. |
| MODEL_DIGEST_MISMATCH | Wrong/absent/duplicated model tag digest from **/api/tags**. **STOP**; never substitute model or LAB-4 shim. |
| OLLAMA_BIND_UNPROVEN; OLLAMA_BIND_WILDCARD | Real server bind evidence absent or address includes 0.0.0.0/::/LAN. **STOP**. A missing or unparseable English netstat observation is still **OLLAMA_BIND_UNPROVEN**. `binds=None` is not always that code: the provider collects netstat itself. |
| PILOT_LISTENER_PRESENT; FORBIDDEN_MODULE_LOADED; CHROMA_CLI_REFUSED | Pilot-owned listening socket, prohibited loaded chromadb.server/fastapi/uvicorn/mcp/drift module, or forbidden chroma CLI. **STOP; security incident REVIEW**. Importing the chromadb base module alone is not disallowed. |
| BLOCKED_SECURITY (installed package); SUPPLY_CHAIN_RECORD_INVALID; MCP_59951_NOT_RED; PYSEC_CVE_MAP_MISMATCH; FASTAPI_NOT_RECORDED; CREWAI_TOOLS_CVE_NOT_NA; MCP_ADVISORY_STATUS_MISMATCH; ZDI_26_706_RECORD_ABSENT | Prohibited installed litellm/tiktoken/posthog/crewai_tools/fastapi, or supply-chain/advisory mapping inconsistent with exact owner-accepted lock. **STOP; security REVIEW.** |
| MEMORY_NOT_DISABLED; KNOWLEDGE_OR_RAG_REFUSED; TOOLS_NOT_EMPTY; TOOLS_REFUSED; MCP_SERVERS_REFUSED; CREWAI_TOOLS_REFUSED; FROM_REPOSITORY_REFUSED; CREW_SHAPE_REFUSED; TRACING_NOT_DISABLED | Built agents/Crew violate no-memory/no-knowledge/no-tools/no-MCP/no-repository/no-tracing, including dangerous from_repository. **STOP; never enable code execution.** |
| TRACE_CONSENT_ABSENT; TRACE_CONSENT_TRUE; TRACE_CONSENT_CHANGED; LEFTOVER_FILE:path | Preseeded opt-out changed or unexpected CrewAI/chroma settings/telemetry artifact remains. **STOP; preserve audit evidence.** |
| PYTHON_ISOLATION_REFUSED; PYTHONPATH_REFUSED; PYTHONHOME_REFUSED; PYTHONUSERBASE_REFUSED; SITECUSTOMIZE_REFUSED; USERCUSTOMIZE_REFUSED; PTH_REFUSED; SANDBOX_DOTENV_PRESENT; FORBIDDEN_ENV:name | The process was not started as `python -I`, or an import hook, config, secret, or cache override may alter behavior before import. All of these **STOP before the model call.** |
| SANDBOX_ENV_ABSENT[:name]; SANDBOX_NOT_ON_D:name; SANDBOX_OUTSIDE_ROOT:name; SANDBOX_OUTSIDE_ROOT:ROOT; SANDBOX_OUTSIDE_VELVET; SANDBOX_PATH_MISMATCH:name; SANDBOX_VALUE_MISMATCH:name | Env/path/value missing, outside D: or not the exact approved sandbox. **STOP; no path relaxation.** |
| SANDBOX_CWD_ABSENT; SANDBOX_CWD_NOT_ON_D; SANDBOX_CWD_OUTSIDE_ROOT; SANDBOX_USERPROFILE_OUTSIDE_ROOT; SANDBOX_HOME_OUTSIDE_ROOT; SANDBOX_TEMP_OUTSIDE_ROOT; SANDBOX_TEMP_ABSENT; WINDOWS_TEMP_CREWAI | Wrong CWD, Windows home/temp or 0-byte C:\Windows\Temp\crewai ADS host detected. **STOP; E4 C: investigation**. |
| E5_PROXY_ABSENT[:name]; E5_PROXY_MISMATCH:name; OLLAMA_HOST_REFUSED; OLLAMA_NO_CLOUD_ABSENT | Dead-proxy/host/cloud denial not proven. **STOP; no network fallback.** |
| MODEL_CONFIG_NOT_OBJECT; MODEL_CONFIG_SCHEMA; MODEL_CONFIG_UNREADABLE; MODEL_CONFIG_ABSENT; MODEL_APPROVAL_MISMATCH; MODEL_EVIDENCE_MISMATCH; MODEL_PROVIDER_REFUSED; MODEL_TAG_MISMATCH | Exact pinned model JSON unreadable/invalid/changed/unapproved. **STOP.** |
| MODEL_URL_MISSING; MODEL_URL_SCHEME_REFUSED; MODEL_URL_USERINFO_REFUSED; MODEL_URL_NOT_LOOPBACK; MODEL_URL_NOT_EXACT_APPROVAL; MODEL_URL_PATH_REFUSED; MODEL_URL_QUERY_REFUSED; LLM_BASE_URL_REFUSED; LLM_ENDPOINT_MISMATCH; LITELLM_ROUTE_REFUSED; MODEL_REDIRECT_REFUSED | Model URL not exact local http://127.0.0.1:11434 and /v1, port 11435, or the wrong adapter. **MODEL_REDIRECT_REFUSED:** the approved loopback HTTP client blocks 3xx and refuses a changed final URL. **STOP; no second request.** |
| REMOTE_API_REFUSED; PAID_API_REFUSED; API_KEY_REFUSED; PAID_PROVIDER_FIELD_REFUSED; PAID_CREDENTIAL_INHERITED | Forbidden paid/cloud API capability or inherited paid key. **STOP**; report names not secrets. |
| THINK_NOT_DISABLED; REASONING_EFFORT_REFUSED; TELEMETRY_FLAGS_NOT_SET_BEFORE_IMPORT; CREWAI_VERSION_MISMATCH | Frozen model flags, pre-import telemetry or CrewAI 1.15.28 identity mismatch. **STOP.** |
| MODEL_CALL_BEFORE_PREFLIGHT; MODEL_MESSAGE_REFUSED; LOCAL_MODEL_RESPONSE_UNUSABLE; KICKOFF_EMPTY_TABLE; KICKOFF_UNCITED_ROW | A premature call, malformed input/output, or empty kickoff. **KICKOFF_UNCITED_ROW** is checked after kickoff: the table lacks source issue URLs or cites a URL that is not in the input rows. **STOP**; do not treat that table as a reviewed result. No fabricated fact table. |
| COST_CEILING_NOT_ZERO; TIMEOUT_NOT_POSITIVE; ATTEMPT_TIMEOUT; SPAWN_ARGV_REFUSED; REFUSED_NOT_OWNED | Harness cost/clock/argv/kill ownership violation. **STOP**; never kill a PID not proven owned. |
| OUTPUT_DISCARDED; OUTPUT_NOT_ON_D; OUTPUT_HASH_MISMATCH; RUN_STATUS_NOT_RUN | Empty, off-D:, corrupt/unhashable output or impossible receipt transition. **STOP; preserve bytes.** |
| FAIL with TypeError/OSError/other Python exception-class name instead of stable reason | runner._fail_reason() emits exception class name for unknown failures. **STOP/REPORT exact head and sanitized traceback**; classification is an OPEN QUESTION. |

**Preflight status priority:** BLOCKED_SECURITY first, then BLOCKED_STORAGE, then PARKED_CAPACITY, then NOT_RUN; all-pass preflight still yields NOT_VERIFIED, never automatic PASS. A recorded overall reason of E1,E6 or PREFLIGHT_CLOSED is a *summary*; inspect each gate's reason.

## 3. E5 collector/validator reasons (a different receipt)

These are produced by **scripts/collect-crewai-e5-network.ps1** and **scripts/vf_office_v2_crewai_e5_network.py**, not runner.identity.reason. A failing E5 receipt means **STOP, preserve original snapshots and report to the independent reviewer**. Do not retry automatically, even if a normal exit seems likely. Every code below is fail-closed.

| Reason code(s) | Meaning |
| --- | --- |
| HOST_NOT_CHRIS; D_ABSOLUTE_PATH_REQUIRED; OUT_OF_PILOT_ROOT_PATH; INPUT_PATH_MISSING; OUTPUT_PARENT_MISSING; RECEIPT_DIRECTORY_MISSING; EVIDENCE_RECEIPT_COLLISION; REPARSE_POINT_REFUSED; OUTPUT_PATH_NOT_ADMITTED | Wrong host, absent/outside approved staged D: paths, reparse traversal, missing output directory or colliding files. Fix via separately reviewed staging, not a shortcut. |
| PROCESS_BIRTH_MISSING; ROOT_PID_BIRTH_MISMATCH; TRACKED_PID_REUSED; PROCESS_IDENTITY_CHANGED_DURING_SAMPLE | CIM birth identity absent, changed, reused or disappeared between snapshots. May conservatively fail on ordinary process exit (#797); **REPORT, do not override**. |
| PROCESS_TREE_TOO_LARGE; TREE_ROOT_MISSING; PROCESS_TREE_CYCLE; PROCESS_TREE_ORPHAN; CHILD_CREATED_BEFORE_PARENT | Cannot establish bounded PID/parent PID chain reaching verified root, or child birth time is impossible. STOP. |
| TCP_LISTENER_DETECTED; UNAPPROVED_TCP_REMOTE; UDP_ENDPOINT_DETECTED | Pilot-owned TCP listener (even loopback), TCP remote other than literal 127.0.0.1:11434 (11435 is refused), or UDP endpoint. STOP/security review. |
| MAX_RUNTIME_EXCEEDED; PROCESS_END_UNVERIFIED; OWNED_STOP_UNVERIFIED:pid; PILOT_EXIT_CODE_UNKNOWN; PILOT_EXIT_NOT_OBSERVED; PILOT_EXIT_CODE_UNAVAILABLE; AFTER_SNAPSHOT_FAILED:detail | Budget exceeded, owned-tree end not proved, null/unavailable exit code or final snapshot failed. STOP; never assume unknown ExitCode = 0. |
| INVALID_JSON; INVALID_EVIDENCE; INVALID_IDENTITY_OR_SCHEMA; INVALID_ROOT_PID; INVALID_SAMPLE_INTERVAL; INVALID_RUN_TIMES; INVALID_SNAPSHOT; INVALID_SNAPSHOT_TIME; OUT_OF_ORDER_SNAPSHOT; BEFORE_NOT_BEFORE_RUN; DURING_OUTSIDE_RUN; AFTER_NOT_AFTER_RUN; MISSING_SNAPSHOT; MISSING_DURING_SNAPSHOT | Validator cannot prove well-formed JSON, root, timestamps, sequence and all before/during/after phases. STOP. |
| INVALID_SNAPSHOT_SHAPE; INVALID_TREE_MEMBER; INVALID_TREE_ANCESTRY; PID_REUSED_OR_IDENTITY_CHANGED; ROOT_NOT_OBSERVED_DURING; PILOT_TREE_PRESENT_BEFORE_LAUNCH; PILOT_TREE_STILL_RUNNING | Invalid/foreign/orphan/cyclic tree, PID identity reuse, missing live root or lingering process. STOP. |
| INVALID_TCP_ROW; TCP_OWNER_NOT_IN_TREE; TCP_STATE_MISSING; TCP_LISTENER_DETECTED; UNAPPROVED_REMOTE_ENDPOINT; WRONG_OLLAMA_PORT; UDP_ENDPOINT_DETECTED; UDP_OWNER_NOT_IN_TREE | Invalid/foreign-owned socket, listener, wrong endpoint/port or any pilot-owned UDP. STOP. |
| COLLECTOR_INCOMPLETE; TIMEOUT_OR_UNKNOWN; PILOT_EXIT_NOT_ZERO | Collector errors, unbounded/incomplete timing, or a process exit other than integer 0. A completed unreviewed kickoff is exit 0. A refusal or exception is exit 2 and this code. Not an automatic safe retry. Exit 0 is not reviewer PASS. |

Only **PASS_SAMPLED_NOT_ENFORCEMENT** means all sampled observations were admitted. It does **not** establish effective deny-by-default firewall/WFP, complete ETW coverage, zero C: effects, reviewer PASS, or model/task success. Unexpected/new reason, malformed receipt or missing fields: **OPEN QUESTION / STOP / REPORT**, never guessed classification.

## 4. Maximum retry count, independent QA and stop point

**Maximum currently authorized retries: 0 (zero). NEEDS_CHRISTIAN (open owner decision).** This checklist does not grant any automatic or manual retry: at most one *separately authorized first attempt* once all prerequisites are independently PASS and the section 0 owner decisions are closed by a recorded decision. The code has no retry counter. Christian and the independent security reviewer must record a concrete finite cap and allowed failure classes on #612 *before* any later manual retry; require a fresh owner time window, E2 free lease, proof that the prior attempt ended and produced no forbidden effects, new immutable attempt ID, new E5/E4 baselines and cleanup. A #797 normal-exit false FAIL is still FAIL, not implied RETRY. This cap stays open.

**Immediate STOP** on any gate refusal, undisclosed or unproven process/identity, C: write or missing C: denial proof, reparse escape, unexpected listener/socket/egress/telemetry, credentials, tool, MCP or memory creation, manipulated prompt response, model/digest drift, missing hash, unreviewed code, CPU/RAM breach, 600 seconds, unknown exit, machine health problem or Christian/reviewer veto. E5 observer must only stop verified owned PIDs with matching creation time. Do not kill shared Ollama, Fleet, Cua, Windows helpers, other workers or production services. Any uncertainty is **RESTORE_REQUIRED / NOT_VERIFIED** until independently examined.

The [governing baseline](pilot-runbook-crewai.md#4-future-attended-operator-sequence--never-executed-by-this-pr) specifies a later independently reviewed scoring series (at least five attempts incl. cold and an adversarial check), 20 real supported issue IDs, zero fabricated issue facts, at least 90% on the 20-fact gold sample, and zero unauthorized effects. That evaluation target **is not a retry authorization** for this first run and is not satisfied by a model response.

## 5. Teardown, D: receipt retention and C: readback

- [ ] Confirm the E5 collector's before/during/after samples contain process-tree PID, PPID, UTC birth, run exit, owned-tree stop proof, zero pilot-owned listeners/forbidden remotes/UDP and no tracked descendants left. Confirm any Ollama listener is a **separate approved model process**; don't stop or alter it absent separate ownership. Failure => RESTORE_REQUIRED/NOT_VERIFIED.
- [ ] Preserve unmodified D: attempt-receipt.json, postflight-receipt.json, e5-snapshots.json, and e5-receipt.json under `$Attempt`. Preserve kickoff.md at its canonical path **D:\Velvet\Pilots\crewai-e4\sandbox-home\crewai-output\kickoff.md** (receipts store that path and its SHA-256). Also preserve the preflight result, E4 OS-level deny/monitor log, timestamps, before/after manifests and HKCU evidence. Hash source files, input, model/lock and evidence; do not erase evidence to clear FAIL.
- [ ] **Read-only C: spot checks after attempt (Windows PowerShell 5.1):**

~~~powershell
$CSpot = @(
  'C:\Windows\Temp\crewai',
  'C:\Windows\System32\config\systemprofile\AppData\Local\CrewAI',
  'C:\Windows\System32\config\systemprofile\AppData\Local\crewai',
  (Join-Path $env:USERPROFILE 'AppData\Local\CrewAI'),
  (Join-Path $env:USERPROFILE 'AppData\Local\crewai'),
  (Join-Path $env:USERPROFILE '.crewai'),
  (Join-Path $env:USERPROFILE '.promptfoo'),
  'C:\Users\Public\CrewAI'
)
$CSpot | ForEach-Object {
    [pscustomobject]@{ Path = $_; Exists = (Test-Path -LiteralPath $_) }
} | Tee-Object -FilePath (Join-Path $ReceiptRoot 'crewai064-c-spotcheck-after.txt')
foreach ($name in @('attempt-receipt.json','postflight-receipt.json',
                    'e5-snapshots.json','e5-receipt.json')) {
    $file = Join-Path $Attempt $name
    if (-not (Test-Path -LiteralPath $file)) { throw ('STOP: receipt missing: ' + $name) }
    Get-FileHash -Algorithm SHA256 -LiteralPath $file
}
~~~

**Expect:** compared with a complete **pre-run baseline**, no *new pilot-attributed* CrewAI files under these C: locations, and a complete independent audit of all pilot/OS-helper C: writes and denied attempts. LAB-4 reported a 0-byte **C:\Windows\Temp\crewai** (NTFS ADS lock host) and an older LAB-2 **SYSTEM profile credentials\secret.key**; #799 adds temp precreation and spot checks but this is not proof of full C: containment. If anything appears or baseline is missing, **STOP**, archive/attribute under security supervision. Never delete C: objects automatically or assume an old object is new. A green spot check is not E4 admission or OS-level enforcement.
- [ ] Revoke only approved pilot-specific session identity/capabilities/leases. After retention, remove only **manifest-owned** ephemeral D: scratch and temp (and only if owner approved); preserve source evidence, hashes, original immutable input and reviewed receipts. Unknown owner or remaining PID: quarantine without deletion. Verify no new scheduler, lingering pilot process, socket or unauthorized path.

## 6. Post the actual sanitized run receipt to #612

Create **a new issue comment on [#612](https://github.com/nocturney/velvetos-core/issues/612)** headed:

**RESULT (attended CrewAI Chris) - attempt [actual attempt ID]**

Include exact staged runner HEAD/SHA and source hashes; board-as-of timestamp with each E1-E7 evidence link, current E1 Christian GO/E2 lease URL and reviewer; host/Windows/PowerShell/Python identity; 154-wheel lock hash; local qwen3.5:9b digest from **/api/tags**; input/gold SHA; UTC start/end; root PID birth; observed runner exit and **separate** runner/E5 verdict; cost, model call count, SHA-256 of `D:\Velvet\Pilots\crewai-e4\sandbox-home\crewai-output\kickoff.md`; sanitized D: receipt and E4/E5 monitor SHA-256s; observed C: changes or absence with attribution/enforcement evidence; cleanup/remaining PIDs; remaining NEEDS_CHRISTIAN items (deny-by-default network, C: write denial, 600-second external watchdog, retries=0), next gate and independent QA verdict. Write **FAIL/BLOCKED/NOT_VERIFIED** if any part is uncertain; never self-certify PASS, never treat exit 0 as reviewer PASS, and never treat a nonzero exit as success. Do not expose keys, private issue text, user profiles, credentials, production data or unredacted system logs in the public repo.

**This docs-only PR neither runs a model nor changes a gate, policy, code, installation, host or GitHub worker. No merge requested from the author.**
