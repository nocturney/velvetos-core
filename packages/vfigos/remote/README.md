# Instagram MCP · Cloud Run remote HTTP

Source of truth for the VelvetOS Instagram **streamable-http** Cloud Run service.
Wraps canonical [`adelaidasofia-instagram-mcp`](https://github.com/adelaidasofia/instagram-mcp) with connector Bearer auth (not the Meta Graph token).

## Why this exists

ChatGPT Business Custom MCP + Cursor Team MCP need a public HTTPS `/mcp` endpoint.
The Meta long-lived token stays in Secret Manager as `INSTAGRAM_MCP_ACCESS_TOKEN`.
Clients authenticate with a **separate** bearer: `VELVET_INSTAGRAM_MCP_BEARER_TOKEN`.

ChatGPT must use **Authentication = API key**, not No Auth / OAuth. See [`../CHATGPT-MCP.md`](../CHATGPT-MCP.md).

## Env (names only — values in Secret Manager)

| Name | Role |
|---|---|
| `VELVET_INSTAGRAM_MCP_BEARER_TOKEN` | Connector auth (ChatGPT / Cursor → this service) |
| `INSTAGRAM_MCP_ACCESS_TOKEN` | Meta Graph (service → Instagram) |
| `INSTAGRAM_MCP_IG_USER_ID` | IG business account id |
| `INSTAGRAM_MCP_APP_SECRET` | optional Meta appsecret_proof |
| `PORT` | Cloud Run port (default 8080) |
| `MCP_PATH` | default `/mcp` |

Never set `INSTAGRAM_MCP_DM_ENABLED` for VelvetOS HQ.

## Local run

```bash
pip install 'adelaidasofia-instagram-mcp>=0.1.2' 'fastmcp>=3.4.2,<4' uvicorn starlette
export VELVET_INSTAGRAM_MCP_BEARER_TOKEN=…  # from Secret Manager
export INSTAGRAM_MCP_ACCESS_TOKEN=…         # from Secret Manager
export INSTAGRAM_MCP_IG_USER_ID=17841407772120429
python3 -m packages.vfigos.remote.http_server
# or from this directory:
python3 http_server.py
```

## Deploy (owner / CI with gcloud)

```bash
./packages/vfigos/remote/deploy.sh
```

Requires authenticated `gcloud` for project `1016876126699` (or `GCP_PROJECT`) region `me-west1`, service `velvet-instagram-mcp`. Secrets stay in Secret Manager — never flags with raw tokens.

## Smoke

```bash
python3 packages/vfigos/remote/smoke_public.py
```

Uses `INSTAGRAM_MCP_REMOTE_URL` + `VELVET_INSTAGRAM_MCP_BEARER_TOKEN`. No publish.
