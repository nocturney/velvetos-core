# Instagram publication incident handling

Current authority: `packages/vfigos/PUBLISHER.json`.

The Cloudflare Publisher owns scheduling, queueing, retries and the Meta Graph write. Grok Bot is **not** a second scheduler or duplicate-write failover.

If a job is overdue or fails:
- `scheduled/retry` before the publish boundary may be handled by the Publisher's bounded retry policy.
- `reconcile_required` means the outcome after/at `media_publish` is ambiguous: do **not** issue another write until live Graph state is reconciled.
- `dead_letter` requires operator attention and a new explicitly authorized recovery decision.
- always verify a live media id/permalink before claiming publication.

OpenPost is frozen. Canva/vfcanva are forbidden. Historical OpenPost/Grok failover documentation is archived at `docs/archive/GROK-OPENPOST-FAILOVER.md`.
