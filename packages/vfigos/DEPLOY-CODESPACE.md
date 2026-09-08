# Instagram MCP · Codespace + remote autonomy

Status date: **2026-09-08**. No secrets in this file. No invented remote endpoint.

## Verified (Codespace / stdio)

| Check | Result |
|---|---|
| Package | `adelaidasofia-instagram-mcp` from [adelaidasofia/instagram-mcp](https://github.com/adelaidasofia/instagram-mcp) |
| Transport | **stdio** |
| Account | `@velvets_cloud` · IG user id `17841407772120429` · linked to Facebook Page |
| `add_account` | label `velvets_cloud` · default `true` |
| Smoke | `healthcheck` · `get_profile` · `list_media` OK |
| Secrets location | **GitHub Codespaces Secrets / runtime env only** — never git, never committed mcp.json with tokens |
| Desk status | `ready-codespace` · `auth: ready` · `transport: stdio` |

## Checklist — local / Codespace setup

1. Set Codespace (or machine) secrets: `INSTAGRAM_MCP_ACCESS_TOKEN`, `INSTAGRAM_MCP_IG_USER_ID` (optional `INSTAGRAM_MCP_APP_SECRET`).
2. Do **not** set `INSTAGRAM_MCP_DM_ENABLED`.
3. `pip install adelaidasofia-instagram-mcp` (or editable install from the clone).
4. Register MCP server name `instagram` with command `instagram-mcp` and env passthrough (see `packages/vfmcp/mcp.desktop.example.json`).
5. Reload MCP client → run `healthcheck` → confirm default account `velvets_cloud`.
6. Publishing still requires vault approval + Canva/vfcovers + PREFLIGHT + **live verify** after `publish_*`.

## Architectural gap — remote autonomy

| Item | Status |
|---|---|
| `remote-endpoint` | **pending** |
| Cloud Agent always-on Instagram MCP | **not solved** |
| stdio inside a **stopped / sleeping** Codespace | **insufficient** for full office autonomy |

VelvetOS goal: prepare → publish → verify → measure → learn with minimal owner clicks.  
Codespace stdio proves the Graph API path. It does **not** mean every Cloud Agent run can publish.

### Next step (engineering — not faked)

Expose a **supported remote MCP transport** or deploy the server in an **always-available** environment that Cursor Cloud / Team MCP can reach — still with secrets in the host vault, never in git. Until that lands:

- Desk keeps `remote_access: pending`
- Cloud / no-live-MCP runs use Canva + Drive + Gmail failover (`SEND.md`)
- Do not claim the feed is live without `liveVerified`

## Explicit non-goals of this note

- Do not invent a public HTTPS MCP URL
- Do not paste tokens into the repo or PR
- Do not enable DM tools
- Do not make the Drive vault world-readable
