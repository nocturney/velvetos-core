# #604 Office 2.0 P0 — six physical hosts: native capabilities and dispatch bottleneck

**Observed:** 2026-10-12, 21:16–21:22 Asia/Jerusalem. **Status:** READ-ONLY / public synthetic task parity verified / real parallel throughput UNKNOWN / security admission BLOCKED.

This update supersedes the historical **two-connected-host inventory count**, but **does not** supersede any #604/#612 safety gates, create worker authority, introduce a scheduler, or change any runtime, GitHub protection, credentials, customers or printers. Evidence was obtained through existing Remote Desktop Commander device listings and direct native OS reads, plus one bounded synthetic SHA-256 task per dispatch. Corresponding issue note: [#604 comment 6130077910](https://github.com/nocturney/velvetos-core/issues/604#issuecomment-6130077910).

## Six real physically reachable hosts

| Device | Hardware actually observed | OS CLI context observed | Current useful tags, not independent execution authority |
| --- | --- | --- | --- |
| Chris | Windows 11 Pro, Core i9-14900K, 24 cores / 32 threads, ~63.7 GiB RAM, RTX 4080 SUPER, Intel UHD | Desktop Commander under SYSTEM **Session 0**; existing interactive explorer session separately present | Native Windows CLI, NVIDIA compute *candidate*, interactive UI only via a separately admitted user-session launcher |
| Chris-3DPC | Windows 11 Pro, Ryzen 9 5950X, 16 cores / 32 threads, ~63.9 GiB RAM, Radeon RX 9070 XT | SYSTEM **Session 0**, no explorer.exe user desktop observed | Native CLI, AMD GPU *candidate*, no GUI user-session authority established; previous TDR incident open |
| Chris-Mini-PC | Windows 11 Pro, Core i5-14500, 14 cores / 20 threads, ~15.7 GiB RAM, Radeon RX 6900 XT + Intel UHD | SYSTEM **Session 0**, no explorer.exe user desktop observed | Native CLI/headless candidate; no GUI user-session authority established |
| MacMiniOffice | macOS Apple M4 10-core, 16 GiB RAM, Apple M4 graphics; Blender command present | chris **UID 501**, console session present | macOS CLI, Apple Silicon/Blender-specific capability candidate; NOT a distinct OS security principal from other Macs |
| MacMiniOffice2 | macOS Apple M4 10-core, 16 GiB RAM, Apple M4 graphics | chris **UID 501**, console session present | macOS CLI and interactive user session; native Blender capability not confirmed |
| Mac-Bedroom | macOS Apple M4 10-core, 16 GiB RAM, Apple M4 graphics | chris **UID 501**, console session present | macOS CLI and interactive user session; native Blender capability not confirmed |

All six existing Remote Commander device records were **Online** when sampled. No model-generated source was executed, no GPU/GUI benchmark run here, and no Windows Sandbox guest or VM isolation claim is implied. Native CLI availability is only a discovery result, not an app workflow acceptance.

## Public synthetic receipt parity across OS boundaries

Every task hashed precisely the UTF-8 bytes of the **fixed synthetic literal** `vf-office604-public-synthetic-sha-v1` using OS-native PowerShell SHA256 (.NET) on Windows or `printf | shasum -a 256` on macOS. No user file, workspace, remote repository, network credentials or model-written Python was accessed or executed.

**Expected and observed SHA-256 on every successful host:**

`aadcc2b396c9268615d088c95ea4e3c3876cafd02394fd8fd1ec9ffb425f99fd`

### Bounded dispatch experiment — NOT worker speedup evidence

Host dispatch requests were issued through the connector in JavaScript Promise.allSettled. The numbers below are measured **client end-to-end dispatch + output retrieval**, *not* per-task CPU time, worker time, proven server-side parallelism or statistically reliable p50/p95.

