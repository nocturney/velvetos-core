# vfigos — local Instagram action guide

Scope: Instagram transport, queue, schedule and publish/readback execution.

- Canonical external-effect authority is `policy_id: instagram.publish`.
- Read `SEND.md`, `CAPABILITIES.json` and the exact routed publication evidence; do not load the full creative warehouse for a transport-only task.
- Scheduling/queue state is not publication. Claim published only after provider receipt + live readback.
- LOW-risk routine publication may proceed without per-asset owner approval only when the canonical evaluator returns `ALLOW` and required content evidence is exact-bound.
- Boost/ads, auto-DM, rights/privacy ambiguity and other protected effects remain separate policies.
- Transport/runtime readiness is evidence, never authorization.

Verification: Instagram policy/publication sensors and `python3 scripts/check-publication-evidence.py`.

## Automatic read-source discovery (all scheduled-publication questions)

For a schedule, status or "what is planned" question, **do not ask the owner which platform to inspect**. Enumerate the active reader inventory in `schedule_observer/source-registry.json`, use `schedule_observer/README.md` and the connected, authorized sources, and reconcile each source's observation with an explicit freshness timestamp. The canonical Cloudflare D1 remains the VelvetOS **write authority**, but Meta Business Suite is an independent native schedule observation; the Google Calendar is Cloudflare's one-way mirror; Instagram Graph confirms published media, not unposted native schedules. The Instagram app's own Scheduled UI remains an explicitly uncovered surface until an approved reader is verified.

On the authorized Chris computer, invoke the **on-demand-only** `VelvetOS Instagram Sources Read` interactive-user task through Remote Desktop Commander and read its verified `all-sources-latest.json` / `on-demand-read-receipt.json`. Refresh Google Calendar and Instagram Graph through the existing connectors; never ask the owner to pick one. If Desktop Commander or an individual source is unavailable, label that source `UNAVAILABLE` or `STALE`, never `EMPTY`. Report Meta virtual-table counts as a **lower bound**, not certified completeness. Do not add second publishing/scheduling authority or change jobs while performing observation.
