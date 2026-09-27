# OpenPost · Publishing Control Plane

מושב: **צמיחה / vfigos**. OpenPost אינו מנוע קריאייטיב, אינו pack/runtime שני ואינו מחליף שום שער איכות או הרשאת מסירה של VelvetOS.

Upstream: `getopenpost/openpost`  
Runtime baseline: **v4.35.0**
Latest reviewed upstream: **v4.35.0** (2026-09-17)
Role: **LEGACY / read-only provenance and recovery inspection** as of 2026-09-24.

> **Cutover 2026-09-24:** Cloudflare Publisher (`packages/vfigos/PUBLISHER.json`) is the primary scheduled publication control-plane. Do not create new Velvet Factory schedules in OpenPost. The production OpenPost runtime stays deployed only so historical records, provider outcomes and recovery evidence remain inspectable.

## החלטת ארכיטקטורה

OpenPost was previously the `vfigos` publication operations/control-plane. It is now retained as a legacy/recovery surface only; scheduled apply belongs to Cloudflare Publisher and live verification remains the canonical Instagram MCP.

```text
Content decision / creative pipeline
  -> Media Vault + exact versionApproval
  -> packages/vfom/PUBLICATION-PREP-EXECUTION.md
  -> Product Truth + Owner-Approved Grid Standard
  -> VISIBLE_TEXT + Brand Guardian + executable creative preflight
  -> PREFLIGHT/publicationEvidence + exact artifact/package hash
  -> scheduled: exact owner_schedule_authorization -> Cloudflare Publisher D1/KV
  -> immediate: signed velvet.delivery_approval.v1 -> direct Instagram MCP
  -> Instagram Graph/MCP live read-back verification
  -> liveVerified + ledger
  -> Insights / learning loop
```

OpenPost אינו מקבל עוד schedules חדשים. הוא נשאר read-only לצורך provenance/recovery ואינו מקור הרשאה או נתיב apply.

## Instagram / Meta

- חשבון יעד: `@velvets_cloud`.
- Direct/canonical Instagram MCP נשאר `adelaidasofia/instagram-mcp` לקריאה, live verification ו־same-turn failover.
- OpenPost מיועד ל־orchestration של publication; הוא לא מקור האמת ל־Instagram capabilities ולא ראיית live.
- OpenPost upload/schedule/publish success לעולם אינו `liveVerified`; רק `list_media` / `get_media` מה־Instagram MCP הקנוני הם ראיית live.
- אין auto-DM, אין boost/Ads, אין שינוי מחיר/Spend ואין המצאת Insights/metrics.

## Authorization boundary after cutover

- **Future scheduled publication:** owner approval is captured when the immutable schedule job is created. The authorization must bind the exact `content_id`, package SHA-256, `scheduled_at`, caption and ordered media hashes. The Worker HMAC-binds the full job and re-verifies media bytes before publish.
- **Immediate direct publication:** the existing short-lived signed `velvet.delivery_approval.v1` boundary remains mandatory.
- A scheduled job is not editable in-place: changing time, caption, package or media requires cancellation and a newly authorized job.
- Ambiguous outcomes after `media_publish` never auto-retry; they enter `reconcile_required`.

## Legacy OpenPost mode

`integrationMode=legacy-read-only`. Health/read operations remain useful for historical evidence and incident inspection. Scheduling, retry delivery and new publication mutations are no longer authorized VF routes.

## Release / upgrade policy

לא משתמשים ב־`latest` ב־production. גרסה או digest ננעצים במפורש ומתקדמים רק לאחר review.

לכל release חדש:

1. לקרוא release notes + changelog + breaking/migration notes.
2. לסווג השפעה על Meta/Instagram auth, API/MCP, media limits, scheduler/queue/retry, analytics, database/schema/storage ו־security/privacy.
3. לעדכן `latestReviewedVersion` רק עם ראיית upstream אמיתית.
4. אם יש migration/schema change — לבצע backup אמיתי לפני upgrade ולבצע staging migration smoke.
5. staging מקבל גרסה מדויקת / immutable digest, לא `latest`.
6. לפני v4.32+ חובה להציב במפורש `OPENPOST_DIAGNOSTICS_ENABLED=false` כל עוד אין אישור מפורש לשיתוף maintainer diagnostics חיצוני.
7. smoke: health/auth + queue/schedule + post/carousel/reel/story contract + retry + analytics read; publish smoke דורש גם provider prerequisites וגם signed delivery approval.
8. Instagram live verification נשאר `list_media` / `get_media`.
9. רק אם אין regression וכל gates הדרושים PASS — ניתן לשקול production pin.

## Review v4.34.2 -> v4.35.0

- **Meta/Instagram auth:** no Instagram/Facebook/OAuth provider code changed; the same Meta app, callback and public-media prerequisites remain.
- **API/MCP:** no VF-relevant contract change identified.
- **Media limits:** no Instagram media-limit change identified.
- **Scheduler/queue/retry:** no VF publication scheduler/queue/retry change identified.
- **Analytics:** PieFed analytics fixes only; no Instagram analytics contract change identified.
- **Database/schema/storage:** no new migrations; isolated smoke and promoted staging remain on schema `136` with `integrity_check=ok` and zero foreign-key violations.
- **Security/privacy:** no VF provider-security boundary change identified. The current runtime explicitly sets `OPENPOST_DIAGNOSTICS_ENABLED=false`; the pre-upgrade backup also captured `false`, but that snapshot is not treated as proof of uninterrupted historical enforcement.
- **Pinned artifact reviewed:** Windows server v4.35.0 SHA-256 `be6520f495def72b1b466a69c9a223954b4403c3c7c40881b52ce0f030334cc8`.
- **Production-host artifact:** Linux server v4.35.0 SHA-256 `157abefc2810dde09e914b78915f79c0160fcf60047856a30a1261c1721d2856`.

## Current runtime decision

מאז cutover של **2026-09-24**, OpenPost **אינו** production publication control-plane של Velvet Factory. ה־GCP host v4.35.0 + `vfbridge6` נשאר זמין לקריאה, provenance, incident inspection וראיות היסטוריות בלבד. אין schedule חדש, אין provider apply חדש ואין auto-failover חדש דרך OpenPost.

ה־production scheduled control-plane הוא Cloudflare Publisher (`PUBLISHER.json`): D1 queue, KV exact-hash media, Cron, bounded pre-publish retry ו־Graph read-back. חבילת `packages/vfigos/failover/` מתועדת כ־legacy של OpenPost ואינה חמושה ל־Publisher jobs.

פרטי build/pin, ה־owner-approved write ההיסטורי וראיות `vfbridge6` נשמרים ב־`OPENPOST.json` וב־`packages/vfigos/openpost/vfbridge6/` לצורך lineage; הם אינם authorization למסלול חדש.

Version state: [`OPENPOST.json`](OPENPOST.json).
