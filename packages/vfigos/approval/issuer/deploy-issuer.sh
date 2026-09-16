#!/usr/bin/env bash
# Deploy velvet-delivery-approval-issuer to Cloud Run (IAM-authenticated).
# NEVER mount Meta Graph / Instagram MCP secrets onto this service.
# NEVER pass private key material on the CLI — GSM only.
set -euo pipefail

PROJECT="${GCP_PROJECT_ID:-${GCP_PROJECT:-instamcp}}"
if [[ "$PROJECT" =~ ^[0-9]+$ ]]; then
  echo "Set GCP_PROJECT_ID to the project ID string (not the numeric project number)." >&2
  exit 1
fi
REGION="${GCP_REGION:-me-west1}"
SERVICE="${DELIVERY_APPROVAL_ISSUER_SERVICE:-velvet-delivery-approval-issuer}"
IMAGE="${DELIVERY_APPROVAL_ISSUER_IMAGE:-gcr.io/${PROJECT}/${SERVICE}:v1}"
SA_EMAIL="${DELIVERY_APPROVAL_ISSUER_SA:-velvet-delivery-approval-issuer@${PROJECT}.iam.gserviceaccount.com}"
REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"

PRIVATE_SECRET="${GSM_DELIVERY_APPROVAL_PRIVATE_SECRET:-velvet-delivery-approval-ed25519-private}"
KEY_ID_SECRET="${GSM_DELIVERY_APPROVAL_KEY_ID_SECRET:-velvet-delivery-approval-key-id}"
# Optional defense-in-depth app bearer (issuer GSM only — never MCP / mutation service).
OPTIONAL_BEARER_SECRET="${GSM_DELIVERY_APPROVAL_ISSUER_BEARER_SECRET:-}"

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud not found. Owner setup required." >&2
  exit 1
fi
if ! gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null | grep -q .; then
  echo "No active gcloud account. Run gcloud auth login, then retry." >&2
  exit 1
fi

echo "Building ${IMAGE} from repo root ${REPO_ROOT}"
gcloud builds submit "${REPO_ROOT}" \
  --project="${PROJECT}" \
  --config="${REPO_ROOT}/packages/vfigos/approval/issuer/cloudbuild.yaml" \
  --substitutions=_IMAGE="${IMAGE}"

SET_SECRETS="VELVET_DELIVERY_APPROVAL_PRIVATE_KEY_B64=${PRIVATE_SECRET}:latest,VELVET_DELIVERY_APPROVAL_KEY_ID=${KEY_ID_SECRET}:latest"
if [[ -n "${OPTIONAL_BEARER_SECRET}" ]]; then
  SET_SECRETS="${SET_SECRETS},VELVET_DELIVERY_APPROVAL_ISSUER_TOKEN=${OPTIONAL_BEARER_SECRET}:latest"
fi

echo "Deploying ${SERVICE} (${REGION}) with IAM auth required (no --allow-unauthenticated)"
gcloud run deploy "${SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --image="${IMAGE}" \
  --service-account="${SA_EMAIL}" \
  --no-allow-unauthenticated \
  --port=8080 \
  --set-env-vars="HOST=0.0.0.0" \
  --set-secrets="${SET_SECRETS}" \
  --quiet

URL="$(gcloud run services describe "${SERVICE}" --project="${PROJECT}" --region="${REGION}" --format='value(status.url)')"
echo "Deployed issuer: ${URL}"
echo "Auth: Cloud Run IAM (run.invoker). Issue with:"
echo "  TOKEN=\$(gcloud auth print-identity-token)"
echo "  curl -H \"Authorization: Bearer \$TOKEN\" -H 'Content-Type: application/json' \\"
echo "    -d '{\"content_id\":\"JOB\",\"package_sha256\":\"<64hex>\",\"mutation_tool\":\"publish_image\"}' \\"
echo "    ${URL}/v1/delivery-approvals"
echo "Do NOT grant run.invoker to ChatGPT/Cursor/office MCP identities."
echo "Do NOT mount INSTAGRAM_MCP_ACCESS_TOKEN or VELVET_INSTAGRAM_MCP_BEARER_TOKEN here."
