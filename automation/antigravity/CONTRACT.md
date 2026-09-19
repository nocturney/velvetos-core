# VelvetOS Antigravity Automation Contract

Current merged/runtime authority wins over stale prompt text. Read `AGENTS.md`, `instances/velvet-factory/AGENTS.md`, the current instance config, `packages/vfops/ROUTINE.md`, `packages/vfops/LOOP.json`, relevant package authority, and recent merged changes before acting.

Protected cadence is owner-approved and must not be optimized silently. Timezone intent is Asia/Jerusalem; on this Windows host the scheduler clock must resolve to `Israel Standard Time`.

Never revive legacy/deleted routines: Creative Autopilot, Morning Brief Fallback, Evening Summary, Automation Steward, Media Intake, Publish Watch, Content Sprint, Insights Review, one-time recovery/publish jobs, or historical content reminders.

GitHub Actions remains the deterministic execution plane. Do not duplicate machine-owned workflows when their evidence is current.

## Owner email contract

Any owner email must use the CURRENT Morning Brief V10.3 rich RTL responsive/Outlook-safe design system, exact owner-visible text gate where required, and only the canonical production sender:

`packages/vfops/out/gmail-send-request.json` -> `.github/workflows/gmail-brief-send.yml` -> `packages/vfops/gmail_brief_request.py`.

Interactive/connected Gmail sending is not a normal or fallback owner-delivery path. Require real sender success, a real Gmail message ID, provider presence when readable, and safe reset of the one-shot request to `enabled:false`. Recovery Morning Brief must be full fidelity, never a reduced fallback.

## Migration safety

While `migrationMode=shadow`, do not send owner email, publish to Instagram, mutate Google Sheets/Drive, alter live automation schedules, push branches, merge PRs, spend money, or make any external write. Read and inspect only; return evidence and blockers.

Do not claim a connector/integration is ready unless it is actually available in the Antigravity runtime. If a required live source is unavailable, fail closed and name the missing capability.

For Google Workspace data on this Windows host, a fresh ephemeral live-context export produced by scripts/antigravity/fetch-live-context.ps1 is valid provider evidence. It uses the owner-authorized Antigravity OAuth credentials with direct Google APIs first and the GitHub OIDC/WIF export as fallback. The OAuth token store is local-only and must never be printed or committed. Google Sheets remains canonical; the ephemeral context is not a second source of truth.

### Shadow execution discipline

Shadow runs are capability probes, not implementation runs. Do not invoke shell/terminal commands in shadow mode. Use repository file/search tools, web/search tools, configured MCP reads, and other read-only agent tools only. Do not work around a denied tool by weakening permissions. A missing read capability is a migration blocker to report, not a reason to mutate the host.

Every shadow run must finish with a final explicit marker: SHADOW_PASS only when equivalent production execution is feasible, otherwise SHADOW_BLOCKED followed by the exact blocker. Do not stop on an intermediate tool error without emitting one of these final markers. Prefer direct file-view tools for known canonical paths; a terminal directory listing is not required to prove file existence.
