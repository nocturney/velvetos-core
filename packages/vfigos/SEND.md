# שליחת אינסטגרם מ־HQ

`policy_id: instagram.publish` הוא שער ההרשאה המכונתי לפרסום אורגני. ה־Cloudflare publisher מריץ את אותו evaluator לפני קבלת job חדש ושוב אחרי claim, לפני כל קריאת publish ל־Meta Graph. Decision receipt נכתב לפני הפעולה; `DENY` ו־`REQUIRE_OWNER_APPROVAL` אינם מגיעים ל־publish mutation.

## Canonical publication route — 2026-09-26


### Active transport

1. **Scheduled publication:** `packages/vfigos/cloudflare-publisher/` — Cloudflare Worker + D1 + KV + cron every minute.
2. **Publication target:** official Meta Instagram Graph API.
3. **Read/live verification:** the existing Instagram Graph/MCP verification surface (`list_media` / `get_media` or equivalent canonical read-back).
4. **OpenPost:** **FROZEN**. No new schedule, queue, retry, release watch, health dependency or failover may be routed to OpenPost. Historical OpenPost evidence is provenance only.
5. **Meta Ads MCP:** Ads/Marketing scope only. It is not the organic Instagram publisher and must not be used as one.

Machine-readable authority: `packages/velvetos/TOOL-STATUS.json`.

## Creative and media safety bindings

- Canonical media authority: `docs/MEDIA-VAULT.md` + `packages/vfmedia/catalog.json`.
- Publication preparation must follow `packages/vfom/PUBLICATION-PREP-EXECUTION.md`: selection/caption/planning alone is incomplete; if a required visual cannot be executed, fail closed as `visual_execution_unavailable`.
- Brand handling must follow `packages/vfom/BRAND-ASSET-LOCK.md`; generated or invented brand marks are prohibited.
- Transformation must follow `packages/vfom/CREATIVE-TRANSFORMATION-LOCK.md`: `raw_passthrough: false` and at least one fully treated hero before publication review.
- Private-source derivatives route through `packages/vfigos/PUBLISH-BRIDGE.md` / `publish-bridge`; archived transport evidence lives under `publish-bridge/archive`, with `archiveRetention=unlimited` and `deleteArchived=false`.
- A publish request is not live proof. Require publish receipt and then verify through `list_media` / `get_media` or equivalent Meta Graph read-back before any live claim. Only that verified state may be called `liveVerified`.

## Preconditions

- Run `scripts/vf_send_preflight.py` against the exact current package and respect its fail-closed result.
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

For explicitly authorized immediate operations, canonical direct write tools may include `publish_image` / carousel/reel/story equivalents. They are never scheduler evidence and still require live read-back.

When an explicitly authorized immediate publish uses the existing Instagram write boundary directly, it must still use the same exact approved package and live verification discipline. Direct mutation is not an approval bypass and is not the scheduler of record.

## Truth states

`prepared != scheduled != publishing != published_verified`

`retry` is allowed only for failures proven to be pre-publish.

`reconcile_required` means the system cannot safely infer whether the write happened; no second write until reconciled.

## Forbidden

- OpenPost as active scheduler, queue, retry engine, release watch, fallback or source of schedule truth
- treating Meta Ads MCP as organic Instagram publishing
- blind retry after `media_publish`
- claiming live from an accepted job without Graph read-back
- auto-DM
- Treg

## VF_VISUAL_STANDARD_GATE

Before public creative execution, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`. Bind SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897` and require `visualStandard.gate=PASS`. Missing/mismatched authority is `visual_standard_unavailable`; generic visual fallback is forbidden.
