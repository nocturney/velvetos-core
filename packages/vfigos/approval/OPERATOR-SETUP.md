# Delivery approval — operator setup (GCP)

Authenticated Instagram write mutations require a signed
`velvet.delivery_approval.v1` receipt from a **dedicated issuer** service.

## Status vocabulary

Do **not** claim these until the named step actually happened:

| Claim | Meaning |
|---|---|
| `DEPLOYED` | Issuer Cloud Run revision serving |
| `LIVE` | End-to-end issue → mutate → replay-block on production |
| `OWNER_AUTH_VERIFIED` | `gcloud` identity token invoke succeeded |
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

1. Service account: `velvet-delivery-approval-issuer@instamcp.iam.gserviceaccount.com`
2. GSM secrets (issuer SA accessor only):
   - `velvet-delivery-approval-ed25519-private` → `VELVET_DELIVERY_APPROVAL_PRIVATE_KEY_B64`
   - `velvet-delivery-approval-key-id` → `VELVET_DELIVERY_APPROVAL_KEY_ID`
   - optional defense-in-depth: issuer bearer (never MCP / mutation)
3. GCS bucket: `velvet-ig-approval-spend` (mutation SA: object create only; no delete)
4. Public keys: commit to `packages/vfigos/approval/keys/registry.json` (canonical verify source)

## Commands

```bash
# 1) Keygen (prints private to stdout once — store in GSM; commit public fragment only)
./packages/vfigos/approval/issuer/keygen.sh vf-da-2026-09

# 2) Create GSM secrets + SA + bucket (owner)
# 3) Append public key to registry.json; set active_signing_key_id; commit

# 4) Deploy issuer (IAM required — no --allow-unauthenticated)
./packages/vfigos/approval/issuer/deploy-issuer.sh

# 5) Grant yourself run.invoker; do NOT grant ChatGPT/Cursor MCP identities
gcloud run services add-iam-policy-binding velvet-delivery-approval-issuer \
  --member="user:OWNER@example.com" --role="roles/run.invoker" \
  --region=me-west1 --project=instamcp

# 6) Redeploy mutation service (spend bucket env; no private key)
./packages/vfigos/remote/deploy.sh

# 7) Smoke issue
TOKEN=$(gcloud auth print-identity-token)
curl -sS -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"content_id":"JOB","package_sha256":"<64hex>","mutation_tool":"publish_image"}' \
  "$ISSUER_URL/v1/delivery-approvals"
```

## ChatGPT / Cursor

Never install the issuer URL as an MCP server.
Never put issuer tokens or private keys in MCP config.
Public key registry in git is verification-only.
