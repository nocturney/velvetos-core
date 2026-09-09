# ChatGPT Business · Custom MCP Plugin · Instagram

Connect ChatGPT Business to the existing VelvetOS Instagram remote MCP.
Do **not** build a second Instagram integration. Do **not** put the Meta Graph token in ChatGPT.

## Root cause (2026-09-09 smoke)

Public endpoint: `https://velvet-instagram-mcp-1016876126699.me-west1.run.app/mcp`  
(alias also live: `INSTAGRAM_MCP_REMOTE_URL` / `…a.run.app/mcp`)

| ChatGPT Authentication | What happens | Why |
|---|---|---|
| **OAuth** | `Error fetching OAuth configuration — MCP server …/mcp does not implement OAuth` | Expected. Server uses static Bearer verification (`StaticTokenVerifier`), not OAuth discovery (no `/.well-known/oauth-protected-resource`). |
| **No Auth** | `Error creating connector — Something went wrong.` | Server returns **HTTP 401** `WWW-Authenticate: Bearer` on `initialize`. ChatGPT never completes connector creation. |
| **API key** (Bearer) | Works | Correct mode. Same gate Cursor Team MCP already uses via `VELVET_INSTAGRAM_MCP_BEARER_TOKEN`. |

Protocol smoke (with Bearer) from the public URL:

`initialize` → `notifications/initialized` → `tools/list` → `healthcheck` / `get_profile` / `list_media` — OK.  
`get_profile.profile.username` = `velvets_cloud`. No publish exercised.

## ChatGPT Business — CONNECTED + VERIFIED 2026-09-09

VelvetOS_Instagram plugin visible with 29 upstream tools (+ VelvetOS overlays after deploy).

| Check | Result |
|---|---|
| healthcheck | PASS |
| Graph reachable | PASS |
| default account | env |
| username | velvets_cloud |
| get_profile | PASS |
| list_media | PASS (7 live items) |
| get_account_insights (pre-patch) | FAIL — deprecated `impressions` + missing `metric_type=total_value` |
| publish_* | available · **not** live-tested this task |
| DM | disabled (Velvet policy) |

Insights fix lives in [`remote/insights_v21.py`](remote/insights_v21.py). Mark Insights **fixed** only after owner Cloud Run redeploy + `INSTAGRAM_MCP_INSIGHTS_EXPECT_FIXED=1 python3 packages/vfigos/remote/smoke_public.py`.

CTA audit (read-only): `audit_public_cta` / `audit_profile_cta` after deploy.  
Profile/caption writes: [`GRAPH-MUTATIONS.md`](GRAPH-MUTATIONS.md) — mostly `unsupported_by_official_graph`.

### Not an Instagram MCP issue

ChatGPT may also show a GitHub connector that returns “disabled” on invoke. That is ChatGPT/plugin-side state — do **not** change GitHub auth, tokens, Actions, or Apps from VelvetOS to “fix” it.

## What to choose in ChatGPT

1. Developer Mode / Create custom MCP connector.
2. **MCP Server URL:** `https://velvet-instagram-mcp-1016876126699.me-west1.run.app/mcp`
3. **Authentication: `API key`** (sometimes labeled Token / Access token).
4. Paste the **Velvet connector bearer** (`VELVET_INSTAGRAM_MCP_BEARER_TOKEN` from Secret Manager / Cursor secrets).
5. Header must be sent as `Authorization: Bearer <token>` (ChatGPT API-key mode does this when the key type is Bearer).
6. Do **not** paste `INSTAGRAM_MCP_ACCESS_TOKEN` (Meta) into ChatGPT.

If the UI only offers OAuth and No Auth (no API key), stop and escalate — do not flip the endpoint to No Auth. Write-capable Instagram tools must stay authenticated.

## Security laws

- Connector auth ≠ Meta Graph token. Two secrets:
  - `VELVET_INSTAGRAM_MCP_BEARER_TOKEN` — ChatGPT / Cursor → Cloud Run MCP
  - `INSTAGRAM_MCP_ACCESS_TOKEN` — MCP → Meta Graph (never leave the Cloud Run runtime / Secret Manager)
- No secrets in git.
- No auto-DM. No boost. No inventing ₪ / Insights.
- Publish still requires vault + Canva/vfcovers + PREFLIGHT + live verify (`CONNECT-IG.md`).

## Remote package (deploy source of truth)

HTTP entry for Cloud Run lives under [`remote/`](remote/README.md).

Overlays (do not fork the whole Instagram MCP):

| File | Role |
|---|---|
| `remote/insights_v21.py` | Graph v21 Insights metric_type split + sane defaults |
| `remote/mutations.py` | Honest `unsupported_by_official_graph` + gated `delete_media` |
| `remote/cta_tools.py` | Read-only `audit_public_cta` / `audit_profile_cta` |

Redeploy with owner `gcloud` (`./packages/vfigos/remote/deploy.sh`) after Insights/CTA/mutation overlays change. This Cloud Agent has **no GCP credentials** — report `CODE READY / DEPLOYMENT PENDING OWNER GCP` when deploy is blocked.

## Related

- [`CONNECT-IG.md`](CONNECT-IG.md)
- [`DEPLOY-CODESPACE.md`](DEPLOY-CODESPACE.md)
- [`CAPABILITIES.json`](CAPABILITIES.json)
- [`constitution/SEND.md`](../../constitution/SEND.md)
