# Instagram MCP · Remote autonomy (production path — Google Cloud Run)

Status date: **2026-09-08**. No secrets in this file. No invented remote endpoint.

## Why Cloud Run (not Fly / not always-on)

| Option | Decision |
|---|---|
| A. Codespace port-forward | **Rejected** — sleeps/stops; not always reachable by Cloud Agent |
| B. GitHub-native always-on | **Unavailable** — Actions are job-scoped |
| C′. Fly.io always-on machine | **Superseded** — paid always-on min instance defeats cost goal; see `remote/LEGACY-FLY.toml` |
| **C. Google Cloud Run** | **Chosen** — fixed HTTPS URL, scale-to-zero, wakes on request, low-volume MCP fit |

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
| **Production / Cloud autonomy** | Streamable HTTP `https://<cloud-run-url>/mcp` + `Authorization: Bearer …` | After deploy + successful remote healthcheck |
| **Dev / Codespace fallback** | stdio `instagram-mcp` | Local work; **not** Cloud autonomy |

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
remoteTransportPreferred: streamable-http
```

State file: [`packages/vfigos/live/remote-health.json`](live/remote-health.json) — updated only by `scripts/vf_instagram_mcp_remote_health.py --write`.

## Region

Default: **`me-west1` (Tel Aviv)** — [Cloud Run locations](https://cloud.google.com/run/docs/locations) list `me-west1`. Closest practical region to Israel. Override with `REGION=…` if the project lacks that region.

## Secret names (values never in git)

| Name | Purpose |
|---|---|
| `INSTAGRAM_MCP_ACCESS_TOKEN` | Meta long-lived token (**server-side only** on Cloud Run) |
| `INSTAGRAM_MCP_IG_USER_ID` | `17841407772120429` |
| `INSTAGRAM_MCP_APP_SECRET` | Optional Meta app secret |
| `VELVET_INSTAGRAM_MCP_BEARER_TOKEN` | Separate random gate token Cloud Agent → MCP (`>=24` chars; **not** the Meta token) |
| `INSTAGRAM_MCP_REMOTE_URL` | `https://<service>-<hash>-<region>.a.run.app/mcp` (client / healthcheck) |
| `INSTAGRAM_MCP_DM_ENABLED` | **Must stay unset/false** |

Use Secret Manager + `gcloud run deploy --set-secrets`. Never paste values into Cursor chat, PR, or git.

## Exact deploy (Cloud Run) — one unavoidable manual path

This Cloud Agent has **no** `gcloud` project login / Instagram secrets, so remote cannot be marked ready from here.

Christian runs **once** (placeholders only — never commit real tokens):

```bash
# A) Install gcloud CLI if needed: https://cloud.google.com/sdk/docs/install
# B) Auth + project
gcloud auth login
export PROJECT_ID="YOUR_GCP_PROJECT_ID"
export REGION="me-west1"          # Tel Aviv — change only if unavailable
export SERVICE_NAME="velvet-instagram-mcp"
gcloud config set project "$PROJECT_ID"

# C) Enable APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com

# D) Create secrets (paste META token into prompt / Secret Manager UI — not into chat)
#    Generate ONE bearer and reuse it for Cloud Run + Cloud Agent env.
export BEARER_TOKEN="$(openssl rand -hex 32)"
# Save BEARER_TOKEN somewhere safe (password manager). Same value must be:
#   - stored in Secret Manager / Cloud Run
#   - set as VELVET_INSTAGRAM_MCP_BEARER_TOKEN on the Cloud Agent / Team MCP
# Do NOT regenerate separately on client vs server.

printf '%s' "$BEARER_TOKEN" | gcloud secrets create velvet-instagram-mcp-bearer --data-file=-
# META_TOKEN: set locally in your shell from password manager — do not echo to logs
printf '%s' "$META_TOKEN" | gcloud secrets create velvet-instagram-mcp-access --data-file=-
printf '%s' "17841407772120429" | gcloud secrets create velvet-instagram-mcp-ig-user --data-file=-

# Grant Cloud Run runtime SA access to secrets (replace SA if your project differs)
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
RUNTIME_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
for S in velvet-instagram-mcp-bearer velvet-instagram-mcp-access velvet-instagram-mcp-ig-user; do
  gcloud secrets add-iam-policy-binding "$S" \
    --member="serviceAccount:${RUNTIME_SA}" \
    --role="roles/secretmanager.secretAccessor"
done

# E–F) Deploy from wrapper directory (buildpacks/Cloud Build from Dockerfile)
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

# --allow-unauthenticated = Cloud Run IAM open; MCP still requires Authorization: Bearer
# (app-layer gate in serve.py). Do not disable the bearer.

# G) Service URL
export SERVICE_URL="$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format='value(status.url)')"
echo "INSTAGRAM_MCP_REMOTE_URL=${SERVICE_URL}/mcp"
```

## H–I) Remote healthcheck (required before desk flip)

```bash
export INSTAGRAM_MCP_REMOTE_URL="${SERVICE_URL}/mcp"
export VELVET_INSTAGRAM_MCP_BEARER_TOKEN="$BEARER_TOKEN"   # SAME token as Secret Manager
python3 scripts/vf_instagram_mcp_remote_health.py --write --json
# Expect exit 0, remote_access=ready, accounts_configured>=1, live_check.ok=true, username velvets_cloud
```

Cursor Team MCP / Cloud Integrations — add HTTP server (do **not** commit filled mcp.json):

```json
"instagram": {
  "type": "http",
  "url": "${env:INSTAGRAM_MCP_REMOTE_URL}",
  "headers": {
    "Authorization": "Bearer ${env:VELVET_INSTAGRAM_MCP_BEARER_TOKEN}"
  }
}
```

After healthcheck exit 0: flip desk `remote_access` → `ready`, `transport` → `streamable-http`, `status` → `ready` in a follow-up commit (sensors refuse ready without `remote-health.json` ok).

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
- Local Codespace stdio ≠ Cloud autonomy

## Local stdio (unchanged)

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
