# Instagram MCP · Codespace / local stdio (dev + fallback)

Status date: **2026-09-08**. No secrets in this file. No invented remote endpoint.

**Production / Cloud autonomy path:** [`REMOTE.md`](REMOTE.md) (Google Cloud Run Streamable HTTP + bearer, scale-to-zero).  
This file is **dev / Codespace fallback only**. Codespace stdio ≠ `remote_access: ready`.

## Verified (Codespace / stdio)

| Check | Result |
|---|---|
| Package | `adelaidasofia-instagram-mcp` from [adelaidasofia/instagram-mcp](https://github.com/adelaidasofia/instagram-mcp) |
| Transport | **stdio** |
| Account | `@velvets_cloud` · IG user id `17841407772120429` · linked to Facebook Page |
| `add_account` | label `velvets_cloud` · default `true` |
| Smoke | `healthcheck` · `get_profile` · `list_media` OK |
| Secrets location | **GitHub Codespaces Secrets / runtime env only** — never git, never committed mcp.json with tokens |
| Desk status | `ready-codespace` · `auth: ready` · `transport: stdio` · `remote_access: pending` |

## Checklist — local / Codespace setup

1. Set Codespace (or machine) secrets: `INSTAGRAM_MCP_ACCESS_TOKEN`, `INSTAGRAM_MCP_IG_USER_ID` (optional `INSTAGRAM_MCP_APP_SECRET`).
2. Do **not** set `INSTAGRAM_MCP_DM_ENABLED`.
3. `pip install adelaidasofia-instagram-mcp` (or editable install from the clone).
4. Register MCP server name `instagram` with command `instagram-mcp` and env passthrough (see `packages/vfmcp/mcp.desktop.example.json`).
5. Reload MCP client → run `healthcheck` → confirm default account `velvets_cloud`.
6. Publishing still requires vault approval + Canva/vfcovers + PREFLIGHT + **live verify** after `publish_*`.

## Why this is not Cloud autonomy

| Item | Status |
|---|---|
| Codespace sleep / stop | Breaks always-on reachability |
| `remote_access` | Stays **pending** until [`REMOTE.md`](REMOTE.md) healthcheck exits 0 |
| Truth file | `packages/vfigos/live/remote-health.json` |

Until remote is verified:

- Desk keeps `remote_access: pending`
- Cloud / no-live-MCP runs use Canva + Drive + Gmail failover (`SEND.md`)
- Do not claim the feed is live without `liveVerified`
- Do not treat Codespace stdio as Cloud autonomy

## Explicit non-goals of this note

- Do not invent a public HTTPS MCP URL
- Do not paste tokens into the repo or PR
- Do not enable DM tools
- Do not make the Drive vault world-readable
- Do not mark `remote_access: ready` from Codespace alone
