# Delivery approval — operator setup (GCP)

Authenticated Instagram write mutations require a signed
`velvet.delivery_approval.v1` receipt from a **dedicated issuer** service.

## Status vocabulary

Do **not** claim these until the named step actually happened:

| Claim | Meaning |
|---|---|
| `DEPLOYED` | Issuer Cloud Run revision serving |
| `LIVE` | End-to-end issue → mutate → replay-block on production |
| `OWNER_AUTH_VERIFIED` | Owner-delegated, audience-bound identity-token invoke succeeded |
| `REPLAY_STORE_VERIFIED` | GCS `ifGenerationMatch=0` concurrent claim proven |
| `COLD_START_PASS` | Owner cold-start acceptance (separate from repo sensors) |

Until then report: **`NEEDS_OPERATOR_SETUP`**.

## Trust boundary

| Service | Has private key? | Has Meta token? | Has MCP bearer? | Auth |
|---|---|---|---|---|
| `velvet-delivery-approval-issuer` | YES (GSM only) | NO | NO | Cloud Run IAM (`run.invoker`) |
| `velvet-instagram-mcp` | **NO** | YES | YES | MCP Bearer + delivery receipt |

`MUTATION_SERVICE_HAS_PRIVATE_KEY` must remain **NO**.

## Resources (project `instamcp`, region `me-west1`)

1. Issuer service account: `velvet-delivery-issuer@instamcp.iam.gserviceaccount.com` (account ID `velvet-delivery-issuer`; IAM 6-30 characters; not the Cloud Run service name)
2. Mutation runtime service account: `velvet-instagram-mcp-runtime@instamcp.iam.gserviceaccount.com`. It must have **no project-level roles**; grant only Secret Manager accessor on the three Instagram MCP runtime secrets and `roles/storage.objectCreator` on `velvet-ig-approval-spend`. Production deploy accepts this exact identity only; never attach the default Compute service account or another override.
   The two vfigos Cloud Build configs pin the user-specified `velvet-vfigos-builder@instamcp.iam.gserviceaccount.com` identity with `CLOUD_LOGGING_ONLY`; keep it limited to Artifact Registry write, Cloud Logging write, and source-object read. The project default build identity is still probed so a future fallback cannot retain replay/signer mutation power. The Cloud Build identity (project default, plus any concrete `serviceAccount` in the strict JSON Cloud Build config) must be effectively denied issuer invocation and issuer `setIamPolicy`; project `resourcemanager.projects.setIamPolicy`; signing/Instagram secret reads and secret `setIamPolicy`; replay-bucket IAM/object mutation; and every protected service-account path used here to obtain credentials or mint a key (`setIamPolicy`, `actAs`, access/OIDC tokens, implicit delegation, signBlob/signJwt, key create; `iam.serviceAccountKeys.create` also authorizes the IAM `keys:upload` method). The dedicated mutation runtime is probed separately for the same signer/issuer escalation paths and for replay-bucket IAM/delete/update; its intended reads of the three Instagram runtime secrets and replay `storage.objects.create` are deliberately not denied by this gate. `deploy.sh` and `deploy-issuer.sh` run `gcloud policy-intelligence troubleshoot-policy iam` **before** Cloud Build starts. The gate resolves the actual default build service account, the numeric project number used in Secret Manager resource names, and any concrete build-config override. Only the exact pair `ALLOW_ACCESS_STATE_NOT_GRANTED` + `CANNOT_ACCESS` passes; command errors, malformed/unknown output or granted access fail closed. Remove broad project grants such as `roles/run.admin`, project-wide `roles/secretmanager.secretAccessor`, `roles/resourcemanager.projectIamAdmin`, `roles/iam.securityAdmin`, `roles/iam.serviceAccountAdmin` and `roles/iam.serviceAccountUser`; a role-name check alone is not sufficient proof. A passing repo sensor is not a live IAM proof and does not set `OWNER_AUTH_VERIFIED` or `LIVE`. Production resource names are fixed to `velvet-instagram-mcp`, `velvet-delivery-approval-issuer`, `velvet-delivery-approval-ed25519-private`, `velvet-delivery-approval-key-id`, the three named Instagram runtime secrets, and `velvet-ig-approval-spend`; the deploy scripts reject environment overrides before Cloud Build so the resources checked by the isolation preflight cannot drift from the resources deployed.
