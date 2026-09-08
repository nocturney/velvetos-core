# Instagram MCP · Remote autonomy (production path)

Status date: **2026-09-08**. No secrets in this file. No invented remote endpoint.

## Verdict (architecture choice)

| Option | Decision |
|---|---|
| A. Codespace port-forward | **Rejected for production** — Codespaces sleep/stop; not always reachable by Cloud Agent |
| B. GitHub-native always-on runtime | **Unavailable** — Actions are job-scoped; no free persistent MCP host in this repo |
| C. Minimal remote host of the same MCP package | **Chosen** — Fly.io app from `packages/vfigos/remote/` |

Canonical package remains [`adelaidasofia/instagram-mcp`](https://github.com/adelaidasofia/instagram-mcp) (`adelaidasofia-instagram-mcp`).  
VelvetOS adds a **thin Streamable HTTP + bearer gate** (`packages/vfigos/remote/serve.py`) that mounts upstream tools — no Graph rewrite, no second publishing SaaS.

Upstream itself is **stdio-only** (`mcp.run()` / `server.json` transport `stdio`). FastMCP 3.x nevertheless supports `transport="streamable-http"` — verified locally (401 without bearer; 29 tools with bearer).

## Roles

| Mode | Transport | When |
|---|---|---|
| **Production / Cloud autonomy** | Streamable HTTP `https://<host>/mcp` + `Authorization: Bearer …` | After deploy + successful remote healthcheck |
| **Dev / Codespace fallback** | stdio `instagram-mcp` | Local work; not sufficient for Cloud autonomy |

Desk fields (target after verified remote healthcheck):

```text
status: ready
auth: ready
transport: streamable-http
remote_access: ready
```

Until then (current truthful state):

```text
status: ready-codespace
auth: ready
transport: stdio
remote_access: pending
```

State file: [`packages/vfigos/live/remote-health.json`](../live/remote-health.json) — updated only by `scripts/vf_instagram_mcp_remote_health.py --write`.

## Secret names (values never in git)

| Name | Purpose |
|---|---|
| `INSTAGRAM_MCP_ACCESS_TOKEN` | Meta long-lived token (server-side only on the MCP host) |
| `INSTAGRAM_MCP_IG_USER_ID` | `17841407772120429` |
| `INSTAGRAM_MCP_APP_SECRET` | Optional Meta app secret |
| `VELVET_INSTAGRAM_MCP_BEARER_TOKEN` | Separate random gate token for Cloud → MCP (`>=24` chars; **not** the Meta token) |
| `INSTAGRAM_MCP_REMOTE_URL` | `https://<app>.fly.dev/mcp` (client / healthcheck) |
| `INSTAGRAM_MCP_DM_ENABLED` | **Must stay unset/false** |

## Exact deploy (Fly.io) — one unavoidable manual path

This Cloud Agent has **no** `FLY_API_TOKEN` / Instagram secrets, so remote cannot be marked ready from here.

Christian (or any operator with Fly + secrets) runs **once**:

```bash
# 0) Install flyctl: https://fly.io/docs/hands-on/install-flyctl/
# 1) Auth
fly auth login

# 2) From repo root
cd packages/vfigos/remote

# 3) Create app (name must match fly.toml or edit app=)
fly apps create velvet-instagram-mcp

# 4) Secrets — paste values only into Fly; never into git / chat / PR
fly secrets set \
  INSTAGRAM_MCP_ACCESS_TOKEN="…" \
  INSTAGRAM_MCP_IG_USER_ID="17841407772120429" \
  VELVET_INSTAGRAM_MCP_BEARER_TOKEN="…"   # openssl rand -hex 32

# 5) Deploy always-on machine (fly.toml sets min_machines_running=1, auto_stop=off)
fly deploy

# 6) Note endpoint
echo "https://velvet-instagram-mcp.fly.dev/mcp"
```

Then on any machine that can reach Fly (including a future Cloud Agent with secrets in the environment dashboard):

```bash
export INSTAGRAM_MCP_REMOTE_URL="https://velvet-instagram-mcp.fly.dev/mcp"
export VELVET_INSTAGRAM_MCP_BEARER_TOKEN="…"   # same gate token
python3 scripts/vf_instagram_mcp_remote_health.py --write --json
# Expect exit 0, remote_access=ready, accounts_configured>=1, live_check.ok=true, username velvets_cloud
```

Cursor Team MCP / Cloud Integrations — add HTTP server (do **not** commit filled mcp.json):

```json
"instagram": {
  "type": "http",
  "url": "https://velvet-instagram-mcp.fly.dev/mcp",
  "headers": {
    "Authorization": "Bearer ${env:VELVET_INSTAGRAM_MCP_BEARER_TOKEN}"
  }
}
```

After healthcheck exit 0: flip desk `remote_access` → `ready`, `transport` → `streamable-http`, `status` → `ready` in a follow-up commit (sensors refuse ready without `remote-health.json` ok).

## Healthcheck success criteria

- MCP transport reachable over HTTPS
- Bearer auth succeeds (401 without token)
- `healthcheck` tool runs
- `accounts_configured >= 1`
- `live_check.ok == true`
- account identity `@velvets_cloud` / IG id `17841407772120429`
- `dm_enabled` is false

## Failover / watchdog

- Remote down → `remote-health.json` `remote_access=degraded` → do **not** publish
- Keep drafts/approved queue; Canva+Drive+Gmail failover (`SEND.md`)
- Never switch to unofficial Instagram APIs
- Local Codespace stdio ≠ Cloud autonomy

## Local stdio (unchanged)

See [`DEPLOY-CODESPACE.md`](DEPLOY-CODESPACE.md) for Codespace/dev stdio. That path stays valid as fallback.

## Non-goals

- Metricool / Publer / Zapier / etc.
- Making Drive vault public
- Fake ready / invented endpoint
- Enabling DM tools
- Solving approved-derivative public media CDN in this deploy (separate pending gap if needed)
