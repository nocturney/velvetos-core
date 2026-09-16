#!/usr/bin/env bash
# Deploy VelvetOS Instagram MCP remote HTTP to Cloud Run.
# Secrets stay in Secret Manager — never pass raw tokens on the CLI.
# Build context is the repository root (approval library + capability SoT).
# Do NOT mount delivery-approval private key or issuer token onto this service.
set -euo pipefail

PROJECT="${GCP_PROJECT_ID:-${GCP_PROJECT:-instamcp}}"
# Prefer project ID (gcloud rejects project number for builds submit).
if [[ "$PROJECT" =~ ^[0-9]+$ ]]; then
  echo "Set GCP_PROJECT_ID to the project ID string (not the numeric project number $PROJECT)." >&2
  exit 1
fi
REGION="${GCP_REGION:-me-west1}"
SERVICE="${CLOUD_RUN_SERVICE:-velvet-instagram-mcp}"
IMAGE="${CLOUD_RUN_IMAGE:-gcr.io/${PROJECT}/${SERVICE}:delivery-approval-gate}"
REMOTE_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${REMOTE_DIR}/../../.." && pwd)"

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud not found. Install Google Cloud SDK and authenticate first." >&2
  exit 1
fi

if ! gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null | grep -q .; then
  echo "No active gcloud account. Run gcloud auth login / activate a service account, then retry." >&2
  exit 1
fi

echo "Building ${IMAGE} from repo root ${REPO_ROOT}"
gcloud builds submit "${REPO_ROOT}" \
  --project="${PROJECT}" \
  --config="${REPO_ROOT}/packages/vfigos/remote/cloudbuild.yaml" \
  --substitutions=_IMAGE="${IMAGE}"

echo "Deploying ${SERVICE} (${REGION})"
# IAM: allow unauthenticated at Cloud Run edge; app enforces Bearer.
# Secrets: GSM names (kebab) → Cloud Run env (SCREAMING). Do not echo values.
# Live project instamcp uses velvet-instagram-mcp-{bearer,access,ig-user}.
BEARER_SECRET="${GSM_BEARER_SECRET:-velvet-instagram-mcp-bearer}"
ACCESS_SECRET="${GSM_ACCESS_SECRET:-velvet-instagram-mcp-access}"
IG_USER_SECRET="${GSM_IG_USER_SECRET:-velvet-instagram-mcp-ig-user}"
SPEND_BUCKET="${VELVET_DELIVERY_APPROVAL_SPEND_BUCKET:-velvet-ig-approval-spend}"

# Refuse to attach issuer private key / issuer bearer if an operator mis-sets them.
if [[ -n "${GSM_DELIVERY_APPROVAL_PRIVATE_SECRET:-}" ]]; then
  echo "Refusing deploy: do not mount delivery-approval private key on the mutation service." >&2
  exit 1
fi

gcloud run deploy "${SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --image="${IMAGE}" \
  --allow-unauthenticated \
  --port=8080 \
  --set-env-vars="MCP_PATH=/mcp,HOST=0.0.0.0,VELVET_DELIVERY_APPROVAL_SPEND_BUCKET=${SPEND_BUCKET}" \
  --set-secrets="VELVET_INSTAGRAM_MCP_BEARER_TOKEN=${BEARER_SECRET}:latest,INSTAGRAM_MCP_ACCESS_TOKEN=${ACCESS_SECRET}:latest,INSTAGRAM_MCP_IG_USER_ID=${IG_USER_SECRET}:latest" \
  --quiet

URL="$(gcloud run services describe "${SERVICE}" --project="${PROJECT}" --region="${REGION}" --format='value(status.url)')"
echo "Deployed: ${URL}/mcp"
echo "ChatGPT Authentication: API key (Bearer = VELVET_INSTAGRAM_MCP_BEARER_TOKEN)"
echo "Write mutations require signed delivery approval + GCS spend claim (${SPEND_BUCKET})."
echo "mutation_service_has_private_key=NO"
echo "Smoke: python3 packages/vfigos/remote/smoke_public.py"
