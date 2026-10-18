# P0 native process-birth identity LAB — 2026-10-09

Owner: [Office v2 #612](https://github.com/nocturney/velvetos-core/issues/612). Fleet placement/leases remain exclusively [#604](https://github.com/nocturney/velvetos-core/issues/604).

## What actually ran

Both physical hosts executed **the same Python process-identity script source SHA-256 `2268091d9129eb504fc17ce7e7374367deb5ae23cb1327872796f353a16043ce`**, with **24/24** deterministic fail-closed offline checks **on each host**. They additionally ran independent native process observations using a uniquely owned disposable pair of **synthetic Python processes** (a parent and its child), not an Aider model execution. The child created its own POSIX session on Mac, and a fresh Windows process group on Windows. Each capture pinned both OS process creation times, their immediate parent relationship, the Task Envelope hash and a still-present no-blind-retry RUNNING journal in an exclusive LAB evidence folder. The second observation after **natural process exit** found the two historic PIDs absent. These synthetic processes were not force-killed; neither run used inference, worker scheduling or customer data.

| Host | Native identity backend | Live parent + child | After normal exit | Group observation |
| --- | --- | --- | --- | --- |
| MacMiniOffice.local | `PSUTIL_OS_CREATE_TIME` | Same kernel instance for both | Both historical PIDs absent | 1 potential member during; 0 afterwards |
| Chris Windows | `WINDOWS_CIM_CREATION_DATE` | Same kernel instance for both | Both historical PIDs absent | No Windows Job Object identity admitted |

- Mac receipt SHA-256: `31b43e7eb2b1cbd472a3466502443b1f172f772135a692cd791192773d8da73c` (elapsed 23.867s)
- Windows receipt SHA-256: `9a2d80625ce8ad568b5088aef6f76ebb3686feb9e1e6f73ebff4d4ff5ee554dc` (elapsed 23.875s)
- Both captures remain pinned to `2268091d9129eb504fc17ce7e7374367deb5ae23cb1327872796f353a16043ce`; readbacks are recorded in `p0-kernel-process-identity-lab-2026-10-09.json`.
- Independent **pure offline** `vf_office_v2_p0_kernel_evidence.py` checked both self-hashed receipts and refused **8/8** manipulated/re-sealed evidence cases (broken seal, source drift, fake retry authority, forged orphan exclusion, fake Windows Job Object, fake Mac birth match, wrong host, missing trial) on **both** machines.
- CI's existing Office contract sensor runs the module selftest and the independent evidence verifier. CI does **not** scan machine process tables, start an LLM or perform a process kill.

## Source, pinning and safe reproduction

- `scripts/vf_office_v2_p0_kernel_identity.py`: `selftest` (fully offline); `sample-self` (read the current process's OS birth metadata); `capture` (manual, only while parent+child are alive and a bound `receipt.json.running` journal exists); `observe` (read-only, requires the same exclusive `kernel-pin.json` beside receipt and verifies journal bytes before/after).
- On macOS, the capture runtime **requires psutil** with native OS process create times; the existing Aider venv had psutil 7.2.2. Absence refuses instead of falling back to weaker `ps` commandline heuristics. On Windows Python 3.11, native PowerShell CIM CreationDate worked without psutil. No package was installed.
- Manual controlled reproduction uses `scripts/vf_office_v2_p0_kernel_pair_lab.py --workspace /absolute/fresh/scratch/directory` (Windows: use a fresh absolute Windows scratch path). The path must pre-exist **outside** the Git source checkout. The probe does not kill anything; two tiny local fixture processes end naturally. It refuses an already-used probe output. This is not an autonomous agent.
- To independently check committed evidence: `python scripts/vf_office_v2_p0_kernel_evidence.py --source scripts/vf_office_v2_p0_kernel_identity.py --evidence docs/implementation/office-v2/phase2/p0-kernel-process-identity-lab-2026-10-09.json`.

## Honest safety limits and next gate

**Kernel-created process birth timestamps** are stronger than PID-only re-identification but **not cryptographic process attestations**, proof of tool/script identity or a guarantee that every descendant can be enumerated. POSIX process-group hints may be incomplete or reused; a zero-member snapshot is **not permission to retry**. Windows CIM does not create or prove Job Object containment. The earlier historical real Aider SIGKILL (#629) happened **before** this capture capability existed, so no birth identity can be attached retroactively to that killed worker. Do not claim historical full lineage, model-worker crash-resume, automatic cross-host failover, guaranteed cleanup or production promotion from this synthetic LAB.

**Next #612 admission:** record an OS-birth pin at the **actual model-worker/Aider child creation time** with durable journal binding, then repeat a real pinned Aider worker interruption in an exclusive leased LAB and independently reconcile (never blind-retry) with precise orphan/host ownership. Any scheduling, lease and host failover still belongs to #604. Keep local-first models and zero-new-spend policy; Codex CLI and production effects stay forbidden.

