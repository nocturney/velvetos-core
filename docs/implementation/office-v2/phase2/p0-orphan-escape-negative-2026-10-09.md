# Office 2.0 #612 — detached descendant false-negative proof (2026-10-09)

**Status:** REAL_MAC_POSIX_ESCAPE_OBSERVED / NO_ORPHAN_EXCLUSION / NO_AUTOMATIC_RETRY / LAB_ONLY.

This is a narrow *negative* safety test for local Aider crash recovery. It does **not** launch Aider/Ollama, run a scheduler, assert there are no remaining descendants, authorize a new task, or touch any business/printer/social application.

## Actual original-process-group escape

In a newly created, isolated Mac LAB directory `OrphanEscapeLab/20261009-a`, a one-shot Python controller started a fixture owner with `start_new_session=True`. The owner recorded native OS kernel birth metadata for itself and its newly spawned child, which also entered **a separate POSIX session and process group**. The parent then exited naturally; the child remained alive briefly and was identified by the **same pid + birth microsecond** as at spawn.

The existing canonical `vf_office_v2_p0_kernel_identity.group_members` scan observed **zero members** of the original owner's group, **while that same-birth detached child was still running**. The sampled historical original group had group ID `20828`; escaped child PID `20829` had distinct group ID `20829` and was observed reparented (PPID `1`). The detached child was instructed to exit via this temporary fixture's own stop marker (no signals); a subsequent OS `ps` check found no such PID. There was no manipulation of user or Office processes.

| Property | Direct readback |
| --- | --- |
| Original group | `20828` |
| Escaped child group | `20829` |
| Native child birth timestamp (µs) | `1791553224398994` |
| Group scan | `NO_GROUP_MEMBERS_SEEN`, candidate count `0` |
| Escaped same-birth child alive at scan | `true` |
| All orphan descendants excluded | `false` |
| Original task retry authorized | `false` |
| Receipt SHA-256 self-seal | `6b69eadd2b20bc25e5f73d257f8a8f671fee1a2b9219d2a92cfca7de690f5ff8` |

The raw Mac record is tracked as `p0-orphan-escape-negative-2026-10-09.json`, validated with the standalone pure `verify --evidence` code; an exact copy passed **independent Windows verification** with the same selfhash. The identical Python source Git object `f410a3c51202636103074f5892c76aaddc3d0f2b` and SHA-256 `341b63b2732b2ea7d30e7e603dae6b01e7d09d1311b2181346822d1e262013af` was independently confirmed on Windows and Mac. `selftest` returned **16/16 PASS** on both machines, including 12 intentionally re-sealed false claims and a corrupted selfhash. The historical receipt's selfhash is **not an asymmetric signature** or a completeness guarantee.

## Permanent CI contract

`scripts/check-office-v2-contracts.py` executes **only** `selftest` and `verify --evidence` on the checked-in result. Those paths are pure offline: zero subprocesses launched by the fixture, zero model calls, no runtime process scans, no changes to scheduler/leases/production. The `live` mode is **manual-only** and, in this version, POSIX-only; Windows fails closed pending a separately proven native Job Object container.

The correct engineering consequence is stronger **supervised process containment / recorded descendant lineage** before any unattended new-attempt creation. A PID or empty process group by itself cannot prove no escapees; no source file or receipt here authorizes a retry. #604 still owns fleet placement and scheduler selection. #612 owns local coding worker reliability. Cross-host auto-recovery, inherited resource containment, Windows Job Object, p50/p95 and production authority remain **UNPROVEN**.