| Hosts in cohort | End-to-end elapsed | Matching SHA receipts | Note |
| ---: | ---: | ---: | --- |
| 1 | 3,635 ms | 1/1 | Chris |
| 2 | 6,015 ms | 2/2 | Chris + MacMiniOffice |
| 4 | 11,880 ms | 4/4 | Chris + 3DPC + two Macs |
| 6, first run | 20,101 ms | **5/6** | One Chris-3DPC tool call rejected by upstream safety checks; **not fully green** |
| 6, second run | 19,141 ms | **6/6** | Six distinct host receipts, equal digest |

The roundtrip cost rose almost linearly despite concurrent client request promises. A separate six-host **OS-clock launch-timestamp probe** produced the following host-emitted UTC times within a ~22,016 ms client window (2026-10-12 18:21:14.479Z–18:21:36.495Z):

| Host | Host-local UTC execution timestamp |
| --- | --- |
| Chris | 18:21:16.3897396Z |
| Chris-3DPC | 18:21:20.7174470Z |
| Chris-Mini-PC | 18:21:24.1467038Z |
| MacMiniOffice | 18:21:29Z |
| MacMiniOffice2 | 18:21:32Z |
| Mac-Bedroom | 18:21:35Z |

**Interpretation:** Requests are *observably staggered*, consistent with serialization/queuing in the remote tool orchestration path; exact layer and independent host clock offsets were **not** calibrated. This is **not** evidence that six physical CPUs cannot compute concurrently. A true throughput benchmark needs controlled long-enough native workloads with per-host start/end timestamps and verified host clock offset, plus backend instrumentation or an already trusted concurrent dispatch adapter. Do not count this as 6x speedup.

## Safety/capability constraints and negative admission

- Chris's Remote Commander bridge runs under Windows **SYSTEM Session 0**; the presence of interactive explorer in another session is not authority to inject arbitrary GUI input there. Chris-3DPC/Mini have no observed explorer desktop even while their SYSTEM agent is available.
- Mac UID501 processes are not separate security identities. No CLI availability or remote service proves protected worker model execution, independent signer principal or daemon-owner restriction.
- Do not enable WinRM/SSH, alter Firewall/UAC/Defender, mount credentials, install a second scheduler, spoof a Windows Sandbox guest receipt, disable CI, force-push, or expand SMB permissions to erase dispatch latency.
- Read-only native transport check: Windows WinRM and sshd services were stopped, and no inbound port 22/5985/5986 listeners were observed on the Windows hosts; Mac system sshd launchd service was not found and no listener observed in the sampled process list. This is *not* permission to start/configure these services. Existing RustDesk, Chrome Remote Desktop, Syncthing and fleet baseline jobs were left untouched.
- The first six-host task batch saw a **tool safety check rejection**; no false acceptance. Later six-host receipt parity is truthful distinct evidence, not a reason to bypass future safety rejections.
- Historical #604 receipt-origin forgery and Hyper-V ETW false-attestation negatives remain authoritative. Independently observed **attended user-session Sandbox guest** is still MISSING. Dedicated Git Sink credential principal and authoritative expired-owner GitHub-native denial / UNKNOWN reconciliation remain UNPROVEN. #604 OPEN / RED; #612 OPEN / PARTIAL.

## Next low-risk measurable gate

1. Instrument existing transport timing with OS-clock skew checks and host-local bounded native task windows; measure actual **overlap**, not just fanout receipt parity. Keep production/inference/graphics loads idle.
2. Run capability-tagged **function-first** task-family comparisons (Windows API/CLI; Mac CLI/native apps; only separately authorized interactive GUI) with positive and negative outcomes.
3. Compare exact accepted off-the-shelf placement candidates using sandboxed public tasks and resource constraints, **not** by installing an additional production scheduler. Preserve one core source of truth and existing OfficeV2-Lab.
4. Only then revisit two distinct accepted algorithm workers and separately trusted Git Sink. This report deliberately contains **no claim of new Worker admission, VM isolation or Git write authority**.

**No production code, source model candidate, infrastructure settings, authentication, workflow, security rule, branch protection or user data was changed by these measurements.** This document is a scoped P0 evidence proposal subject to regular protected PR review/CI, not an automatic deployment authority.
