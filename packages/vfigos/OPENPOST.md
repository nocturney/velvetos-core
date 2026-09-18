# OpenPost · Publishing Control Plane

מושב: **צמיחה / vfigos**. OpenPost אינו מנוע קריאייטיב, אינו pack/runtime שני ואינו מחליף שום שער איכות או הרשאת מסירה של VelvetOS.

Upstream: `getopenpost/openpost`  
Runtime baseline: **v4.35.0**
Latest reviewed upstream: **v4.35.0** (2026-09-17)
Role: **scheduler + queue + retry/delivery status + multi-channel publication control + analytics collector**.

## החלטת ארכיטקטורה

OpenPost נכנס **בתוך `vfigos` הקיים** כשכבת publication operations/control-plane בלבד.

```text
Content decision / creative pipeline
  -> Media Vault + exact versionApproval
  -> packages/vfom/PUBLICATION-PREP-EXECUTION.md
  -> Product Truth + Owner-Approved Grid Standard
  -> VISIBLE_TEXT + Brand Guardian + executable creative preflight
  -> PREFLIGHT/publicationEvidence + exact artifact/package hash
  -> signed velvet.delivery_approval.v1 for the exact write mutation
  -> OpenPost queue/schedule/apply OR direct Instagram MCP failover
  -> Instagram MCP list_media/get_media live verification
  -> liveVerified + ledger
  -> Insights / learning loop
```

OpenPost רשאי לקבל רק artifact שעבר את מסלול הפרסום הקנוני וקיבל את הראיות הנדרשות. הוא **לא** יוצר bypass ל־VISIBLE_TEXT, `packages/vfom/PUBLICATION-PREP-EXECUTION.md`, Product Truth, Media Vault/versionApproval, Owner-Approved Grid Standard, Brand Guardian, PREFLIGHT/publicationEvidence, rights/privacy, exact-hash binding או signed `velvet.delivery_approval.v1`.

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

Windows staging remains pinned to **v4.35.0** with its verified backup/migration evidence. A dedicated GCP production host is now deployed at `https://openpost.34.9.7.22.sslip.io` using the exact Linux v4.35.0 artifact `sha256:157abefc2810dde09e914b78915f79c0160fcf60047856a30a1261c1721d2856` behind Caddy. Public `/api/v1/ready` returns HTTP 200 with `status=ready` and `database=ok`; TLS verification passes, HTTP redirects to HTTPS, direct external TCP/18080 is blocked, public SSH/RDP are denied by higher-priority target-specific firewall rules, IAP-only SSH is verified, diagnostics are disabled, and a full VM reset returned the same ready response. This proves the stable public app/media origin, not production promotion. The first OpenPost user is now verified as instance admin, one workspace with one member exists, and new registrations are disabled (`OPENPOST_DISABLE_REGISTRATIONS=true`, `/api/v1/auth/config` reports `registration_enabled=false`). The Meta App Secret has not been entered, provider OAuth has not run, and no real Instagram write was performed. Delivery approval remains **BOUNDARY_SMOKE_VERIFIED / LIVE_BLOCKED**.

Version state: [`OPENPOST.json`](OPENPOST.json).
