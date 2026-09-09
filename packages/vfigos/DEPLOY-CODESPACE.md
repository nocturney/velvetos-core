# Instagram MCP · Codespace + remote autonomy

Status date: **2026-09-09**. No secrets in this file.

## Verified (Codespace / stdio)

| Check | Result |
|---|---|
| Package | `adelaidasofia-instagram-mcp` from [adelaidasofia/instagram-mcp](https://github.com/adelaidasofia/instagram-mcp) |
| Transport | **stdio** |
| Account | `@velvets_cloud` · IG user id `17841407772120429` · linked to Facebook Page |
| Smoke | `healthcheck` · `get_profile` · `list_media` OK (2026-09-08 Codespace) |
| Secrets location | host vault / Codespaces secrets / runtime env only — **never git** |

## Verified (Cloud Team MCP / remote — 2026-09-09)

| Check | Result |
|---|---|
| Cursor namespace | `instagram` · ready |
| Host | Cloud Run MCP path `/mcp` (Team MCP binding named `instagram`) |
| Transport | Streamable HTTP via Cursor Team MCP session (Team-scope metadata not exposed by `environment-info` — left unverified) |
| `healthcheck` | `live_check.ok=true` · username `velvets_cloud` |
| `get_profile` | username `velvets_cloud` · id `17841407772120429` |
| `list_media` | ok · sample count 5 · usernames `velvets_cloud` |
| Desk | `status: ready` · `auth: ready` · `transport: streamable-http` · **`remote_access: ready`** |
| DM | `dm_enabled: false` |

## Checklist — local / Codespace setup

1. Set secrets: `INSTAGRAM_MCP_ACCESS_TOKEN`, `INSTAGRAM_MCP_IG_USER_ID` (optional `INSTAGRAM_MCP_APP_SECRET`).
2. Do **not** set `INSTAGRAM_MCP_DM_ENABLED`.
3. `pip install adelaidasofia-instagram-mcp` (or editable install from the clone).
4. Register MCP server name `instagram` with command `instagram-mcp` and env passthrough (see `packages/vfmcp/mcp.desktop.example.json`).
5. Reload MCP client → run `healthcheck` → confirm `@velvets_cloud`.
6. Publishing still requires vault approval + Canva/vfcovers + PREFLIGHT + **live verify** after `publish_*`.

## Explicit non-goals of this note

- Do not paste tokens into the repo or PR
- Do not enable DM tools
- Do not make the Drive vault world-readable
- Do not claim `liveVerified` from publish tool success alone
