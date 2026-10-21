# Agent sandbox comparative test contract — Quicksand candidate

Source: [microsoft/quicksand at 5db6ada](https://github.com/microsoft/quicksand/tree/5db6adaf04ed61a003d7906a898f448ef89e4f3c), MIT. **Research-only / not installed.** Quicksand launches Linux QEMU guests via Python API and supports snapshots, host mounts and port forwarding; those features require hard trust-boundary tests. It does not create a new fleet scheduler or grant execution authority.

## Isolated comparative protocol

1. Establish existing protected execution baseline on a disposable host; identify allowed guest capabilities, QEMU/runtime versions, available disk/RAM/CPU, no GPU conflicts, and teardown ownership. Do not run on production services or a host with hardware instability.
2. Before launch, plan anonymous disposable guest image, network OFF, no host mounts by default, no host secrets/tokens, no privileged passthrough. Any mounts/ports explicitly allowlisted, read-only where possible, and documented in fixtures.
3. For Quicksand and incumbent, run matched **synthetic** probes: ordinary commands; network deny; guest-to-host and forwarded-port reachability; mount write attempts and traversal/symlink tests; process cancellation; guest crash; timeouts; snapshot/restore, persistent-file bleed, and complete teardown.
4. Independently measure functional task output and default-deny violations, startup and teardown times, CPU/RAM/disk peaks, snapshot integrity, cleanup, crash recovery and operator complexity.
5. Record exact pin, guest image hashes/licenses, chosen host, configuration and QA receipts; score incumbent / Quicksand adapter / hybrid. If any isolation test fails or is unverified, mark `NOT_ADMITTED` or `BLOCKED`, not promoted.

**Hard stops:** no unsandboxed generated source, production mounts, private credentials, broad port forwarding, auto-install, persistent daemon, new cloud cost, or host lease preemption. P0 #612/#604 gates still win. See `docs/implementation/office-v2/phase2/owner-creative-agent-tools-intake-2026-10-21.md`.
