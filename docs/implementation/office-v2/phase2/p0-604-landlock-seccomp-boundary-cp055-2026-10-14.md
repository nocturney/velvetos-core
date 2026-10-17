# Office 2.0 #604 / #612 — CP055 Landlock + Seccomp native isolation research

**Status: LAB ONLY / fixed benign fixture / NOT AN ADMITTED WORKER.** Verified 2026-10-14. This is a nonproduction candidate for reducing the OS-executor gap; it does not mint an authoritative fleet lease or permit model-generated source execution.

## Reproduced real kernel outcome

On the **existing** MacMiniOffice2 `velvet-qa` Colima guest, Linux 6.8.0-117-generic **aarch64**, running as unprivileged UID 501 (2 guest CPUs / 4 GiB allocation), the Landlock ABI query returned **4**. User namespace creation was independently blocked, and rootless containerd was absent. Therefore we tested Landlock filesystem + TCP policy paired with an ARM64 Seccomp classic BPF syscall-deny filter, without installing a container daemon, creating another VM, changing sysctls or using root.

The fixed **operator-authored synthetic** Python fixture tested one explicitly allowed Scratch directory; restricted file reads/writes, `/run/containerd` directory traversal, direct Unix/TCP/UDP socket creation, process spawning, signals, the `no_new_privs`/Seccomp state, and access to the runtime interpreter. No LLM-authored text, arbitrary shell request, credentials, customer data or production Git action was admitted.

| Native test | Actual result | Pinned source SHA-256 | Native guest receipt SHA-256 |
| --- | --- | --- | --- |
| Initial basic boundary | **14/14 PASS** | `a1401adab6d95223d5c71355237ef24a7d5e81ae776593a2114201f55b907728` | `05545a3f3155043df212aa21ce91e388a8dbc99f5bfc311123478bb02e9d73d3` |
| **Metadata RED** (16 cases) | **14/16, exit 2**, failed `denied_outside_chmod`, `denied_outside_utime` | `8822b072d0dab3c235f2f4b27f2a6456d6343eda1e6947d1fe29f7c322642fbb` | `ff126e5fd88384156306e54a4e824f982d8311ba0186c3392ea6578bf8ce9b67` |
| **Metadata GREEN** (same 16 cases) | **16/16 PASS, exit 0** | `362b77b0b64c1da40ea875fb38126a3039ece658fe81710f35dd7aeb527ad45e` | `374ec43fc3bd9bfeab56e16746d4c65ad9e862abb04a64ad45f8f0b0e1965262` |

All outside-Scratch metadata operations targeted **temporary sentinel files created by the probe itself**. The metadata RED test demonstrated a *real missing restriction* in the original design: `os.chmod` and `os.utime` worked on same-UID files even though Landlock denied their contents. The GREEN version explicitly denies the relevant ARM64 metadata syscalls via Seccomp, including fchmodat and utimensat, and installs memory/CPU/output/FD limits before the Seccomp filter. The original basic checks remained passing. No untrusted/generated source was executed in any test.

**Source-pinned deliverables:** `scripts/vf_office_v2_604_landlock_seccomp_native_lab.py` is the **exact SHA-256-identical** GREEN source shown above (a one-shot, hardcoded Scratch-only native probe, not a general executor). `scripts/vf_office_v2_604_landlock_seccomp_receipt_gate.py` is a portable **read-only** evidence checker. The accompanying JSON contains exact red/green hashes, 16 expected case identities, denied metadata fields and explicit false authority assertions. The historical hashes are operator-captured readbacks, **not cryptographically attested or signed provider receipts**.

## Safe verification path

On any checkout with Python 3.9+:

```sh
python3 -B scripts/vf_office_v2_604_landlock_seccomp_receipt_gate.py --check
python3 -B scripts/vf_office_v2_604_landlock_seccomp_receipt_gate.py --selftest
```

The first command validates the pinned bytes and historical evidence with **no runtime execution**. The second uses at least 35 negative mutations to ensure altered admission, status, outcome and receipt claims fail closed, also with no guest/model access.

The native probe is **not a run-on-every-machine command**. It only permits a pre-created owned `/tmp/office-p0-landlock-cp055-metadata-green` inside a dedicated existing Linux ARM64 research guest, and refuses source collisions, root UID, unsupported Landlock ABI or altered host state. **Do not rerun by deleting existing guest receipts or switching to a real model-source file; that would destroy historical evidence / expand authorization.** New native reruns must be separately staged and re-pinned in a fresh isolated LAB.

## Missing security and runtime admission gates

