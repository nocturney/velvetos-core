# OpenPost · Publishing Control Plane

מושב: **צמיחה / vfigos**. OpenPost אינו מנוע קריאייטיב, אינו pack/runtime שני ואינו מחליף שום שער איכות או הרשאת מסירה של VelvetOS.

Upstream: `getopenpost/openpost`  
**Status (2026-09-26): PAUSED (publishing frozen).** Staging: **v6.2.0** (evidence: PR #342, commit `d6b55fcd`; staging only, pin unchanged). Production runtime and LIVE status: **unknown / not verified**. Machine-readable: `OPENPOST.json` → `status`.
Last pinned baseline: v4.35.0 (pin record only; production not re-verified since 2026-09-20)
Role: **FROZEN historical publication control-plane only**. New scheduling, queueing, retry, monitoring and failover route to Cloudflare Publisher / current canonical tools, not OpenPost.

## החלטת ארכיטקטורה

מאז cutover של 2026-09-24, **Cloudflare Publisher הוא מקור האמת היחיד לתזמון Instagram עתידי**; `packages/velvetos/TOOL-STATUS.json` ו־`PUBLISHER.json` הם הסמכות הנוכחית. OpenPost נשאר לקריאת provenance/incident evidence בלבד ואסור להזרים אליו עבודה חדשה.

```text
Content decision / creative pipeline
  -> Media Vault + exact versionApproval
  -> packages/vfom/PUBLICATION-PREP-EXECUTION.md
  -> Product Truth + Owner-Approved Grid Standard
  -> VISIBLE_TEXT + Brand Guardian + executable creative preflight
  -> PREFLIGHT/publicationEvidence + exact artifact/package hash
  -> owner schedule authorization + Cloudflare D1/KV for future schedule
     OR signed velvet.delivery_approval.v1 for explicitly authorized immediate publish
  -> Meta Instagram Graph API
  -> list_media/get_media live verification
  -> published_verified + ledger
  -> Insights / learning loop
```

OpenPost evidence may be inspected historically, but it is not an approval, transport, scheduler, retry or failover authority.

## Instagram / Meta

- חשבון יעד: `@velvets_cloud`.
- Direct/canonical Instagram MCP נשאר `adelaidasofia/instagram-mcp` לקריאה, live verification ו־same-turn failover.
- OpenPost מיועד ל־orchestration של publication; הוא לא מקור האמת ל־Instagram capabilities ולא ראיית live.
- OpenPost upload/schedule/publish success לעולם אינו `liveVerified`; רק `list_media` / `get_media` מה־Instagram MCP הקנוני הם ראיית live.
- אין auto-DM, אין boost/Ads, אין שינוי מחיר/Spend ואין המצאת Insights/metrics.

## Authenticated write boundary

כל Instagram write mutation — גם דרך OpenPost וגם דרך direct Instagram MCP — חייבת לעבור את אותו mutation boundary עם receipt חתום מסוג `velvet.delivery_approval.v1` מה־dedicated issuer.

- `packages/vfigos/approval/OPERATOR-SETUP.md` הוא מסמך ההקמה/סטטוס הקנוני.
- כל עוד live evidence נשאר `NEEDS_OPERATOR_SETUP`, אין production promotion ואין write authorization.
- Publication evidence, standing authorization או transport success אינם תחליף ל־delivery approval חתום.
- Direct Instagram MCP הוא failover תעבורתי בלבד; הוא **לא** approval bypass.

## מצבי הפעלה

1. `shadow` — OpenPost מקבל/מאמת payloads ותזמון בלי להחליף את הנתיב הקנוני.
2. `staging` — בדיקות מבוקרות: health/auth, queue/schedule, post/carousel/reel/story contract, forced failure/retry, analytics ingest ומיגרציות על staging בלבד.
3. `primary-control-plane` — רק אחרי שכל הבדיקות, provider OAuth/public HTTPS, signed delivery approval וה־Instagram live verification עוברים.
4. `degraded` — כשל OpenPost מחזיר מיד ל־direct Instagram MCP; אותה הרשאת delivery חתומה עדיין חובה לכל write.
5. `paused` — **המצב הנוכחי.** הבעלים הקפיא את הפרסום דרך OpenPost. זה לא נתיב שליחה, לא primary ולא failover; לוח הפרסום לא נקרא, ובריפים מציגים "מושהה" ולא כשל.

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

## Historical runtime record (2026-09-20; not re-verified)

> Superseded 2026-09-26: OpenPost is **paused (publishing frozen)**, and the production runtime and LIVE status are **unknown / not verified**. What follows is a historical record of the 2026-09-20 state. It is not a current claim.

At that time OpenPost was the production publication control-plane on the dedicated GCP host at `https://openpost.34.9.7.22.sslip.io`. The host remains pinned to upstream **v4.35.0** plus the reproducible Velvet overlay `vfbridge6`; both `openpost` and `openpost-worker` run `/opt/openpost/v4.35.0-vfbridge6/openpost-server`. The deployed server SHA-256 is `7680c802ddb9de55e51b5fc68ef7dafae659a2798b9ba2fd07cfeab907100293`, the token-helper SHA-256 is `a31030d4bb9c8234266e168f9aa6435970a44f9cbc6923a5a60ba5735cf1dc31`, and `/api/v1/ready` returns `status=ready` with `database=ok`. The exact build/deploy provenance is preserved under `packages/vfigos/openpost/vfbridge6/`.

The Meta provider OAuth for `@velvets_cloud` is valid and a real owner-approved Instagram write has now been completed and canonically verified with the Instagram MCP (`media_id=17899807347597720`). The live mutation service is Cloud Run revision `velvet-instagram-mcp-00018-8mk`, image digest `sha256:5336f9b4ae3db34bb954e31522f07d4e6f85462a1e416964be516704c08569c2`, which waits for feed-image container `FINISHED` before `media_publish` and returns sanitized `error_class`, `stage`, `write_outcome` and `retry_safety` metadata for safe recovery. Delivery approval is therefore **LIVE_VERIFIED** rather than `LIVE_BLOCKED`.

`vfbridge6` preserves safe Meta/Instagram diagnostics: definite auth/permission/validation/rate-limit failures retain their class/code; timeout/network/provider interruption after the durable write fence remains ambiguous and is never blindly replayed. A GrokBot recovery path is available under `packages/vfigos/failover/`, but it is fenced by exact manifest binding, fresh preflight, live duplicate check, signed delivery approval and a read-only OpenPost state check. Grok cannot call Graph directly or publish when the primary outcome is ambiguous/processing/reconcile-only.

Every production `publish_image` schedule must prepare a `velvet.instagram_failover.v1` manifest at staging time so a definitively failed delivery can be recovered inside the delivery window without inventing bindings during the incident. Owner-approved scheduled image posts arm automatic failover by default when `scheduled_at_utc` is present; `--no-auto-failover` is the explicit opt-out. The boot-supervised watcher performs a read-only OpenPost coverage audit every 60 seconds and records `UNPROTECTED_SCHEDULE` when an active Instagram image schedule has no armed exact manifest.

Version state: [`OPENPOST.json`](OPENPOST.json).
