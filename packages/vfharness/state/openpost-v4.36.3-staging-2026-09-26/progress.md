# progress: openpost-v4.36.3-staging-2026-09-26

| Time (Asia/Jerusalem) | Step | Result |
|---|---|---|
| 2026-09-26 08:24 | Read authority: `OPENPOST.json`, `OPENPOST.md`, `AGENTS.md`, `instances/velvet-factory/AGENTS.md`, `automation/grok/CONTRACT.md`, vfbridge6, prior staging checkpoints | Staging = Windows `windows-backup-worker`, loopback 18080, isolated smoke 18081 |
| 2026-09-26 08:28 | Upstream releases + compare `v4.35.0...v4.36.3` | 118 commits; migrations 137, 138; new Meta scopes; MCP default change |
| 2026-09-26 08:31 | vfbridge6 `tracked.patch` + overlay on the v4.36.3 source | Clean apply (1 offset); go test 4 packages ok |
| 2026-09-26 08:34 | Box-isolated smoke (loopback 18090, synthetic DB) | 136→138 PASS, integrity ok, FK 0, restart ok, rollback-by-restore ok |
| 2026-09-26 08:35 | Compile probe of the patched server + token helper | exit 0 (stub frontend; not deployable) |
| 2026-09-26 08:40 | Classification probe (throwaway test, not committed) | Upstream `TransportError` changes vfbridge6 classification on upstream-client paths; velvet_mcp path unchanged |
| 2026-09-26 08:50 | Windows staging run (turn 1) | NOT_RUN: unreachable from the agent box; owner/operator gate |
| 2026-09-26 10:08 | Owner approval: "Run the test from my computer, staging environment only." | Staging-only run on the owner PC |
| 2026-09-26 10:10 | Step 0 read-only host verification (PC `Chris`, COMPUTERNAME `CHRIS`) | Confirmed staging host: dir, task Running, v4.35.0 sha, start-script sha, firewall Block, schema 136; prod not on this PC; nothing shared with prod |
| 2026-09-26 10:13 | Runbook attempt 1 | FAIL_BEFORE_ANY_CHANGE (pre-probe firewall read null: helper `Fw` shadowed by alias `fw`=Format-Wide); no change |
| 2026-09-26 10:14 | Runbook attempt 2: stop + real backup | `D:\Velvet\Backups\OpenPost\pre-v4.36.3-20260926-101455` (raw copy hash-match, consolidated DB schema 136 ok) |
| 2026-09-26 10:15 | Download + SHA | `8d799a0d…f35f` match |
| 2026-09-26 10:15 | Migration smoke 127.0.0.1:18081 on a copy | PASS: 136→138, integrity ok, FK 0, API smoke pass, staging DB unchanged |
| 2026-09-26 10:15 | Promote staging 18080 → v4.36.3 | Ready; firewall Block |
| 2026-09-26 10:15 | Staging smoke 18080 | PASS (health, ready, queue, retry contract, analytics) |
| 2026-09-26 10:16 | Restart/persistence | PASS; final: v4.36.3 running, schema 138, firewall Block |
| 2026-09-26 10:36 | Owner follow-up: "Maybe update to the latest version? Keep it in the test environment, because we're temporarily not using OpenPost for publishing due to failures and unreliability in scheduled posts." | Staging-only evaluation of latest upstream |
| 2026-09-26 10:37 | GitHub releases + 5.x/6.x notes + v6.2.0 source diff | v6.2.0 is latest; migration 139 only; CLI/.env unchanged; `OPENPOST_MCP_MODE` default `direct` |
| 2026-09-26 10:38 | Box pre-check v6.2.0 on a copy (loopback 18096) | 138→139, integrity ok, FK 0, smoke + restart pass |
| 2026-09-26 10:39 | Staging run v6.2.0: pre-probe + backup | v4.36.3/138/Block confirmed; backup `D:\Velvet\Backups\OpenPost\pre-v6.2.0-20260926-103903` verified |
| 2026-09-26 10:39 | Download + SHA | `b0b35293…cdb7d` = release asset digest |
| 2026-09-26 10:39 | Migration smoke 18081 on copy | PASS: 138→139, discovery tables dropped, integrity ok, FK 0, staging DB unchanged |
| 2026-09-26 10:39 | Promote 18080 → v6.2.0 | Ready; firewall Block; start script path-only change |
| 2026-09-26 10:39 | Staging smoke 18080 | PASS (health, ready, 401, draft create/delete, schedule refusal 503, retry 409, analytics) |
| 2026-09-26 10:40 | Restart/persistence | PASS; final: v6.2.0 running, schema 139, firewall Block |
