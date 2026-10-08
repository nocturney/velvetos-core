# P0 agent-task envelope + worker receipt — offline protocol v0 (2026-10-08)

Canonical owner: [Office Infrastructure Accelerator #612](https://github.com/nocturney/velvetos-core/issues/612).
Fleet scheduling, concurrency and worker placement remain owned by [#604](https://github.com/nocturney/velvetos-core/issues/604). This file does not instantiate a scheduler or independent authority.

## Scope of the implemented proof

`scripts/vf_office_v2_p0_worker.py` implements three commands: `selftest`, `run --envelope PATH --receipt PATH`, and `verify --envelope PATH --receipt PATH`. The worker executes **only a previously reviewed, Git-tracked, SHA-256-pinned Python fixture** with `subprocess.run` (no shell). The process is not a security sandbox; run it only in a dedicated nonproduction checkout with no credentials or customer data. It **does not invoke any model, autonomous coding agent, API, Dagu coordinator, WSL or production service**.

Task envelopes (schema `velvetos.office-v2.p0-task-envelope.v0`) bind a canonical issue URL, task ID, SHA-40 baseline, exact branch, isolated checkout path, actual host name, LAB authority, bounded timeout / one attempt / zero spend, pinned executor/script/args, exact allowed artifact paths and a sealed Project State checkpoint **outside** the mutable repo. The checkpoint must pass the existing `vf_office_v2_continuity.py` validation, match the exact branch/base/repo/worktree, and contain no active external effects.

A successful run writes a **separate** receipt (schema `velvetos.office-v2.p0-worker-receipt.v0`) with normalized envelope SHA-256, host/base/branch, timestamps, elapsed milliseconds, exit code, output hashes, exact changed-file hashes, before/after checkpoint file hashes, compacted sealed checkpoint and full-receipt content hash. `verify` independently reopens the envelope, receipt, changed files and checkpoints, re-hashes the data, checks exact paths and Git state and runs the existing continuity verifier.

Durability rule: a `.running` journal is persisted *before* launching code, and no invocation automatically overrides either an existing receipt or an orphan RUNNING marker. A crash after effects and before receipt produces **UNKNOWN**, not automatic idempotent success or blind retry. A nonzero or timed-out executor is never reported as success. Exactly-once external effects are **not** proven.

## Evidence and acceptance

`python3 scripts/vf_office_v2_p0_worker.py selftest`

This runs one real isolated local Python process plus independent receipt readback and negative controls for duplicate execution, tampered output, stale baseline, wrong host, unauthorized spending, unapproved agent (including Codex), path traversal, invalid context checkpoint and orphan journal. It uses a disposable local Git fixture and adds no paid calls. `check-office-v2-contracts.py` now invokes the selftest via the existing registered sensor; the new script is owned/triggered by that sensor. The output must explicitly retain `autonomous_coding_agent_proven=false`, `worker_fleet_proven=false`, `model_invocations=0`, `additional_spend_usd=0`.

Next mandatory gates **not satisfied by this offline proof**: verified zero-incremental-spend genuine code-capable model/executor, two different physical hosts producing *real* distinct coding changes, independent postconditions, protected PR/CI and merge, restart/failover across host/process boundary, 1-vs-2 worker baseline and time/resource/reliability measures. The P0 automation and #604 fleet watch retain separate ownership.

## Recovery

An orphan `.running` file or a failed receipt is a review-needed terminal outcome: inspect live process/side effects, compare Git/artifact hashes and checkpoints, then create a new explicitly approved task ID/attempt only after outcome reconciliation. Never delete journal to blindly rerun. No user desktop/WSL/Dagu service is changed by this contract.

## Owner constraints

No Codex CLI; no assumption that ChatGPT entitlement includes paid inference; no production writer, customer communications, social publication, printer actions, credentials, reboot, global WSL changes, or unauthorized machine effects. GitHub #612 is the execution owner, not a second queue.