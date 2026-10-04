#!/usr/bin/env bash
# Deploy velvetos-control-api to Cloud Run for the private Control Center proxy.
# NEVER mount Instagram / delivery-approval private credentials.
# This script is an operator helper — running it is not claimed by CI agents.
set -euo pipefail

PROJECT="${GCP_PROJECT_ID:-${GCP_PROJECT:-}}"
REGION="${GCP_REGION:-me-west1}"
SERVICE="${VELVETOS_CONTROL_API_SERVICE:-velvetos-control-api}"
SA_EMAIL="${VELVETOS_CONTROL_API_SA:-velvetos-control-api@${PROJECT}.iam.gserviceaccount.com}"
TOKEN_SECRET="${VELVETOS_CONTROL_API_TOKEN_SECRET:-velvetos-control-api-token}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

if [[ -z "${PROJECT}" ]]; then
  echo "Set GCP_PROJECT_ID" >&2
  exit 1
fi
if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud not found" >&2
  exit 1
fi

# Refuse if operator accidentally exports IG secrets into this shell for deploy
for bad in INSTAGRAM_MCP_ACCESS_TOKEN VELVET_INSTAGRAM_MCP_BEARER_TOKEN VELVET_DELIVERY_APPROVAL_ED25519_PRIVATE; do
  if [[ -n "${!bad:-}" ]]; then
    echo "Refusing deploy: unset $bad before deploying Control API" >&2
    exit 1
  fi
done

gcloud builds submit "${REPO_ROOT}" \
  --config "${REPO_ROOT}/packages/velvetos_control_api/cloudbuild.json" \
  --project "${PROJECT}"

IMAGE="gcr.io/${PROJECT}/velvetos-control-api:latest"

gcloud run deploy "${SERVICE}" \
  --project "${PROJECT}" \
  --region "${REGION}" \
  --image "${IMAGE}" \
  --allow-unauthenticated \
  --service-account "${SA_EMAIL}" \
  --set-secrets "VELVETOS_CONTROL_API_TOKEN=${TOKEN_SECRET}:latest" \
  --set-env-vars "VELVETOS_INSTANCE_ID=velvet-factory" \
  --cpu 1 \
  --memory 512Mi \
  --max-instances 3

echo "Deploy submitted. Verify unauthenticated GET /health=200, unauthenticated GET /v1/snapshot=401, then bearer-authenticated snapshot before claiming LIVE."
