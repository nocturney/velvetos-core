#!/usr/bin/env bash
# Deploy velvet-delivery-approval-issuer to Cloud Run (IAM-authenticated).
# NEVER mount Meta Graph / Instagram MCP secrets onto this service.
# NEVER pass private key material on the CLI — GSM only.
set -euo pipefail

PROJECT="${GCP_PROJECT_ID:-${GCP_PROJECT:-instamcp}}"
if [[ "$PROJECT" =~ ^[0-9]+$ ]]; then
  echo "Set GCP_PROJECT_ID to the project ID string (not numeric)." >&2
  exit 1
fi
REGION="${GCP_REGION:-me-west1}"
EXPECTED_PROJECT="instamcp"
EXPECTED_REGION="me-west1"
EXPECTED_ISSUER_SERVICE="velvet-delivery-approval-issuer"
SERVICE="${DELIVERY_APPROVAL_ISSUER_SERVICE:-velvet-delivery-approval-issuer}"
IMAGE="${DELIVERY_APPROVAL_ISSUER_IMAGE:-gcr.io/${PROJECT}/${SERVICE}:v1}"
EXPECTED_ISSUER_SA="velvet-delivery-issuer@${PROJECT}.iam.gserviceaccount.com"
EXPECTED_OWNER_INVOKER_SA="velvet-delivery-owner-invoker@${PROJECT}.iam.gserviceaccount.com"
SA_EMAIL="${DELIVERY_APPROVAL_ISSUER_SA:-velvet-delivery-issuer@${PROJECT}.iam.gserviceaccount.com}"
REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
BUILD_CONFIG="${REPO_ROOT}/packages/vfigos/approval/issuer/cloudbuild.json"

EXPECTED_PRIVATE_SECRET="velvet-delivery-approval-ed25519-private"
EXPECTED_KEY_ID_SECRET="velvet-delivery-approval-key-id"
EXPECTED_OPTIONAL_BEARER_SECRET="velvet-delivery-approval-issuer-bearer"
PRIVATE_SECRET="${GSM_DELIVERY_APPROVAL_PRIVATE_SECRET:-velvet-delivery-approval-ed25519-private}"
KEY_ID_SECRET="${GSM_DELIVERY_APPROVAL_KEY_ID_SECRET:-velvet-delivery-approval-key-id}"
OPTIONAL_BEARER_SECRET="${GSM_DELIVERY_APPROVAL_ISSUER_BEARER_SECRET:-}"
CAS_HOST_SUFFIXES="${VELVET_MEDIA_CAS_HOST_SUFFIXES:-storage.googleapis.com}"
BOOTSTRAP="${VELVET_DELIVERY_APPROVAL_BOOTSTRAP:-0}"
BOOTSTRAP_DEPLOY_FLAGS=()
BOOTSTRAP_SERVICE_PENDING=0
POLICY_FILE=""

cleanup_issuer_deploy() {
  if [[ -n "${POLICY_FILE}" ]]; then
    rm -f "${POLICY_FILE}"
  fi
  if [[ "${BOOTSTRAP_SERVICE_PENDING}" == "1" ]]; then
    echo "Bootstrap isolation did not complete; deleting unpromoted issuer service." >&2
    gcloud run services delete "${SERVICE}" \
      --project="${PROJECT}" \
      --region="${REGION}" \
      --quiet >/dev/null 2>&1 || \
      echo "WARNING: failed to delete unpromoted bootstrap issuer; it was deployed with zero traffic." >&2
  fi
}
trap cleanup_issuer_deploy EXIT

if [[ "${PROJECT}" != "${EXPECTED_PROJECT}" ]]; then
  echo "Refusing deploy: project must remain ${EXPECTED_PROJECT}." >&2
  exit 1
fi
if [[ "${REGION}" != "${EXPECTED_REGION}" ]]; then
  echo "Refusing deploy: region must remain ${EXPECTED_REGION}." >&2
  exit 1
fi
if [[ -n "${OPTIONAL_BEARER_SECRET}" && "${OPTIONAL_BEARER_SECRET}" != "${EXPECTED_OPTIONAL_BEARER_SECRET}" ]]; then
  echo "Refusing deploy: optional issuer bearer secret must remain ${EXPECTED_OPTIONAL_BEARER_SECRET} or be empty." >&2
  exit 1
fi
if [[ "${BOOTSTRAP}" != "0" && "${BOOTSTRAP}" != "1" ]]; then
  echo "Refusing deploy: VELVET_DELIVERY_APPROVAL_BOOTSTRAP must be 0 or 1." >&2
  exit 1
fi

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud not found. Owner setup required." >&2
  exit 1
fi
if ! gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null | grep -q .; then
  echo "No active gcloud account. Authenticate, then retry." >&2
  exit 1
fi

if [[ "${SA_EMAIL}" != "${EXPECTED_ISSUER_SA}" ]]; then
  echo "Refusing deploy: issuer must use ${EXPECTED_ISSUER_SA}." >&2
  exit 1
fi
if [[ "${SERVICE}" != "${EXPECTED_ISSUER_SERVICE}" ]]; then
  echo "Refusing deploy: issuer service must remain ${EXPECTED_ISSUER_SERVICE}." >&2
  exit 1
