# שליחת אינסטגרם מ־HQ

## Canonical publication route — 2026-09-26

For Velvet Factory publication tasks, creative preparation follows the current VF Project / vfom authority. Canva/vfcanva are forbidden and have no connector, skill, package, composition, export, approval or fallback role.

### Active transport

1. **Scheduled publication:** `packages/vfigos/cloudflare-publisher/` — Cloudflare Worker + D1 + KV + cron every minute.
2. **Publication target:** official Meta Instagram Graph API.
3. **Read/live verification:** the existing Instagram Graph/MCP verification surface (`list_media` / `get_media` or equivalent canonical read-back).
4. **OpenPost:** **FROZEN**. No new schedule, queue, retry, release watch, health dependency or failover may be routed to OpenPost. Historical OpenPost evidence is provenance only.
5. **Meta Ads MCP:** Ads/Marketing scope only. It is not the organic Instagram publisher and must not be used as one.

Machine-readable authority: `packages/velvetos/TOOL-STATUS.json`.

## Preconditions

- Use the exact approved final package/hash.
- Pass the current creative/publication preflight and all rights/privacy/brand/copy gates.
- A scheduled/accepted job is not proof of publication.
- Media bytes uploaded to the Worker are SHA-256 bound; the job is HMAC-bound.
- Any failure at or after the `media_publish` boundary becomes `reconcile_required`; never blind-retry an ambiguous write.
- Only a Meta Graph media id plus live read-back/permalink may become `published_verified`.
- No auto-DM. No boost/Ads without the separate lead gate. No invented metrics or publication success.

## Scheduling

For a scheduled image/carousel:

- upload only the approved derivative bytes to the Cloudflare publisher;
- verify returned SHA-256 matches the exact source bytes;
- create the job with exact `content_id`, `package_sha256`, caption, ordered media list and authorization evidence;
- read the job back and verify `scheduled_at`, media count/order and `status=scheduled`;
- after due time require `published_verified` and independent Instagram read-back.

The migrated production job `VF-OCTOPUS-20260927-CAROUSEL` is recorded under `cloudflare-publisher/migrations/2026-09-24-openpost/`. The old OpenPost record was cleared from active scheduling during migration.

## Immediate publication

When an explicitly authorized immediate publish uses the existing Instagram write boundary directly, it must still use the same exact approved package and live verification discipline. Direct mutation is not an approval bypass and is not the scheduler of record.

## Truth states

`prepared != scheduled != publishing != published_verified`

`retry` is allowed only for failures proven to be pre-publish.

`reconcile_required` means the system cannot safely infer whether the write happened; no second write until reconciled.

## Forbidden

- Canva / vfcanva
- OpenPost as active scheduler, queue, retry engine, release watch, fallback or source of schedule truth
- treating Meta Ads MCP as organic Instagram publishing
- blind retry after `media_publish`
- claiming live from an accepted job without Graph read-back
- auto-DM
- Treg
