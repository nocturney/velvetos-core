# Office 2.0 / #604 / #612 — CP069: real low-privilege namespace execution boundary

**Date:** 2026-10-15 Asia/Jerusalem. **Scope:** existing Colima Linux LAB `velvet-qa` on physical **MacMiniOffice2.local**, fixed human/operator-authored synthetic code only. **Not a P0 agent executor admission; no model-generated source was executed.**

## Concrete gap and change

CP055/056 fixed Landlock/Seccomp metadata/execve escapes, but the Linux guest's regular user `chris` (UID 501, group `chris`) can access `/run/containerd/containerd.sock` (rootful daemon). Reusing that UID to execute future untrusted model code is not admissible. CP069 proves that a **different OS principal**, UID `65534` with supplementary groups cleared, can execute an exactly fixed harmless Python fixture in fresh Linux mount/network/PID namespaces with no effective caps or persistent privileges. The privileged namespace launcher is **only** a controlled prewritten `sudo -n unshare ... setpriv` command; there is no model/LLM command interpreter.

## Actual guest evidence — not inferred from static analysis

- Host MacMiniOffice2.local, pre-existing Colima profile `velvet-qa`, 2 vCPU/4 GiB, Linux kernel `6.8.0-117-generic`, `aarch64`. No VM, account, network listener, kernel parameter, daemon, firewall, shared directory, GPU or startup configuration changed.
- Parent UID 501 had read/write permission to the rootful containerd socket (the **known bad origin**); isolated child UID/EUID `65534`, GIDs cleared, `CapEff=0`, `NoNewPrivs=1`, separate `net/mnt/pid` namespaces, empty IPv4 route table, no outbound route, Unix socket connection denied, private canary read denied, credential env empty, bounded memory/CPU/files/FDs. **13/13 actual checks PASS twice** with different fresh private temp roots; temp root cleanup verified by follow-up `find`. Guest fixed child output SHA256 `6cda5412a1efce30dfc9ac0efdf3b40006e2e5471741a2250b43f8ca370e0003` both times.
- Pure static `selftest`: 17/17 mutation/false-authority negative checks, zero Linux guest launch in CI. Exact source SHA256 `7bef7efb34fa5611627f43c8f06cedf9c8d000c04190d9d80d25fb2ffda49eea`; parent and guest source hashes independently match.
- A real initial RED `no_ipv4_routes` check incorrectly expected one `/proc/net/route` header, while the isolated guest returned **zero lines**. The criterion was corrected to permit zero lines or exactly the conventional `Iface` header, never any route; subsequent full native tests 13/13 twice. Not a network escape, not counted as an early PASS.

## Why this is partial / admission still denied

1. **No Landlock+Seccomp composition on this new UID execution path yet.** Separate PID/mount/net namespaces and no privileges do NOT block arbitrary world-readable guest files, all filesystem metadata, every syscall, child process creation or kernel exploits. In particular there is no chroot/rootfs mount policy, no guest-local approved UID whose deployment/host-socket access has been fully audited, no provider-bound source digest, and no general untrusted-program admission.
2. The launcher temporarily invokes **root in the disposable Linux guest** to create namespaces; a fixed literal script is the only accepted child. This does not make the host controller root-safe or an isolated signing principal.
3. The child JSON report is **not signed attestation**, and host Mac UID 501 still retains rootful containerd authority, though child UID65534 cannot access the socket. Do not pass this as proof of sole Git credential custody.
4. No Core #604 **signed exclusive task/host/GPU lease**, provider mTLS/epoch cutover, crash/UNKNOWN reconciler, independent hidden QA of CP058 model source, external Git Sink fencing, live PR writer, merge or production effects. #612's existing `P0_GENERATED_SOURCE_OS_ISOLATION_NOT_ADMITTED` guard is **unchanged**.

**Next bounded integration gate:** compose CP055/56 filesystem+syscall restrictions with this reduced OS principal under an exclusive authenticated Core #604 lease, prove no rootful socket, no child/FD/process escape and provider-time fence, and only then run CP058 exact pinned model-produced repair in a separate trusted protected-base QA lane. No Codex CLI, new scheduler, paid inference, social/customer/printer/production effect or OpenBao PR #584 activation.