Landlock ABI4 has no native Unix-socket resolution / signal scope, device ioctl gating or coverage of all chmod/metadata actions. The ARM64 Seccomp deny list addresses **only specifically enumerated syscall families** and has not had a comprehensive bypass audit; other same-UID IPC, `/proc`, inherited FDs, file capabilities, kernel changes, user-group access and alternate metadata/syscall paths may remain. No dedicated guest identity, independently enforced cgroup memory ceiling, signed task/host/GPU lease, immutable worker image, credentialless external Git sink, atomic effect fencing, concurrent double-claim prevention, crash/UNKNOWN reconciliation or full hidden QA is proven.

The guest user's group access to the **rootful containerd socket** remains a material risk outside this one child process; Seccomp denies the child's socket syscalls, but that is **not** proof of exclusive rootless host isolation. Preserve the intentional `P0_GENERATED_SOURCE_OS_ISOLATION_NOT_ADMITTED` guard in #612; do not connect this script to Aider/OpenCode, a real worker, a scheduler or Production.

Only after a separate security review, dedicated user/guest, trusted task claim and independently verified end-to-end effect boundary should a **new** isolated worker implementation be considered.

**References:** [Linux 6.8 Landlock userspace documentation](https://docs.kernel.org/6.8/userspace-api/landlock.html), [Landlock(7) ABI/version and limitations](https://man7.org/linux/man-pages/man7/landlock.7.html), [ARM64 syscall definitions](https://github.com/torvalds/linux/blob/master/tools/include/uapi/asm-generic/unistd.h).

**Owners:** canonical fleet/lease authority [#604](https://github.com/nocturney/velvetos-core/issues/604); P0 real coding-agent acceptance [#612](https://github.com/nocturney/velvetos-core/issues/612). Not a new owner, scheduler or authority.

## CP056 follow-up — executable image replacement gap and native correction

**The CP055 metadata GREEN result did not prove process-image confinement.** The original ARM64 Seccomp policy rejected `clone`/subprocess but allowed direct `execve`, including the wrapper's own use of `execve` to start the fixed Python fixture. An already-running process could replace its executable even though the kernel retained its existing Landlock/Seccomp restrictions.

**Native RED, on the same existing Linux guest:** An isolated copy of the original policy (source SHA256 `a566df3cb4b84248dcbd3733df44653f20d1d7afd15ca7cb55113dfa455279d4`) attempted only the benign, operator-fixed `os.execve('/usr/bin/true', ...)` after installing both restrictions. It printed `CP056_BEFORE_DIRECT_EXECVE_TRUE`, the executable replacement succeeded and the process exited **0**. No user/customer file, dynamic model content or other program was executed.

**Native GREEN:** the test harness now runs its **fixed operator-authored Python literal in the same process**, after restrictions, without an OS-level executable replacement. The ARM64 Seccomp filter denies both `execve` (221) and `execveat` (281). Two new real negative controls invoke both system calls against harmless `/usr/bin/true` and require permission-denied. All original 16 cases remain present; the real guest run completed **18/18 PASS, exit 0**, source SHA256 `5d1f1769b36646c10d469e194d8338b6b038bfdeedc05f265fb3a5a7db9d1c36`, guest receipt SHA256 `dc7a8875de833242fd68ccbf11d31c5bea0e11a77ac3ed6099151c5b3dd3c5db`.

The source-controlled `scripts/vf_office_v2_604_landlock_seccomp_native_lab.py` is the **18-case CP056 GREEN** copy, byte-identical to the above actual native test. The associated JSON preserves both older CP055 metadata result hashes in `red` and `green` and adds `execve_red` / `execve_green` with distinct exact source/receipt pins. The offline evidence gate requires the new source bytes and retains its strict false-authority negative controls. Historic CP055 green remains valid only for its original 16 assertions, not for `execve`.

Python `exec(compile(FIXTURE_TEXT,...))` in this particular LAB consumes **only a source literal bundled in the pinned operator-authored script**. It is *not* an OS executable replacement and **is not a general facility for executing model output**. No arbitrary code parameter, filename override, privileged service, production Git effect or Core lease was added.

**Still NOT ADMITTED:** a raw Linux UID501 in the shared Colima guest remains outside an independently proven dedicated OS-principal boundary and can belong to a group with rootful Containerd access; same-UID IPC, inherited file descriptors, the complete ARM64 syscall surface, cgroups and input provenance remain unaudited. No signed/fenced Core #604 task/host/GPU lease, privileged-output sink, model-generated patch or independent hidden QA is proven. The deliberate #612 `P0_GENERATED_SOURCE_OS_ISOLATION_NOT_ADMITTED` guard remains intact.
