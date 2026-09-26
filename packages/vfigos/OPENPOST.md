# OpenPost — FROZEN / NON-ROUTING

Do not schedule, publish, retry, fail over, monitor releases or create new work through OpenPost.

Reason: scheduled Instagram publications were missed and no timely failure alert was produced.

Current state: `integrationMode=frozen`, `activeSchedules=0`. The 27.9 carousel was migrated to Cloudflare; the old OpenPost row is draft with no `scheduled_at`.

Replacement: `packages/vfigos/PUBLISHER.json` and `packages/vfigos/cloudflare-publisher/`.

Historical implementation: `packages/vfigos/archive/openpost/`; historical failover code: `packages/vfigos/archive/openpost-failover/`. Audit only.
