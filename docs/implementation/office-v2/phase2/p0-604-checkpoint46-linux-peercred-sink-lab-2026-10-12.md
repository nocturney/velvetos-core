# Office 2.0 / #604 — Checkpoint 46: Linux kernel peer-credential synthetic sink LAB

**Date:** 2026-10-12 (Asia/Jerusalem)  
**Scope:** ephemeral ChatGPT Linux container; **NOT** any of the owner's six computers  
**Status:** SYNTHETIC LAB ONLY / no production admission / no external effect  
**Baseline:** Checkpoint 45 design (draft PR #705, main previously verified at `1fb06173a6af7ad7242a751f5853a4133170b2ce`).

## Purpose / genuine new delta

The existing #604 local Git, SQLite, etcd and Dagu tests already cover separate parts of intent replay, stale remote SHA, UID501 weaknesses and missed cancellation. They **do not** prove OS-principal custody of an effect sink. This new tiny experiment exercises actual Linux kernel `SO_PEERCRED` checks plus native filesystem permissions against separate ephemeral numeric UIDs, in one disposable directory with a fake sink. It specifically tests an old actor who knows the **current** fake ref SHA and an attempted direct read or write of sink-only files. No credentials or real user data are used.

## Reproducibility

- Exact Python source: `vf_office_v2_604_linux_peercred_sink_lab.py`.
- Source SHA-256: `2b9bf96e719363d4aca723b77deb9a07b9358bddc31211158b5cf8cb588b01b2`.
- Primary source-digest-bound JSON receipt: `vf604_linux_peercred_lab_receipt.json`.
- Receipt SHA-256: `a7dc350ae6138f369f9c8da0921c362d48e4be876ee6fa831b1a1915f16e25d9`.
- Linux kernel: 6.18.44; Python 3.13.5; ephemeral numeric UIDs 62001 sink, 62002 worker-A, 62003 worker-B, 62004 unauthorized. No OS user accounts created.
- Privileged execution is permitted **only** inside a disposable Linux container with the explicit environment gate `VF604_DISPOSABLE_LINUX_LAB=YES`. It should not be deployed on any production host.
- Invocation: `VF604_DISPOSABLE_LINUX_LAB=YES python3 vf_office_v2_604_linux_peercred_sink_lab.py lab` and `python3 vf_office_v2_604_linux_peercred_sink_lab.py verify`.
- Without the explicit environment gate, the LAB exits 3 with `NOT_RUN_REQUIRES_EXPLICIT_DISPOSABLE_LINUX_ROOT_GATE`.

## Verified outcome

17/17 cases passed in the final exact-source run and three further consecutive documented repetitions. Checks included:

1. Kernel `SO_PEERCRED` UID-to-worker identity admission denial for mismatched self-assertions.
2. Unknown UID admission denial; label/capability/source scope negative cases; unprivileged worker cannot rotate provider state.
3. Real filesystem denial: each of three non-sink UIDs failed to open the mock credential and the sink-owned SQLite file for mutation.
4. Provider-fixture epoch rotated from 7 to 8 **without changing fake ref SHA**; old UID still holding exact current fake ref SHA was denied before the local effect.
5. Three independently launched Linux processes from two worker UIDs raced for the same logical intent: exactly one local synthetic SQLite effect, observed from independent controller readback; replay denied.
6. Fake `FROZEN_UNKNOWN` and provider-unavailable states deny further requests, with no permissive fallback; root controller may shut down and remove disposable socket.

**Mutation sensitivity:** 2 deliberate changes to separate disposable code copies were rejected by the test suite rather than silently passing.

| Mutation | Exit | PASS count | Detected critical failure |
| --- | ---: | ---: | --- |
| Accept self-declared worker identity rather than kernel UID | 1 | 11/17 | Unauthorized UID committed a synthetic effect; spoofed identity was not denied |
| Skip actor/epoch guard | 1 | 14/17 | Old owner committed with the latest ref SHA; gate L08 failed |

Raw mutation receipts (original source was unchanged):
- `vf604_mutation_selfassert.json`, SHA-256 `334e3108ff7cbab1598989b922316d523973d1994d8444ec76e0a72dbe970ae7`.
- `vf604_mutation_staleepoch.json`, SHA-256 `5265189ee22655a795cfa3ef6b3f5da0479a55f2be2fb3d23fc1befbf88427a3`.

**Cleanup:** All final-run disposable sink child processes exited, socket was removed, and source proof checked for no remaining `/tmp/vf604-peercred-*` directories. One earlier interrupted repeated-run invocation left a stale LAB socket path; its listener was verified inactive and its marker-gated scratch directory removed. This is an operational caveat: do **not** claim cleanup was flawless under all interruption conditions.

## Explicit NON-CLAIMS

- The provider, lease, ref SHA, effect and journal are all **fixture state in the same local SQLite database**. That shared atomic transaction is exactly what external GitHub+etcd do **not** provide. This test does not solve the cross-store race or establish exactly-once behavior across hosts.
- A synthetic file called `fake-git-token` is **not** a real GitHub credential; no actual GitHub App token, native Git push, provider key custody, certificate, CA, Dagu coordinator, mTLS, external API, TCP listener or protected branch write was involved.
- The simulated Linux UIDs are not independent Windows SYSTEM / Session1 principals or Mac UID501 accounts. Root of the disposable container can inspect any fixture; an administrator compromise remains in the sink trust domain. No sandbox escape or malicious source hardening claim.
- Positive local permission/identity tests do not satisfy I01 two physical hosts, I02 *native provider GitHub*-enforced stale-epoch denial, I06 genuine certificate-subject-to-Dagu-ID rejection, I07 real OS/network credential denial on owner machines, I08 reliable process-tree cancellation, or I09 production-provider partition safe recovery.
- This fixture runs model-authored trusted synthetic code **only in the assistant's disposable container**, not on any of the six real hosts; no customer, CAD, printer, Instagram or privileged production operation occurred. No Codex CLI or new paid inference.

## Next gate

Review/pin this isolated fixture and negative results under a protected narrow PR. The next material target is separate-OS-principal credential custody with authenticated sink admission and a provider-native stale-owner denial **including current remote Git SHA**, constrained to an explicitly approved scratch resource. Do not activate Dagu LAN workers or live agent pushes on the strength of this offline lab. #604 stays OPEN/RED and #612 stays OPEN/PARTIAL.
