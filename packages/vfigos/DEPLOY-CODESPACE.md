# Instagram MCP · Codespace + remote autonomy

Status date: **2026-09-09**. No secrets in this file.

## Verified (Codespace / stdio)

| Check | Result |
|---|---|
| Package | `adelaidasofia-instagram-mcp` from [adelaidasofia/instagram-mcp](https://github.com/adelaidasofia/instagram-mcp) |
| Transport | **stdio** |
| Account | `@velvets_cloud` · IG user id `17841407772120429` · linked to Facebook Page |
| `add_account` | label `velvets_cloud` · default `true` |
| Smoke | `healthcheck` · `get_profile` · `list_media` OK (2026-09-08 Codespace) |
| Secrets location | **GitHub Codespaces Secrets / runtime env only** — never git, never committed mcp.json with tokens |
| Desk status | `ready-codespace` · `auth: ready` · `transport: stdio` |

## Checklist — local / Codespace setup

1. Set Codespace (or machine) secrets: `INSTAGRAM_MCP_ACCESS_TOKEN`, `INSTAGRAM_MCP_IG_USER_ID` (optional `INSTAGRAM_MCP_APP_SECRET`).
2. Do **not** set `INSTAGRAM_MCP_DM_ENABLED`.
3. `pip install adelaidasofia-instagram-mcp` (or editable install from the clone).
4. Register MCP server name `instagram` with command `instagram-mcp` and env passthrough (see `packages/vfmcp/mcp.desktop.example.json`).
5. Reload MCP client → run `healthcheck` → confirm default account `velvets_cloud`.
6. Publishing still requires vault approval + Canva/vfcovers + PREFLIGHT + **live verify** after `publish_*`.

## Remote Cloud / Team MCP (2026-09-09)

| Item | Status |
|---|---|
| Cursor namespace | `instagram` · `namespaceStatus: ready` in Cloud Agent |
| Host | Cloud Run MCP path `/mcp` (Team MCP binding named `instagram`) |
| Transport observed | Cursor MCP session live (Streamable HTTP details / Team-scope metadata **not** exposed by `environment-info` — not verified beyond namespace ready) |
| Account wiring | `list_accounts` → ig_user_id `17841407772120429` · label `env` · `dm_enabled: false` |
| Live Graph | **FAIL** — `live_check.ok=false` · Meta access token **expired** (oauth class) on 2026-09-09 |
| Desk `remote_access` | stays **`pending`** until `live_check.ok=true` + `get_profile` username `@velvets_cloud` |

### Owner action required (blocker)

Refresh the long-lived Instagram Graph API access token on the **Cloud Run / MCP host vault** (`INSTAGRAM_MCP_ACCESS_TOKEN` — value never in git). Then re-run from Cloud Agent:

1. `healthcheck` → expect `live_check.ok=true`
2. `get_profile` → `@velvets_cloud`
3. `list_media` (limit small, read-only)
4. `python3 scripts/vf_send_preflight.py --gate instagram` → `ready`
5. Only then set desk `remote_access: ready` and re-run `python3 scripts/check-all.py`

Until then: failover Canva + Drive + Gmail (`SEND.md`). Do not Publish. Do not claim the feed posted.

## Explicit non-goals of this note

- Do not paste tokens into the repo or PR
- Do not enable DM tools
- Do not make the Drive vault world-readable
- Do not mark `remote_access: ready` while `live_check.ok=false`
