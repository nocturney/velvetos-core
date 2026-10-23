# OpenPost · RETIRED

**Status (2026-10-23): RETIRED from active VelvetOS source.** OpenPost is not runnable here. Machine-readable record: `OPENPOST.json` (`status.state = "retired"`, `runnable = false`).

Cloudflare Instagram Publisher is the only scheduling, queue and retry path for Instagram publication. Canonical read-back and live verification go through the Instagram Graph / canonical Instagram MCP (`adelaidasofia/instagram-mcp`). Authority: `packages/vfigos/SEND.md`, `packages/vfigos/cloudflare-publisher/` and `instance:surface:toolStatus`.

## What was removed

- OpenPost vfbridge6 deploy, Cloud Build, Go overlay and tracked patch (`packages/vfigos/openpost/`).
- OpenPost morning snapshot and thumbnail hooks.
- Grok Instagram failover runners, watcher, state gate, manifest preparer and trusted dispatch (`packages/vfigos/failover/`).

The full list is in `OPENPOST.json#removedArtifacts`. Historical evidence is kept in Git history and the old handoff records under `packages/vfharness/state/` and `packages/vfigos/cloudflare-publisher/migrations/2026-09-24-openpost/`. It is provenance only and must not be run or treated as current state.

## Rules

- No new schedule, queue, retry, release watch, health dependency, monitoring or failover may route to OpenPost.
- OpenPost upload, schedule or publish responses are not live evidence. Live status comes only from Instagram Graph / MCP `list_media` or `get_media` read-back.
- Every Instagram write still requires the signed `velvet.delivery_approval.v1` boundary. The direct Instagram MCP is a transport, not an approval bypass.
- Production OpenPost version and live status are not verified and must not be claimed.