fi
if [[ "${PRIVATE_SECRET}" != "${EXPECTED_PRIVATE_SECRET}" ]]; then
  echo "Refusing deploy: signing secret must remain ${EXPECTED_PRIVATE_SECRET}." >&2
  exit 1
fi
if [[ "${KEY_ID_SECRET}" != "${EXPECTED_KEY_ID_SECRET}" ]]; then
  echo "Refusing deploy: key-id secret must remain ${EXPECTED_KEY_ID_SECRET}." >&2
  exit 1
fi
if [[ ! "${CAS_HOST_SUFFIXES}" =~ ^[A-Za-z0-9.-]+(,[A-Za-z0-9.-]+)*$ ]]; then
  echo "Refusing deploy: invalid VELVET_MEDIA_CAS_HOST_SUFFIXES." >&2
  exit 1
fi
if [[ "${CAS_HOST_SUFFIXES}" == *"|"* || "${CAS_HOST_SUFFIXES}" == *"^"* ]]; then
  echo "Refusing deploy: CAS host list contains reserved delimiter" >&2
  exit 1
fi

if [[ "${BOOTSTRAP}" == "1" ]]; then
  EXISTING_ISSUERS="$(gcloud run services list \
    --platform=managed \
    --project="${PROJECT}" \
    --region="${REGION}" \
    --format='value(metadata.name)')"
  if printf '%s\n' "${EXISTING_ISSUERS}" | grep -Fxq "${SERVICE}"; then
    echo "Refusing bootstrap: issuer service already exists; use normal deploy mode." >&2
    exit 1
  fi
  python3 "${REPO_ROOT}/packages/vfigos/approval/build_isolation.py" \
    --project "${PROJECT}" \
    --region "${REGION}" \
    --cloudbuild-config "${BUILD_CONFIG}" \
    --issuer-resource-absent
  BOOTSTRAP_DEPLOY_FLAGS=(--no-traffic)
else
  python3 "${REPO_ROOT}/packages/vfigos/approval/build_isolation.py" \
    --project "${PROJECT}" \
    --region "${REGION}" \
    --cloudbuild-config "${BUILD_CONFIG}" \
    --require-issuer-policy
fi

echo "Building ${IMAGE} from repo root ${REPO_ROOT}"
gcloud builds submit "${REPO_ROOT}" \
  --project="${PROJECT}" \
  --config="${BUILD_CONFIG}" \
  --substitutions=_IMAGE="${IMAGE}"

SET_SECRETS="VELVET_DELIVERY_APPROVAL_PRIVATE_KEY_B64=${PRIVATE_SECRET}:latest,VELVET_DELIVERY_APPROVAL_KEY_ID=${KEY_ID_SECRET}:latest"
if [[ -n "${OPTIONAL_BEARER_SECRET}" ]]; then
  SET_SECRETS="${SET_SECRETS},VELVET_DELIVERY_APPROVAL_ISSUER_TOKEN=${OPTIONAL_BEARER_SECRET}:latest"
fi

if [[ "${BOOTSTRAP}" == "1" ]]; then
  BOOTSTRAP_SERVICE_PENDING=1
fi

echo "Deploying ${SERVICE} (${REGION}) with IAM auth required"
gcloud run deploy "${SERVICE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --image="${IMAGE}" \
  --service-account="${SA_EMAIL}" \
  --no-allow-unauthenticated \
  --port=8080 \
  --set-env-vars="^|^HOST=0.0.0.0|VELVET_MEDIA_CAS_HOST_SUFFIXES=${CAS_HOST_SUFFIXES}" \
  --set-secrets="${SET_SECRETS}" \
  "${BOOTSTRAP_DEPLOY_FLAGS[@]}" \
  --quiet

POLICY_FILE="$(mktemp)"
cat >"${POLICY_FILE}" <<EOF
{"bindings":[{"role":"roles/run.invoker","members":["serviceAccount:${EXPECTED_OWNER_INVOKER_SA}"]}]}
EOF
gcloud run services set-iam-policy "${SERVICE}" "${POLICY_FILE}" \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --quiet
if [[ "${BOOTSTRAP}" == "1" ]]; then
  python3 "${REPO_ROOT}/packages/vfigos/approval/build_isolation.py" \
    --project "${PROJECT}" \
    --region "${REGION}" \
    --cloudbuild-config "${BUILD_CONFIG}" \
    --require-issuer-policy
  gcloud run services update-traffic "${SERVICE}" \
    --project="${PROJECT}" \
    --region="${REGION}" \
    --to-latest \
    --quiet
  BOOTSTRAP_SERVICE_PENDING=0
else
  python3 "${REPO_ROOT}/packages/vfigos/approval/build_isolation.py" \
    --project "${PROJECT}" \
    --region "${REGION}" \
    --cloudbuild-config "${BUILD_CONFIG}" \
    --issuer-policy-only
fi

URL="$(gcloud run services describe "${SERVICE}" --project="${PROJECT}" --region="${REGION}" --format='value(status.url)')"
echo "Deployed issuer: ${URL}"
echo "Auth: Cloud Run IAM (run.invoker)."
echo "Use the delegated owner-invoker, audience-bound token recipe in OPERATOR-SETUP.md."
echo "Do NOT grant run.invoker to ChatGPT/Cursor/office MCP identities."
echo "Do NOT mount INSTAGRAM_MCP_ACCESS_TOKEN or VELVET_INSTAGRAM_MCP_BEARER_TOKEN here."