3. Build service account: `velvet-vfigos-builder@instamcp.iam.gserviceaccount.com`. The vfigos Cloud Build configs pin this exact identity and use `CLOUD_LOGGING_ONLY`. Grant only `roles/artifactregistry.writer` on the `gcr.io` Artifact Registry repository, `roles/logging.logWriter` on the project, and `roles/storage.objectViewer` on the Cloud Build source bucket `instamcp_cloudbuild`. Do not grant replay-bucket access, signer-secret access, Cloud Run invoke/admin, service-account impersonation/signing, project IAM mutation, `roles/cloudbuild.builds.builder`, or `roles/storage.admin`.
4. Owner invocation service account: `velvet-delivery-owner-invoker@instamcp.iam.gserviceaccount.com`. It has **no project-level roles** and only `roles/run.invoker` on the issuer service. The human owner gets only `roles/iam.serviceAccountOpenIdTokenCreator` on this service account, so an audience-bound ID token can be minted without granting service-account access tokens. Never grant that impersonation role to ChatGPT/Cursor/MCP identities.
5. GSM secrets (issuer SA accessor only):
   - `velvet-delivery-approval-ed25519-private` → `VELVET_DELIVERY_APPROVAL_PRIVATE_KEY_B64`
   - `velvet-delivery-approval-key-id` → `VELVET_DELIVERY_APPROVAL_KEY_ID`
   - optional defense-in-depth: issuer bearer (never MCP / mutation)
6. GCS bucket: `velvet-ig-approval-spend` (mutation SA: object create only; no delete).
7. Public keys: commit to `packages/vfigos/approval/keys/registry.json` (canonical verify source)

## Commands

```bash
# 1) Keygen (prints private to stdout once — store in GSM; commit public fragment only)
./packages/vfigos/approval/issuer/keygen.sh vf-da-2026-09

# 2) Create GSM secrets + SA + bucket (owner)
# 3) Append public key to registry.json; set active_signing_key_id; commit

# 4) Pin least-privilege Cloud Build execution. The config files already name this exact SA.
BUILD_SA="velvet-vfigos-builder@instamcp.iam.gserviceaccount.com"
DEFAULT_BUILD_SA="$(gcloud builds get-default-service-account --project=instamcp)"
# One-time grants: Artifact Registry Writer on gcr.io; Logging Writer on project;
# Storage Object Viewer only on gs://instamcp_cloudbuild. No replay-bucket grant.
# Remove broad fallback roles from DEFAULT_BUILD_SA, including roles/cloudbuild.builds.builder
# and roles/storage.admin; build_isolation.py proves the effective denials before every build.

# 5) Deploy issuer (IAM required — no --allow-unauthenticated)
./packages/vfigos/approval/issuer/deploy-issuer.sh

# 6) Owner invocation: use a dedicated audience-bound caller identity.
# Grant ONLY the human owner OpenID-token creation on velvet-delivery-owner-invoker,
# and grant that SA ONLY run.invoker on the issuer. Do not grant ChatGPT/Cursor/MCP identities.
OWNER_INVOKER_SA="velvet-delivery-owner-invoker@instamcp.iam.gserviceaccount.com"
ISSUER_URL="$(gcloud run services describe velvet-delivery-approval-issuer --region=me-west1 --project=instamcp --format='value(status.url)')"
TOKEN="$(gcloud auth print-identity-token --impersonate-service-account="${OWNER_INVOKER_SA}" --audiences="${ISSUER_URL}")"
curl -sS -H "Authorization: Bearer ${TOKEN}" "${ISSUER_URL}/healthz"
unset TOKEN

# 7) Redeploy mutation service (dedicated least-privilege runtime SA; spend bucket env; no private key)
# One-time IAM setup: create velvet-instagram-mcp-runtime with no project roles; grant only
# the three MCP secret accessors + bucket objectCreator described above.
./packages/vfigos/remote/deploy.sh

# 8) Smoke issue (issuer computes media_sha256s + mutation_payload_sha256 — never trust client digests)
# Re-mint the same delegated, audience-bound owner-invoker identity used for healthz.
TOKEN="$(gcloud auth print-identity-token --impersonate-service-account="${OWNER_INVOKER_SA}" --audiences="${ISSUER_URL}")"
# Media URLs must be content-addressed: .../sha256/<64-hex>/...
# Prefer media_artifacts bytes (issuer hashes) or let issuer fetch the CAS URL body.
curl -sS -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"content_id":"JOB","package_sha256":"<64hex>","mutation_tool":"publish_image","mutation_payload":{"image_url":"https://cdn.example/sha256/<mediahex>/a.jpg","caption":"…","account":"velvets_cloud"},"media_artifacts":[{"bytes_b64":"<base64 media bytes>"}]}' \
  "$ISSUER_URL/v1/delivery-approvals"
unset TOKEN
```

Body size for `/v1/delivery-approvals` is capped at 16 KiB (`ISSUER_MAX_BODY_BYTES`). Auth (optional app bearer) is checked before body buffering. Mutable non-CAS URLs are refused — Graph URL fetch is not byte identity.

Production CAS hosts: set `VELVET_MEDIA_CAS_HOST_SUFFIXES=cdn.example,storage.googleapis.com` on issuer + mutation service so only allowlisted content-addressed hosts may back Graph media. Objects at `/sha256/<digest>/` must be immutable (never overwrite bytes for a digest path).

## ChatGPT / Cursor

Never install the issuer URL as an MCP server.
Never put issuer tokens or private keys in MCP config.
Public key registry in git is verification-only.
