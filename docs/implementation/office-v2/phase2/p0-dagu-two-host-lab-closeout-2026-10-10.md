# Office 2.0 / #604 — recover and close the old Dagu 1/2/4 host LAB (2026-10-10)

**Status:** `HISTORICAL_13_OF_13_RAW_LOG_RECHECK_PASS` + `EXACT_IDLE_LAB_CLEANUP_VERIFIED`. **NOT** distributed lease/fencing, host-loss recovery, new provider authority or production rollout.

## Why this was needed

The existing, isolated `fleet-placement-20261008-1423z` Dagu 2.18.2 lab had accumulated independently gathered 2026-10-08 synthetic 1/2/4-host-placement and fairness data. The existing independent-audit receipt was explicitly `FAIL_CLOSED_CLEANUP_PENDING`; four Mac Dagu processes and a Windows worker remained alive on 2026-10-10 although all observed history was terminal. No new orchestrator, worktree owner or Dagu pilot was created for this closure.

## Independent evidence and fidelity

The new, **read-only** `scripts/vf_office_v2_604_dagu_raw_log_audit.py observe --lab-root <exact lab>` inspected the pre-existing, unchanged Mac-stored `manifest.json`, `groups-progress.json`, `fairness.json` and `independent-audit.json`, verified their four original SHA-256 hashes, then separately opened and hashed 13 actual Dagu stdout files under the original root. Each task's named worker, actual host identity (10 Mac / 3 Windows), start/end markers, correct payload SHA256 `d5d7a4ca0b3763074c62a08ba762c307ab2f986240bd9a267e3a4eed41783976` and postcondition agreed with historical readback.

| Scenario | Tasks checked | Verified peak concurrent tasks | Evidence limitation |
| --- | ---: | ---: | --- |
| solo | 1 Mac | 1 | one round only |
| dual | 1 Mac + 1 Windows | 2 | one round only |
| quad | 2 Mac + 2 Windows | 4 | one round only |
| fairness | 6 Mac, one worker slot | 1 | **4 FIFO dispatch inversions** observed |

Historical end-to-end p50 / interpolated p95 (seconds): solo 7.749 / 7.749 (n=1), dual 9.624 / 9.724 (n=2), quad 13.403 / 14.207 (n=4). **None is a statistically meaningful p95, throughput SLA or 1-to-2-to-4 agent-coding comparison.** The fairness observer reported queue p50 ~11.383s and p95 ~21.51s for six tiny synthetic jobs; real FIFO is *not established*.

Sanitized independent evidence: `p0-dagu-two-host-13-run-forensic-audit-2026-10-10.json` (13 pinned stdout hashes). Original raw stdout and run records stay in the pre-existing Mac lab, not in Git. The new verifier's `verify` and `selftest` are **strictly offline**; 18/18 cases include fake lease/authority/cancellation, producer hash, concurrency, physical host, non-FIFO and tamper denials.

## Live idle cleanup, not an invented cancellation proof

Before stopping anything: Dagu native `ps` returned `[]`; coordinator `history` contained **14/14 terminal Succeeded** records, zero nonterminal, synthetic-only DAG definitions, and no nonlock active/queue records. Exact process command lines and 2026-10-08 births were rechecked. Only one Dagu process existed in the Windows pilot root, and only four Dagu processes existed in the named Mac pilot root.

- Windows: exact owned synthetic Dagu worker PID **49084**, checked `vf604-win-1423z`, was stopped with `Stop-Process` while idle. This was an explicit process termination, **not** a graceful in-flight checkpoint.
- Mac: exact owned workers **14840**, **15073**, **15248** received SIGTERM; after their absence was verified, the exact synthetic coordinator **14782** received SIGTERM.
- Afterward, both hosts separately saw all five exact PIDs absent; Mac saw **zero** listeners on synthetic UI 31810 and gRPC coordinator 31557, while Windows independently failed to connect to the former coordinator's exact port. Mac original four data-file hashes were independently read back unchanged. Windows Maya PID 24392 and Ollama PID 43272 remained running. The current production Fleet services were never touched.

**Discovery during read-only diagnostics:** invoking `dagu ps` for a previously uninitialized DAGU_HOME automatically created six example DAG files in each of two directories (the Windows user default and isolated Windows Dagu worker home). Before removing them, their full six-file allowlist, exact byte sizes, directories and creation times at 11:16 UTC were verified; both newly created directories were precisely cleaned with post-readback, without deleting project data. The diagnostic command must not be treated as a truly side-effect-free first invocation of Dagu.

Scoped shutdown receipt: `p0-dagu-fleet-idle-cleanup-2026-10-10.json`. `scripts/vf_office_v2_604_dagu_cleanup_gate.py` checks this receipt in offline CI (21/21 negative/positive tests). CI does **not** signal any processes or contact either host. Historical hashes and the cleanup receipt are operator observed and self-hashed, **not** independent cryptographic signatures.

## Hard boundaries and next acceptance gates

This closes the specific old #604 **cleanup debt** and captures previously unmerged historical fleet evidence. It does **not** choose Dagu as the production winner, verify loss/recovery or cancellation, issue/renew/revoke a canonical worker lease, atomically enforce monotonic fencing at external Git/artifact effects, prove two physical GitHub writers, establish exact model usage, or authorize an auto-retry of preserved UNKNOWN tasks.

#604 alone owns provider selection and cross-host lease/fencing. #612 remains the consumer-side Task Envelope, model agent, QA and PR authority lane. **Next real #604 challenge:** compare the established Dagu synthetic fixture with ready-made Restate/Nomad alternatives in separate bounded slots; require a single chosen provider's actual atomic ownership/fence at each effect boundary and negative tests for partition, stale-owner wakeup, loss/rejoin. Mac native Git write credentials remain separately unverified: do not copy/share tokens or claim a physical Mac Git writer without explicit host authorization. No new service/daemon, scheduler, production writer, paid inference, customer/social/printer effect or system configuration change was introduced.

Reproduce only offline, from a clean repo: `python scripts/vf_office_v2_604_dagu_raw_log_audit.py verify`, `selftest`; `python scripts/vf_office_v2_604_dagu_cleanup_gate.py verify`, `selftest`.
