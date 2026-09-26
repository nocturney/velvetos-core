# progress: openpost-v4.36.3-staging-2026-09-26

| Time (Asia/Jerusalem) | Step | Result |
|---|---|---|
| 2026-09-26 08:24 | Read authority: `OPENPOST.json`, `OPENPOST.md`, `AGENTS.md`, `instances/velvet-factory/AGENTS.md`, `automation/grok/CONTRACT.md`, vfbridge6, prior staging checkpoints | Staging = Windows `windows-backup-worker`, loopback 18080, isolated smoke 18081 |
| 2026-09-26 08:28 | Upstream releases + compare `v4.35.0...v4.36.3` | 118 commits; migrations 137, 138; new Meta scopes; MCP default change |
| 2026-09-26 08:31 | vfbridge6 `tracked.patch` + overlay on the v4.36.3 source | Clean apply (1 offset); go test 4 packages ok |
| 2026-09-26 08:34 | Box-isolated smoke (loopback 18090, synthetic DB) | 136→138 PASS, integrity ok, FK 0, restart ok, rollback-by-restore ok |
| 2026-09-26 08:35 | Compile probe of the patched server + token helper | exit 0 (stub frontend; not deployable) |
| 2026-09-26 08:40 | Classification probe (throwaway test, not committed) | Upstream `TransportError` changes vfbridge6 classification on upstream-client paths; velvet_mcp path unchanged |
| 2026-09-26 08:50 | Windows staging run | **NOT_RUN**: unreachable from the agent box; owner/operator gate |
