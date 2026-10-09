# Office v2 P0 — Two-host local exclusive-claim + owner-loss LAB

**Date:** 2026-10-09 | **Issue:** [#612](https://github.com/nocturney/velvetos-core/issues/612) | **Scope:** dedicated synthetic local process/file experiment only

## Why this is needed

A canonical Task Envelope, a clean Git worktree and a retained `RUNNING` journal are **not** mutually-exclusive process ownership. Two contenders can pass separate preflights before either records execution. A process disappearing must also not be used to automatically requeue an ambiguous task. We therefore tested the smallest real primitive on **both connected hosts**, without adding another scheduler or overriding #604.

## Actual two-host OS experiments

A freshly-created, owned scratch directory on each physical host was used solely by the new script `scripts/vf_office_v2_p0_local_singleflight_lab.py`:

1. Start **two different child processes concurrently**; both independently capture native OS PID + creation-time identity (`kernel_identity.sample`), signal readiness, and wait for one release flag.
2. Both attempt `os.open(..., O_CREAT|O_EXCL)` for the *same local reservation path*. Exactly **one** wins and writes a self-hashed, scoped LAB-only claim. The other receives `FileExistsError` and emits `DENIED_ALREADY_CLAIMED` without altering the claim.
3. Confirm the winner is still alive and matches its claimed kernel process creation identity; terminate **only the child process directly spawned by this LAB**, through its `Popen` handle. No process-name or global kill.
4. Start a **third** new child process after the owned winner has exited. It must receive `DENIED_ALREADY_CLAIMED`. The original reservation bytes must remain identical. No automatic TTL unlock, retry, orphan cleanup or replay.
5. Independently re-read the local original claim, all three contender results and historical receipt, ensuring one winner, two denials, source-attached receipt integrity and `new_job_execution_authorized=false`.

| Readback | Chris Windows | MacMiniOffice.local |
|---|---|---|
| Executed code commit | `5466f6d24382dcf6d724401cc3842bacdcff0b10` | Same Git commit |
| PID of winner (historical) | `17240` | `55024` |
| OS birth backend | `WINDOWS_CIM_CREATION_DATE` | `PSUTIL_OS_CREATE_TIME` |
| One winner, concurrent loser denied, post-loss contender denied | **PASS** | **PASS** |
| Wall time (bounded fixture, not coding) | 1577 ms | 1291 ms |
| Offline negative checks | **25/25** | **25/25** |
| Raw local reservation SHA256 | `840a442f8e47dc5aa12244b0c56d9fc2ef64f81c00b437e525f8fc3dda75e25c` | `5b7112d32e4c5e4ef03a831e6a29a0822803320304ad36610319c7e10a8a5b8c` |
| Self-hashed OS experiment receipt | `e4ca551d64d8284fc1848fc37aaf995fd5368576901cdccf832a70517354d65d` | `4103291fc75701fe75bf9784e1c72e1d2d07a9468223b9ee8f3a5e08d06002f8` |

The exact, sanitized historical report/claim objects are in `p0-two-host-local-singleflight-loss-2026-10-09.json`. Raw probe directories remain separate from Git under their own `p0-singleflight-probe-{win,mac}-20261009-a` lab roots. The records' self-hashes protect against accidental modification, **not** against deliberate re-sealing or external forgery.

The original source script is pinned to commit `5466f6d24382dcf6d724401cc3842bacdcff0b10`; Git blob `2526682600bb2b99b7bf4792bab091658c297607`; LF file SHA256 `c02e1374ad2a6775baef8c1231f0662932c0fb72d768188ae8666911e0826b8c`.

## Key limits and next gate

This is **local filesystem atomic exclusion** on *two entirely separate physical hosts*. It does not coordinate those hosts, and it is **not a distributed lease, epoch, fencing token, TTL policy, process sandbox or production runtime**. Lost process ownership remains UNKNOWN for real work until independently reconciled; a persisted local reservation requires human disposition rather than silent deletion. No actual coding worker, Ollama, provider, PR or customer action was invoked by this fixture.

The future real worker admission must coordinate through the **canonical #604 placement/lease authority** (not implemented/proven as a live cross-host lease here), with monotonic fencing checked by the external-effect receiver, plus existing #612 Task Envelope/Project State/Worker Receipt/independent QA. The single-host reservation can be used later **only after** formal integration and tests on true worker tasks, never automatically inferred from this LAB.

CI runs only `selftest` and source/receipt validation. It **never** launches the live contender fixture, kills OS processes, requeues UNKNOWN, starts a model or changes production. `new_job_execution_authorized=false`, `canonical_fleet_lease=false`, `distributed_fencing_verified=false`, `autonomous_recovery_proven=false`, `all_orphan_descendants_excluded=false`; no Codex CLI, subscriptions, paid model/API calls or customer/social/printer/system settings changes.
