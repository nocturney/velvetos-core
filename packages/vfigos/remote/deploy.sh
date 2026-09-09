#!/usr/bin/env bash
# Deploy VelvetOS Instagram MCP remote HTTP to Cloud Run.
# Secrets stay in Secret Manager — never pass raw tokens on the CLI.
set -euo pipefail

PROJECT="${GCP_PROJECT_ID:-${GCP_PROJECT:-velvet-factory}}"
# Prefer project ID (gcloud rejects project number for builds submit).
if [[ "$PROJECT" =~ ^[0-9]+$ ]]; then
  echo "Set GCP_PROJECT_ID to the project ID string (not the numeric project number $PROJECT)." >&2
  exit 1
fi
REGION="${GCP_REGION:-me-west1}"
SERVICE="${CLOUD_RUN_SERVICE:-velvet-instagram-mcp}"
IMAGE="${CLOUD_RUN_IMAGE:-gcr.io/${PROJECT}/${SERVICE}:chatgpt-connector}"
ROOT="$(cd "$(dirname "$0")" && pwd)"

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud not found. Install Google Cloud SDK and authenticate first." >&2
  exit 1
fi

if ! gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null | grep -q .; then
  echo "No active gcloud account. Run gcloud auth login / activate a service account, then retry." >&2
  exit 1
fi

echo "Building ${IMAGE} from ${ROOT}"
gcloud builds submit "${ROOT}" \
  --project="${PROJECT}" \
  --tag="${IMAGE}"

echo "Deploying ${SERVICE} (${REGION})"
# IAM: allow unauthenticated at Cloud Run edge; app enforces Bearer.
# Secrets: map GSM secrets → env (create/update secrets out-of-band; do not echo values).
gcloud run deploy "${SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --image="${IMAGE}" \
  --allow-unauthenticated \
  --port=8080 \
  --set-env-vars="MCP_PATH=/mcp,HOST=0.0.0.0" \
  --set-secrets="VELVET_INSTAGRAM_MCP_BEARER_TOKEN=VELVET_INSTAGRAM_MCP_BEARER_TOKEN:latest,INSTAGRAM_MCP_ACCESS_TOKEN=INSTAGRAM_MCP_ACCESS_TOKEN:latest,INSTAGRAM_MCP_IG_USER_ID=INSTAGRAM_MCP_IG_USER_ID:latest" \
  --quiet

URL="$(gcloud run services describe "${SERVICE}" --project="${PROJECT}" --region="${REGION}" --format='value(status.url)')"
echo "Deployed: ${URL}/mcp"
echo "ChatGPT Authentication: API key (Bearer = VELVET_INSTAGRAM_MCP_BEARER_TOKEN)"
echo "Smoke: python3 packages/vfigos/remote/smoke_public.py"
