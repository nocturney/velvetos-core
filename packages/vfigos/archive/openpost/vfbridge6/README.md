# OpenPost vfbridge6

Velvet Factory production overlay for `getopenpost/openpost` **v4.35.0**.

## Production evidence

- Production install: `/opt/openpost/v4.35.0-vfbridge6`
- Cloud Build ID: `da80d4fe-c7af-4f40-9f14-4023bd45e4b1`
- `openpost-server` SHA-256: `7680c802ddb9de55e51b5fc68ef7dafae659a2798b9ba2fd07cfeab907100293`
- `vf-openpost-token` SHA-256: `a31030d4bb9c8234266e168f9aa6435970a44f9cbc6923a5a60ba5735cf1dc31`
- Production verification: both `openpost` and `openpost-worker` active on vfbridge6; `/api/v1/ready` returned `status=ready` and `database=ok`.

## What vfbridge6 changes

- Propagates safe Instagram MCP `error_class` and safe provider messages into the OpenPost failure model instead of collapsing failures to `unknown` / `<nil>`.
- Maps definite validation/auth/permission/rate-limit failures to stable HTTP/provider classifications.
- Keeps timeout/network/provider-interruption outcomes ambiguous after the durable write fence so OpenPost does not blindly replay a write that Meta may already have accepted.
- Preserves 429/rate-limit as retryable when the delivery outcome is definitely rejected and safe to retry.
- Returns terminal rendition failures to the worker instead of reporting the execution loop as successful while the rendition failed.
- Runs web and worker from the same exact binary.

## Reproducible overlay

`tracked.patch` contains only tracked upstream changes used by the production build.

`overlay/` contains the VF-only files added to the upstream tree:

- `apps/server/internal/platform/velvet_mcp.go`
- `apps/server/internal/platform/velvet_mcp_test.go`
- `apps/server/cmd/vf-openpost-token/main.go`

`cloudbuild.yaml` is the exact v6 build recipe. `deploy.sh` installs the exact artifacts and verifies their SHA-256 values before switching systemd.

## Rollback

`deploy.sh` adds only `zz-vfbridge6.conf` drop-ins. If deployment/readiness fails it removes those drop-ins, reloads systemd, and restarts the previous configuration. On the production host the previous active bridge was vfbridge5.

Do not deploy unpinned `latest` artifacts and do not modify the Instagram write boundary: every mutation still requires the exact signed `velvet.delivery_approval.v1` package/media binding.