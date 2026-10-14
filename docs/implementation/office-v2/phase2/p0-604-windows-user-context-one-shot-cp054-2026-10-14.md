# Office 2.0 #604 — CP054 Windows interactive one-shot LAB

**Scope:** native user-session identity proof, not a signed Core lease, sandbox, agent, scheduler, production writer or model-code executor. Verified 2026-10-14.

## Concrete host finding

Remote Desktop Commander reaches Chris Windows as SYSTEM Session 0, while CHRIS\Chris is actively logged on to console Session 1. Prior Register-ScheduledTask calls with New-ScheduledTaskPrincipal failed (CimException UserId). The pre-existing task named OfficeV2 LAB Lease is a WSL OfficeV2-Lab keepalive, NOT the Core #604 signed lease. It was not run or modified.

Windows schtasks.exe /RU CHRIS\Chris /IT /RL LIMITED successfully launched a bounded one-shot, no-effect identity probe in the standard user token, then deleted its own temporary task. First native receipt SHA256 87eb712cabbe3e25bf3a1f2c82c1c8e1e112794946a7cfde657f7ed06732b699: user CHRIS\Chris, Session 1, is_system=false, elevated=false. Afterward task inventory confirmed absence.

Separate earlier local Ollama Qwen3.5:9b inference under that user process produced ONE synthetic non-executed propose_literal_fix function call (replacement return n * 2), 18.708s client wall, 34 generated tokens, 347 prompt tokens; receipt SHA256 4e2f4dd9f1538ce9b06304524615816e9c57e9177cc0b2983d62302d0f6347ca. The model was unloaded and temporary task was removed. This model experiment is NOT embedded in the committed probe and is NOT a coding agent.

## Versioned deliverables

Windows PowerShell: scripts/vf_office_v2_604_windows_user_session_probe.ps1. Source script SHA256 cda440c440dd17b2587ff776816b154824bf6309aa72a7e264d34cd6f1741bc7. For this precise lab it must be staged with the fixed execution filename D:\Velvet\Pilots\OfficeP0UserBridgeCP054-20261014\user-session-bridge.ps1 on the already-authorized Chris host. Controller rejects incorrect host, unpinned source, missing local account or existing task and refuses to mint any lease; Child refuses SYSTEM, elevation, wrong user/session, and performs only a one-shot local JSON receipt write. The Controller creates an Interactive/Limited Task Scheduler entry with a fresh attempt nonce, reads receipt, deletes task in finally and independently checks absence. No arbitrary code, GUI, model, Git provider or customer effect is exposed.

Actual Controller corrected for Windows 261-character /TR task command limit, source SHA above, PowerShell parse 0 errors. Direct -Mode Child under SYSTEM was DENIED and left no receipt. On the corrected Controller run the native Windows result was PASS_USER_CONTEXT_ONLY, attempt d2f68e52b1fc40ccb4b66610e8abff4d, user CHRIS\Chris, Session 1, normal token; receipt SHA256 c984f6e7eace76417386ef39b75280053e15cbc55debcc5b14886b79d1828baa, exit 0, TASK_REMOVED=true, no matching tasks remain. One earlier too-long /TR attempt created no task. Both are preserved as actual test outcomes.

Portable independent content checker: scripts/vf_office_v2_604_windows_user_session_receipt_check.py SHA256 0758379d05a34a85283a8815595d848387f32204318730a5ffbd3ac1b7039751. Python selftest: 21/21 tampered, malformed, missing, symlink, identity, privilege and scope denials PASS on MacMiniOffice (exit 0), no Windows API or external call. CLI: python3 scripts/vf_office_v2_604_windows_user_session_receipt_check.py --selftest. To inspect one actual receipt: add --receipt PATH --source-sha256 SOURCE_SHA --attempt ATTEMPT_ID. This independently validates content only; it never attests a Windows token or Core lease.

## Safety and limitations

Only one fixed, non-GUI and non-model Child identity probe is supported. The Controller must be invoked through the existing authorized Windows management channel and the target user must already be logged in; no password capture or privilege alteration. Do not add a permanent watcher or call this a low-privilege sandbox: a standard user still has access to user files and network.

Normal completion deletes the temporary scheduled task, but crash/power loss before finally could leave an inert future one-time task; durable orphan reconciliation is not proven. The receipt is not cryptographically authenticated and source SHA is not authorization. No Core-issued signed task/host/GPU lease, OS-isolated model code execution, Git credential custody, external-effect fencing, production deployment, continuous throughput or autonomous PR integration is claimed.

Next #604/#612 gate: use the sole Core lease authority to admit exactly one bounded user-host and isolated coding task; require generated diff in a protected worktree, independent hidden QA, fenced effect sink, protected PR/CI, crash UNKNOWN recovery and then genuinely independent second-host acceptance. Preserve existing Office P0 hourly automation; no Codex CLI or new paid inference.
