# task_plan — OpenPost v4.36.3 staging review

> Template: `packages/vfharness/templates/task_plan.md`

**task_id:** openpost-v4.36.3-staging-2026-09-26
**pack:** vfigos · vfharness
**Opened:** 2026-09-26 (Asia/Jerusalem)
**Owner approval (scope):** "prepare a v4.36.3 test in a staging environment, without touching production"

## Goal

The exact upstream `v4.36.3` Windows binary runs on the **existing Windows staging** (`windows-backup-worker`, loopback 18080) with
a real backup, a PASS migration smoke 136→138 and a PASS staging smoke. Production (`openpost-prod`, `v4.35.0-vfbridge6`) and
`OPENPOST.json` pin/production fields stay untouched until a separate owner decision.

## Steps

- [x] **1. Planning.** Read `AGENTS.md`, `packages/vfigos/OPENPOST.md` (release/upgrade policy 1–9) and `OPENPOST.json` (`releasePolicy`, `runtime`).
- [x] **2. Sources.** Upstream release notes, compare `v4.35.0...v4.36.3` and source tarballs at the exact tags (see `findings.md`).
- [x] **3. Box preparation.** vfbridge6 rebase check (clean apply, tests ok, compile probe ok); box-isolated migration smoke 136→138 PASS.
- [ ] **4. Windows staging run.** **Waiting for owner or office host operator** (see the runbook below). Not reachable from the agent box.
- [ ] **5. Verification.** Record the results in this folder + `openpost-v4.36.3-staging-2026-09-26.json`; `staging_smoke` PASS/FAIL.
- [ ] **6. Owner decision.** Only after 4–5 pass: build a `vfbridge7` candidate (with the TransportError follow-up) and a separate production decision.

## Staging runbook (Windows host, staging only)

Run on `windows-backup-worker` as the staging owner account. **Never** point any of this at `openpost-prod`, its tokens, its SSH/IAP
path, or the Instagram failover state under `C:\ProgramData\VelvetOS\instagram-failover`.

Paths follow `packages/velvetos/WINDOWS-PATH-CONTRACT.md` (`D:\Velvet\Services\OpenPost\staging`, backups under `D:\Velvet\Backups`).

1. **Pre-probe (read-only).** `GET http://127.0.0.1:18080/api/v1/ready` = 200 `ready`. The running binary SHA-256 must equal
   `be6520f495def72b1b466a69c9a223954b4403c3c7c40881b52ce0f030334cc8`. `schema_migrations` max = 136. `integrity_check=ok`. FK = 0.
   The start-script SHA-256 must equal `2d5541e4c2b7017c9d34212e78e53c02ee6f144f0e54cf1b1f68defbfed03bd0` (`OPENPOST.json` → `runtime.persistence`).
2. **Download the exact artifact.** Get `https://github.com/getopenpost/openpost/releases/download/v4.36.3/openpost-server-windows-amd64.exe`
   into a new versioned folder. Verify SHA-256 = `8d799a0de2a2a0cf286c02c479343187a75b21d8329e1d9e0bb410fe81f3f35f`, or **stop**.
   Never use `latest`.
3. **Real backup (migration upgrade).** Stop the staging task. Copy the SQLite DB (+ `-wal`/`-shm` if present) and the media dir to
   `D:\Velvet\Backups\OpenPost\pre-v4.36.3-<yyyymmdd-hhmmss>`. Record the DB SHA-256, schema 136 and media file/byte counts.
4. **Isolated migration smoke (port 18081).** Run the v4.36.3 binary against a **copy** of the backup DB on `127.0.0.1:18081` with
   `OPENPOST_DIAGNOSTICS_ENABLED=false`. Expect ready 200, schema max 138, `integrity_check=ok`, FK 0, the
   `publications.creation_source` column present and the `mcp_media_upload_tickets` table present. The original DB must stay byte-identical (re-hash it).
5. **Promote on staging only.** Point the staging start script at the v4.36.3 binary (keep explicit `OPENPOST_DIAGNOSTICS_ENABLED=false`), restart
   the task and confirm the firewall rule `VelvetOS-OpenPost-Staging-LocalOnly` is still Block. Record the new start-script SHA-256
   (`scripts/check-windows-path-contract.py` pins it, so the `OPENPOST.json` staging fields must be updated in the same results PR).
6. **Staging smoke** (`OPENPOST.md` step 7): health/auth config, queue/schedule of a **draft** publication with no provider account, API
   contract read (`/api/v1/workspaces`, `/api/v1/publications` as used by `packages/vfigos/openpost_morning_snapshot.py`), retry
   path, analytics read, and a restart/persistence test. **No publish and no provider connect.** Staging holds no Meta provider app.
7. **Rollback** if any step fails: stop the task, restore the start script and the pre-upgrade DB from step 3, restart and re-verify the step 1 values.
8. **Record.** Write the results into `openpost-v4.36.3-staging-2026-09-26.json` + `progress.md`. Only then may `runtime.staging*` in `OPENPOST.json` be
   updated to v4.36.3. `currentBaseline`, `runtime.productionHost.*` and `liveVerified` stay unchanged.

## Out of scope for this task (separate owner decisions)

- Meta app permissions `pages_read_user_content` + `pages_manage_metadata` on app `1748471159829574` (owner, Meta dashboard).
- `vfbridge7` build (Cloud Build in GCP project `instamcp`) and any production deploy.
- Anything v5.x / v6.x (hold PRs #279 and #298 stay untouched).

## Decisions

| Date | Decision | Why |
|---|---|---|
| 2026-09-26 | Stop before the Windows staging run | The loopback-only host is unreachable from the agent box, the office host also runs the Instagram failover watcher, and the task stop rule applies to ambiguous or owner-only steps |
| 2026-09-26 | No `OPENPOST.json` edit in this PR | Pin, production tag and `liveVerified` must not change; staging fields change only after a real staging run |

## Blockers / escalation

See `checkpoint.json` → `gate`.
