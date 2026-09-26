# findings — OpenPost staging review v4.35.0 → v4.36.3

**task_id:** openpost-v4.36.3-staging-2026-09-26
**pack:** vfigos (OpenPost control plane) · harness: vfharness
**Reviewed:** 2026-09-26 08:24–08:50 Asia/Jerusalem
**Decision:** `STAGING_PREPARED / STAGING_NOT_RUN / PIN_HOLD`. No pin, no production-tag and no `liveVerified` change.

This review follows the release/upgrade policy in `packages/vfigos/OPENPOST.md` ("Release / upgrade policy", steps 1–9) and the
`releasePolicy.requiredChecks` list in `packages/vfigos/OPENPOST.json`. Every claim below comes from upstream GitHub
(release notes, compare API, source tarballs at the exact tags) or from commands actually run on an isolated box.
Nothing here counts as a staging PASS. The repo's staging runtime was not touched.

## 1. Upstream evidence

| Item | Value |
|---|---|
| Baseline | `v4.35.0` (published 2026-09-17 22:05 Asia/Jerusalem) |
| Target | `v4.36.3` (published 2026-09-19 14:44 Asia/Jerusalem): https://github.com/getopenpost/openpost/releases/tag/v4.36.3 |
| Releases in range | `v4.35.3` (Android release-promotion fix only: https://github.com/getopenpost/openpost/releases/tag/v4.35.3) and `v4.36.3`. There are no `v4.36.0`–`v4.36.2` tags. |
| Compare | https://github.com/getopenpost/openpost/compare/v4.35.0...v4.36.3: `ahead_by=118`, `behind_by=0`. The source-tree diff has 264 differing paths; the compare API caps its file list at 300. |
| Windows server asset (staging) | `openpost-server-windows-amd64.exe` `sha256:8d799a0de2a2a0cf286c02c479343187a75b21d8329e1d9e0bb410fe81f3f35f` (GitHub asset digest) |
| Linux server asset | `openpost-server-linux-amd64` `sha256:de478b024d751135620f707fa6c84f34b5fc679b4310490e2dee5c8c3a38c286` (GitHub asset digest; box download re-hashed identically) |
| Cross-check | The GitHub asset digests for v4.35.0 (`be6520f4…` Windows, `157abefc…` Linux) match the values already recorded in `OPENPOST.json` / `OPENPOST.md`. |

## 2. requiredChecks classification

| requiredCheck | Status | Evidence |
|---|---|---|
| release_notes_and_breaking_changes | REVIEWED | v4.35.3 + v4.36.3 release bodies; see §3. There is no declared breaking change, but the MCP default changed (§3.3). |
| meta_instagram_auth | REVIEWED: **owner action before any reconnect** | New OAuth scopes (§3.1). |
| api_mcp_contract | REVIEWED: **low VF impact** | VF reads OpenPost over REST (`/workspaces`, `/publications`) plus a read-only SQLite gate. No VF code calls OpenPost MCP (§3.3). |
| media_limits | REVIEWED: no Instagram change | Only Threads UTF-8 byte limit and Facebook video Story/Reel upload sessions. |
| scheduler_queue_retry | REVIEWED: **vfbridge follow-up** | New `PublishRequestReconciler` affects TikTok only. Upstream `TransportError` changes vfbridge6 classification on upstream-client paths (§4.3). |
| database_schema_migrations | **MIGRATIONS 137 + 138**: backup + staging migration smoke REQUIRED | §3.2; box-isolated smoke PASS (§5). |
| security | REVIEWED | Credential-bearing URLs are removed from provider transport errors, and a decompression-DoS fix landed in the archive reader. New authenticated endpoints: `PUT /mcp/media-upload`, `POST /mcp/code` and RFC 9207 issuer metadata (§3.4). |
| staging_smoke | **NOT_RUN** | The repo's staging host is not reachable from the agent box (§6). |
| instagram_live_verify | UNCHANGED / NOT_APPLICABLE | No write was performed. The existing LIVE_VERIFIED evidence belongs to the v4.35.0-vfbridge6 pin only. |
| analytics_read | REVIEWED | Facebook analytics metric families changed. Instagram analytics still requires only `instagram_manage_insights`. |
| signed_delivery_approval_live | UNCHANGED | No mutation path was touched. |

## 3. Upstream changes that matter to VF

### 3.1 Meta / Instagram OAuth scopes

- Source: `apps/server/internal/platform/instagram.go` `instagramScopes()` adds `pages_read_user_content` and
  `pages_manage_metadata`. `facebook.go` adds the same pair. The release note reads: "Fixed Facebook and Instagram connect failing with
  `Invalid Scopes: pages_read_user_content`…"
- Upstream docs at v4.36.3: `docs/reference/providers/instagram.md` and `apps/docs/content/docs/self-hosting/integrations/instagram.mdx`
  now list 10 scopes. `docs/reference/providers/troubleshooting.md` says `instagram_basic` depends on
  `pages_read_user_content`. The docs say to enable both on the Meta app and then reconnect.
- **Existing grant:** in v4.36.3 no Instagram capability requires either new scope at runtime. Engagement needs
  `instagram_manage_comments` + `pages_read_engagement`, messaging needs `instagram_manage_messages`, analytics needs
  `instagram_manage_insights` and account content needs `instagram_basic` (`engagement_capabilities.go`, `messaging_meta.go`,
  `analytics_meta.go`, `account_content_meta.go`). Inference from code: **an upgrade alone should not force re-auth** of the current
  `@velvets_cloud` grant. The first **reconnect or re-auth** after upgrading will request the two new scopes.
- **Meta app review:** Meta's access-level rules (https://developers.facebook.com/docs/graph-api/overview/access-levels/,
  https://developers.facebook.com/docs/permissions) grant Standard Access automatically, but only for users who hold a role on the app.
  Advanced Access (Business Verification + App Review) is needed only for users without a role. Whether Meta app
  `1748471159829574` already has the two permissions added, and whether the connecting Facebook user holds an app role,
  is **UNPROVEN**. Only the owner can check this in the Meta dashboard.

### 3.2 Database migrations (SQLite)

- `137_mcp_media_upload_tickets.sql`: new table `mcp_media_upload_tickets` (FKs to `workspaces`, `users`, ON DELETE CASCADE) plus index.
- `138_publication_creation_source.sql`: `ALTER TABLE publications ADD COLUMN creation_source TEXT NOT NULL DEFAULT 'unknown'` plus index.
- Additive only. The failover gate `packages/vfigos/failover/openpost_failover_state.py` reads explicit columns from `jobs`,
  `publications`, `renditions`, `provider_deliveries` and `provider_write_attempts`, and none of those columns change.
- Policy consequence: `backupBeforeMigrationUpgrade=true` means a real backup, then isolated migration smoke, then promotion.

### 3.3 MCP default change (in range)

- The release note says: "MCP lists every operation as its own tool by default; set `OPENPOST_MCP_MODE=search` to keep the previous search-first flow."
- **Source finding:** at tag v4.36.3, nothing in `apps/server` reads `OPENPOST_MCP_MODE`. `SetToolMode` is called only from
  `mcp_test.go`, so the documented opt-out has **no effect in v4.36.3** and the server always advertises direct mode. The wiring appears
  in `cmd/openpost/main.go` from v5.0.0 onward (checked at v5.0.0 and v6.2.0).
- VF impact: low. No VF runtime calls OpenPost MCP. VF uses REST plus the SQLite read-only gate, and the Instagram write path is
  the vfbridge `velvet_mcp` client to the Velvet Instagram MCP, not OpenPost's own MCP server. Any external assistant connected to
  OpenPost `/mcp` would see a different `tools/list`.

### 3.4 Security-relevant

- `platform/http.go`: provider transport failures are now returned as `*platform.TransportError`, which keeps no request URL
  (tokens in query strings no longer leak into stored or logged errors). This is good for VF, but see §4.3.
- New endpoints `PUT /mcp/media-upload` and `POST|GET /mcp/code`, plus `/.well-known/oauth-protected-resource/mcp/code`. On the box smoke,
  unauthenticated `POST /mcp` and `PUT /mcp/media-upload` both returned **401**.
- `OPENPOST_DIAGNOSTICS_ENABLED=false` must still be set explicitly (policy since v4.32). No new diagnostics default was found in range.

## 4. vfbridge6 rebase impact (`packages/vfigos/openpost/vfbridge6/`)

### 4.1 Patch applicability

- `tracked.patch` touches 7 upstream files. Of these, 4 are unchanged v4.35.0→v4.36.3 (`errors.go`, `failures.go`, `failures_test.go`,
  `publisher_lifecycle_test.go`) and 3 changed upstream (`cmd/openpost/main.go` +1 line, `platform/instagram.go` +2 scope lines,
  `services/publisher/publisher.go` new `PublishRequestReconciler` branch).
- `git apply --check` on the v4.36.3 source tree: **clean**, with one offset (`main.go` hunk #1 at line 1008, offset 1). There are no conflicts.
- The `overlay/` files (`velvet_mcp.go`, `velvet_mcp_test.go`, `cmd/vf-openpost-token/main.go`) copy in without collisions.

### 4.2 Build and tests on the rebased tree (box, go1.26.6 as pinned in `go.mod`)

- `go test ./internal/platform ./internal/services/publisher ./internal/queue ./internal/services/apitokens`: **all ok**. These are the
  same packages `vfbridge6/cloudbuild.yaml` tests. They include the 6 `TestVelvet*` tests.
- Compile probe: `go build ./cmd/openpost` with a stub `public/index.html` (no frontend build) and `go build ./cmd/vf-openpost-token`
  both succeeded (exit 0). **This is not a deployable artifact.** The real build must run the `cloudbuild.yaml` recipe (bun frontend + CGO).
- `gofmt -l` flags `velvet_mcp.go`, `velvet_mcp_test.go` and `failures_test.go`. This matches v6, whose recipe runs `gofmt -w` before testing.

### 4.3 Semantic finding: failure classification of upstream `TransportError`

vfbridge6 `failures.go` treats a post-write-fence network failure as `ambiguous_transport` via `errors.As(err, &net.Error)` /
`errors.Is(err, context.DeadlineExceeded)`. In v4.36.3, `platform.doRequestWithClient` returns `*platform.TransportError`, which
does not implement `net.Error` and has no `Unwrap`. A throwaway probe test on the rebased tree (deleted, not committed) showed:

| Input | kind / code / retryable |
|---|---|
| post-fence `TransportError{timeout}` (upstream adapters) | `unknown` / `ambiguous_provider_write` / false (still fail-closed, no replay) |
| post-fence raw `net.Error` timeout (vfbridge `velvet_mcp` own `http.Client`) | `network` / `ambiguous_transport` / false (unchanged) |
| pre-fence `TransportError{timeout}` | `unknown` / "" / **false** (was `network`, retryable) |
| pre-fence raw `net.Error` timeout | `network` / "" / true (unchanged) |

- The prod Instagram publish path (`velvetMCPConfigured()`) uses vfbridge's own `http.Client`, so its classification is **unchanged**.
- The failover gate keys on `provider_deliveries.state` / `retry_safety`, not `error_kind`, so failover safety is unchanged.
- Upstream-client paths lose automatic retry of transient pre-fence timeouts. This degrades reliability; it is not a double-publish risk.
  Recommended for a `vfbridge7` candidate: handle `*platform.TransportError` in `failures.go` (timeout/connection → network, with the
  post-fence ambiguity preserved) and add tests. This decision belongs to the build step, not to this PR.

## 5. Box-isolated pre-staging smoke (NOT the repo's staging)

This ran on the agent box only, on loopback port `18090`, with a fresh throwaway SQLite database, ephemeral random secrets, and
`OPENPOST_DIAGNOSTICS_ENABLED=false`, `OPENPOST_TELEMETRY_ENABLED=false` and `OPENPOST_DISABLE_REGISTRATIONS=true`. It had no provider app,
no Meta credential and no network exposure. Upstream Linux binaries were verified against the GitHub digests above.

1. v4.35.0 `all` on an empty DB: `/api/v1/ready` 200 `ready` / `database=ok`, `schema_migrations` max **136**.
2. A synthetic user, workspace and publication were inserted; `integrity_check=ok`, FK violations 0. DB backup sha256 `b614df23…153c`.
3. v4.36.3 `all` on the same DB: ready 200, schema max **138** (137 and 138 applied), `integrity_check=ok`, FK violations **0**,
   existing publication backfilled `creation_source='unknown'`, `mcp_media_upload_tickets` present, `/api/v1/openapi.json` 200,
   unauthenticated `/mcp` 401 and `/mcp/media-upload` 401.
4. Restart of v4.36.3 on the upgraded DB: ready 200.
5. Rollback probes: the v4.35.0 binary on the schema-138 DB came up ready 200 (additive schema). v4.35.0 on the **restored pre-upgrade
   backup** came up ready 200 with schema 136. Restoring the backup remains the canonical rollback.

What this does **not** prove: the real staging DB, the Windows binary, provider OAuth, publish/queue/retry flows, or anything in production.

## 6. Repo staging run (Windows staging host, 2026-09-26, owner-approved)

Owner approval (10:08 Asia/Jerusalem): "Run the test from my computer, staging environment only."
Turn 1 of this task could not reach the host from the agent box (see git history of this file); it was then run on the owner's registered PC.

### 6.1 Host verification (read-only, before any change)

- PC `Chris`, `COMPUTERNAME=CHRIS`, Windows 11 Pro, PowerShell 7.6.6. `windows-backup-worker` in `OPENPOST.json` is a role label; every
  fingerprint matched: `D:\Velvet\Services\OpenPost\staging` (`data`, `media`, `v4.31.0`, `v4.34.2`, `v4.35.0`), task `VelvetOS-OpenPost-Staging`
  Running, running exe sha `be6520f4…4cc8` (v4.35.0), start script sha `2d5541e4…3bd0`, firewall rule `VelvetOS-OpenPost-Staging-LocalOnly`
  enabled/Inbound/Block/Any/18080, `/api/v1/ready` ready, schema 136, provider apps/social accounts/OAuth grants 0.
- Isolation: the staging `.env` points only at `staging\data` / `staging\media`, port 18080 and staging-only secrets. Production runs on GCP
  `openpost-prod`; no prod-class OpenPost runs on this PC. Nothing (DB, data dir, port, credentials) is shared.
- Avoided: GrokBot tasks (Boot Supervisor/Interactive Handoff/Watchdog), the Instagram failover watcher (`C:\ProgramData\VelvetOS\instagram-failover`),
  and the prod rollout scripts in `C:\ProgramData\VelvetOS\openpost-rollout` (not scheduled here; not run).

### 6.2 Run (`run-openpost-v4.36.3-staging.ps1`, sha256 `963a176b…0d39`, non-admin)

| Step | Result |
|---|---|
| Attempt 1 (10:13) | `FAIL_BEFORE_ANY_CHANGE`: pre-probe firewall read returned null because a helper named `Fw` is shadowed by the built-in alias `fw` (Format-Wide). Staging was not stopped; nothing changed. Fixed by renaming. |
| Pre-probe (10:14:58) | ready; v4.35.0 sha; start script sha; firewall Block; schema 136; providers 0 |
| Backup | `D:\Velvet\Backups\OpenPost\pre-v4.36.3-20260926-101455`: raw copy of `data\` (`openpost.db`, `-wal`, `-shm`, migrate lock) hash-matched the originals; start script copied; `openpost.consolidated.db` (sqlite backup API, sha `3bdffb8d…cb28`) schema 136, integrity ok, FK 0; media 0 files; `BACKUP-MANIFEST.json` + `RUN-RESULT.json` |
| Download | `openpost-server-windows-amd64.exe` sha `8d799a0d…f35f` = release digest; `.env` copied from v4.35.0 (identical config) into `staging\v4.36.3` |
| Migration smoke 127.0.0.1:18081 (copy of backup) | **PASS**: ready; schema **138**; integrity ok; FK 0; `mcp_media_upload_tickets` + `publications.creation_source` present; jobs 3992 completed/6 pending preserved; API smoke pass; real staging DB sha unchanged |
| Promote 18080 | start script path `v4.35.0` → `v4.36.3` (new sha `9ca6072f…460a`); task started; ready; listener sha = v4.36.3; firewall Block |
| Staging smoke 18080 | **PASS**: health 200, ready, version `v4.36.3`, unauth `/api/v1/publications` + `/mcp/media-upload` 401, register/login, workspace, draft create (`creation_source=web`)/validate/get/delete, schedule without destination 503 ("no destinations to authorize"; no job), retry-failed 409 ("no retryable failed destinations remain"), publications + jobs list 200, analytics read 200 + refresh queue 200, accounts 0 |
| Restart/persistence | **PASS**: stop + start via the scheduled task, ready, v4.36.3 sha, schema 138, integrity ok, firewall Block |
| Result | `PASS`; no rollback needed |

Post-run read-only check: task Running; `::18080` pid 13808 = v4.36.3, ready; no 18081 listener; firewall rule Block; no firewall rules were
auto-created for the new exe.

### 6.3 Caveats

- Upstream listens on all interfaces (`e.Start(":"+port)`); local-only relies on the firewall. 18080 has the Block rule. The ~5 s 18081 smoke ran
  non-admin, so no temporary block rule was created; all profiles report `DefaultInboundAction=NotConfigured` (Windows default: Block inbound).
- Staging keeps one synthetic smoke user/workspace (`staging-smoke-staging-20260926101531@example.invalid`); the draft was deleted.
- Staging still has no provider OAuth, so Meta/Instagram publishing and the new scopes were **not** exercised (not possible without prod-class
  credentials; out of scope).
- `OPENPOST.json` `runtime.staging*` and `persistence.startScriptSha256` (pinned in `scripts/check-windows-path-contract.py`) still describe v4.35.0.
  Recording the new staging state is a separate owner decision/PR; this PR does not edit `OPENPOST.json`.
- Rollback path: stop the task, restore `start-openpost-staging.ps1` and `data\*` from the backup dir, start the task (v4.35.0 on schema 136).
