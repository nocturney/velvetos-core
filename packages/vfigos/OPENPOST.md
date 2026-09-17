# OpenPost · Publishing Control Plane

מושב: **צמיחה / vfigos**. OpenPost אינו מנוע קריאייטיב, אינו pack/runtime שני ואינו מחליף שום שער איכות או הרשאת מסירה של VelvetOS.

Upstream: `getopenpost/openpost`  
Runtime baseline: **v4.34.2**
Latest reviewed upstream: **v4.34.2** (2026-09-16)
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

## Review v4.31.0 -> v4.34.2

- **Meta/Instagram auth:** לא זוהה breaking change ישיר ל־VF; public HTTPS/media origin ו־Meta provider OAuth עדיין prerequisites.
- **API/MCP:** תוקנו scope combinations של `mcp:read`/`mcp:full`, נעילת OAuth authorization callback נגד צריכת code כפולה, ו־API token clock-skew סמוך לאורך החיים המקסימלי.
- **Media limits:** לא זוהה שינוי במגבלות Instagram; השינויים המתועדים מוסיפים יעדי Fediverse.
- **Scheduler/queue/retry:** לא זוהה שינוי breaking בנתיב VF; v4.32 מוסיפה bounded non-blocking diagnostics queue.
- **Analytics:** השינויים הרלוונטיים הם Discord/Lemmy/PieFed, לא Instagram.
- **Database/schema/storage:** migrations `135_fediverse_instance_provider.sql` ו־`136_billing_discord_notifications.sql` משנות סכימה; נדרש backup + staging migration smoke לפני runtime upgrade.
- **Security/privacy:** החל מ־v4.32 maintainer diagnostics מופעלים כברירת מחדל ב־self-hosted ושולחים failure reports מצומצמים החוצה. מדיניות VF היא fail-closed: `OPENPOST_DIAGNOSTICS_ENABLED=false` עד אישור מפורש אחר.
- **Pinned artifact reviewed:** Windows server v4.34.2 SHA-256 `43a2696d0c7bafdba064b84df414ff0c1c0ccfaf99215a999291b67e447e7442`.

## Current runtime decision

Windows staging is now pinned to **v4.34.2** after a hashed backup and isolated migration smoke (schema 134 -> 136, `integrity_check=ok`, zero foreign-key violations). `OPENPOST_DIAGNOSTICS_ENABLED=false` is enforced. Production remains blocked on public HTTPS/provider OAuth and `NEEDS_OPERATOR_SETUP` delivery-approval live evidence. The Windows binary listens on `::`, so staging is explicitly protected by inbound firewall block `VelvetOS-OpenPost-Staging-LocalOnly` on TCP/18080; loopback `127.0.0.1` OpenAPI remains HTTP 200.

Version state: [`OPENPOST.json`](OPENPOST.json).
