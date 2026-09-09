# Instagram MCP · Remote autonomy (production path — Google Cloud Run)

Status date: **2026-09-09**. No secrets in this file. Live endpoint evidence: [`live/remote-health.json`](live/remote-health.json).

## Why Cloud Run (not Fly / not always-on)

| Option | Decision |
|---|---|
| A. Codespace port-forward | **Rejected** — sleeps/stops; not always reachable by Cloud Agent |
| B. GitHub-native always-on | **Unavailable** — Actions are job-scoped |
| C′. Fly.io always-on machine | **Superseded** — paid always-on min instance defeats cost goal; see `remote/LEGACY-FLY.toml` |
| **C. Google Cloud Run** | **Chosen + live** — fixed HTTPS URL, scale-to-zero, wakes on request, low-volume MCP fit |

Cloud Run benefits for this workload:

- Stable HTTPS endpoint (no local computer / open Codespace)
- **Scale to zero** (`min instances = 0`) — no always-on process
- Cold start acceptable for office MCP traffic
- Likely stays within free-tier / low spend for sparse healthchecks + occasional publish
- Billing and free-tier limits are **external and may change** — do not promise “guaranteed free forever”

Canonical package remains [`adelaidasofia/instagram-mcp`](https://github.com/adelaidasofia/instagram-mcp) (`adelaidasofia-instagram-mcp`).  
VelvetOS adds a **thin Streamable HTTP + bearer gate** (`packages/vfigos/remote/serve.py`) — no Graph rewrite, no second publishing SaaS.

Upstream itself is **stdio-only**. FastMCP 3.x supports `transport="streamable-http"`. Container listens on `$PORT` (Cloud Run) at path `/mcp`.

## Roles

| Mode | Transport | When |
|---|---|---|
| **Production / Cloud autonomy** | Streamable HTTP `https://…/mcp` + `Authorization: Bearer …` | **Live** — Cloud Run `velvet-instagram-mcp` · `me-west1` · project `instamcp` |
| **Dev / Codespace fallback** | stdio `instagram-mcp` | Local work; **not** a replacement for Cloud autonomy |

Desk fields (verified 2026-09-09 after remote healthcheck exit 0):

```text
status: ready
auth: ready
transport: streamable-http
remote_access: ready
```

Local stdio remains documented as fallback (`DEPLOY-CODESPACE.md`).

State file: [`packages/vfigos/live/remote-health.json`](live/remote-health.json) — updated only by `scripts/vf_instagram_mcp_remote_health.py --write`.

## Live deploy facts (no secrets)

| Field | Value |
|---|---|
| GCP project | `instamcp` |
| Region | `me-west1` |
| Service | `velvet-instagram-mcp` |
| Path | `/mcp` |
| Scale | min=0 · max=1 · memory 512Mi |
| Evidence | `live/remote-health.json` (`ok=true`, account `@velvets_cloud`) |

Client env (values never in git):

- `INSTAGRAM_MCP_REMOTE_URL` = service URL + `/mcp` (from `gcloud run services describe` or remote-health `endpoint`)
- `VELVET_INSTAGRAM_MCP_BEARER_TOKEN` = same Secret Manager value as Cloud Run (`velvet-instagram-mcp-bearer`)

**Paste hygiene (Cloud Agent / Team secrets):** paste URL and bearer as single-line values with **no** leading/trailing newlines and **no** spaces inside the bearer. A single space inside the bearer yields `401 invalid_token`. Diagnose with `python3 scripts/vf_instagram_mcp_remote_health.py --json` (exits `1` on `bearer_internal_whitespace`). Recovery probe only: `--sanitize-whitespace` (still re-save clean Team secrets afterward).

## Region

Default: **`me-west1` (Tel Aviv)** — verified supported for this project. Override with `REGION=…` only if unavailable.

## Secret names (values never in git)

| Name | Purpose |
|---|---|
| `INSTAGRAM_MCP_ACCESS_TOKEN` | Meta long-lived token (**server-side only** on Cloud Run) |
| `INSTAGRAM_MCP_IG_USER_ID` | `17841407772120429` |
| `INSTAGRAM_MCP_APP_SECRET` | Optional Meta app secret |
| `VELVET_INSTAGRAM_MCP_BEARER_TOKEN` | Separate random gate token Cloud Agent → MCP (`>=24` chars; **not** the Meta token) |
| `INSTAGRAM_MCP_REMOTE_URL` | `https://…/mcp` (client / healthcheck) |
| `INSTAGRAM_MCP_DM_ENABLED` | **Must stay unset/false** |

Secret Manager ids: `velvet-instagram-mcp-access` · `velvet-instagram-mcp-ig-user` · `velvet-instagram-mcp-bearer`.  
Use Secret Manager + `gcloud run deploy --set-secrets`. Never paste values into Cursor chat, PR, or git.

## Redeploy (Cloud Run)

```bash
export PROJECT_ID="instamcp"
export REGION="me-west1"
export SERVICE_NAME="velvet-instagram-mcp"
gcloud config set project "$PROJECT_ID"

cd packages/vfigos/remote
gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --min-instances=0 \
  --max-instances=1 \
  --memory=512Mi \
  --cpu=1 \
  --timeout=300 \
  --set-secrets="INSTAGRAM_MCP_ACCESS_TOKEN=velvet-instagram-mcp-access:latest,INSTAGRAM_MCP_IG_USER_ID=velvet-instagram-mcp-ig-user:latest,VELVET_INSTAGRAM_MCP_BEARER_TOKEN=velvet-instagram-mcp-bearer:latest" \
  --set-env-vars="INSTAGRAM_MCP_HOST=0.0.0.0,INSTAGRAM_MCP_PATH=/mcp,INSTAGRAM_MCP_TRANSPORT=streamable-http"

export SERVICE_URL="$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format='value(status.url)')"
export INSTAGRAM_MCP_REMOTE_URL="${SERVICE_URL}/mcp"
# Bearer: access Secret Manager locally — do not echo
export VELVET_INSTAGRAM_MCP_BEARER_TOKEN="$(gcloud secrets versions access latest --secret=velvet-instagram-mcp-bearer)"
python3 scripts/vf_instagram_mcp_remote_health.py --write --json
```

`--allow-unauthenticated` = Cloud Run IAM open; MCP still requires `Authorization: Bearer` (app-layer gate in `serve.py`).

## Cloud Agent / Team MCP

```json
"instagram": {
  "type": "http",
  "url": "${env:INSTAGRAM_MCP_REMOTE_URL}",
  "headers": {
    "Authorization": "Bearer ${env:VELVET_INSTAGRAM_MCP_BEARER_TOKEN}"
  }
}
```

Set both env vars in Cursor Team / Cloud Integrations **and** register the HTTP MCP server (`type: http`) so the Cloud Agent tool catalog exposes namespace `instagram`. Env alone is not enough for Cursor `CallDynamicTool` — without Team MCP binding, consumer verification uses `scripts/vf_instagram_mcp_remote_health.py` over Streamable HTTP. Never commit filled mcp.json. Never put the Meta Graph token in the Cloud Agent client.

## Healthcheck success criteria

- MCP transport reachable over HTTPS (Cloud Run)
- Bearer auth succeeds (401 without token)
- `healthcheck` tool runs
- `accounts_configured >= 1`
- `live_check.ok == true`
- account identity `@velvets_cloud` / IG id `17841407772120429`
- `dm_enabled` is false

## Failover / watchdog

- Remote down / cold-start fail / auth fail → `remote-health.json` `remote_access=degraded` → do **not** publish
- Keep drafts/approved queue; Canva+Drive+Gmail failover (`SEND.md`)
- Never switch to unofficial Instagram APIs
- Local Codespace stdio ≠ Cloud autonomy replacement when remote is degraded

## Local stdio (unchanged fallback)

See [`DEPLOY-CODESPACE.md`](DEPLOY-CODESPACE.md) for Codespace/dev stdio. That path stays valid as fallback.

## Legacy Fly

Do not deploy with Fly for new work. Historical config: [`remote/LEGACY-FLY.toml`](remote/LEGACY-FLY.toml).

## Non-goals

- Metricool / Publer / Zapier / etc.
- Making Drive vault public
- Fake ready / invented endpoint
- Enabling DM tools
- Always-on min instances (defeats cost goal)
- Solving approved-derivative public media CDN in this deploy (separate pending gap if needed)
