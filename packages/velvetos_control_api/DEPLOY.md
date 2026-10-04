# Deploy — VelvetOS Control API

## Goal

Run the Control API as an isolated Cloud Run service that projects VelvetOS disk/adapters for the Control Center Site adapter.

This document describes the **intended** operational pattern. A live Cloud Run deploy is **not claimed** unless an operator actually ran and verified it.

## Service shape

| Item | Value |
|------|--------|
| Suggested service name | `velvetos-control-api` |
| Region | Prefer existing VF region (`me-west1` on project `instamcp`) unless the owner chooses otherwise |
| Ingress | Public Cloud Run invocation for this read-only projection gateway — `--allow-unauthenticated`; `/v1/*` remains app-token protected |
| Runtime SA | Dedicated SA with **read** access to the repo checkout / mounted projection data only |
| Secrets | `VELVETOS_CONTROL_API_TOKEN` from GSM only |
| Instance selection | `VELVETOS_INSTANCE_ID=velvet-factory` for the current VF deployment; code fails closed when absent |

## Isolation (hard rules)

Do **not** mount on this service:

- `INSTAGRAM_MCP_ACCESS_TOKEN`
- `VELVET_INSTAGRAM_MCP_BEARER_TOKEN`
- Delivery-approval Ed25519 private keys
- Any Meta Graph write credentials

The process calls `assert_isolation()` on boot and exits if those env vars are present.

## Auth

1. App bearer: GSM secret → env `VELVETOS_CONTROL_API_TOKEN` is mandatory for protected `/v1/*` reads.
2. Cloud Run invocation is public in the current Control Center topology so the private IAP-protected Site proxy can call the service with the app token. `/health` is intentionally unauthenticated.

The Site adapter must never expose the token to the browser. No wildcard CORS (Site proxies server-side). If the upstream is later moved back to IAM-only invocation, first enable and verify the Site identity-token path and grant the narrow server-side identity `roles/run.invoker`; do not change auth mode implicitly during a routine redeploy.

## Build

From repository root:

```bash
gcloud builds submit . --config packages/velvetos_control_api/cloudbuild.json --project "$GCP_PROJECT_ID"
```

Or:

```bash
docker build -f packages/velvetos_control_api/Dockerfile -t gcr.io/$GCP_PROJECT_ID/velvetos-control-api:dev .
```

## Deploy sketch (operator)

```bash
gcloud run deploy velvetos-control-api \
  --image "gcr.io/${GCP_PROJECT_ID}/velvetos-control-api:${TAG}" \
  --region "${GCP_REGION:-me-west1}" \
  --allow-unauthenticated \
  --service-account "velvetos-control-api@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --set-secrets "VELVETOS_CONTROL_API_TOKEN=velvetos-control-api-token:latest" \
  --set-env-vars "VELVETOS_INSTANCE_ID=velvet-factory" \
  --cpu 1 --memory 512Mi --max-instances 3
```

Do not remove the current `allUsers -> roles/run.invoker` binding during a routine Control API redeploy; application-token enforcement is the protected read boundary in this topology. The owner-facing Control Center itself remains private behind IAP.

## Failure semantics

| Situation | Behavior |
|-----------|----------|
| Process up, jobs cache not hydrated | `/health` → `service=ready`, `velvetos=degraded`; snapshot jobs collection `state=needs_sync`, `items=null` |
| Token unset | `/v1/*` → `503 NEEDS_OPERATOR_SETUP` |
| Bad/missing token | `401 UNAUTHORIZED` |
| Unknown / unwired action | reject with receipt; `CAPABILITY_UNAVAILABLE` / `UNKNOWN_ACTION` / `CAPABILITY_DENIED` |
| Unavailable domain | `items: null`, `count: null`, explicit `reason` |

## Data freshness

The container image copies catalog files at build time. For live office data (jobs cache, handoff, followups), prefer:

- mounting / syncing the office tree at revision deploy time, or
- rebuilding on a cadence from the canonical repo + ledger sync workflow,

without turning the Control API into a second jobs store. Jobs remain Sheet-canonical via `vf_jobs_adapter`.

## Verify after deploy (operator checklist)

1. `GET /health` → `service=ready` (unauthenticated probe ok).
2. `GET /v1/snapshot` without token → 401.
3. `GET /v1/snapshot` with bearer → `schema=velvetos.control.v1`, including canonical `integrations` / `collections.integrations` when the instance desk is packaged.
4. Confirm response has no secret material.
5. `POST /v1/actions` with `auto.dm` → denied receipt.

Do not mark this document as LIVE_VERIFIED until those checks are actually run.
