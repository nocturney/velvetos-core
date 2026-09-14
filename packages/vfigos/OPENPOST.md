# OpenPost · Publishing Control Plane

מושב: **צמיחה / vfigos**. OpenPost אינו מנוע קריאייטיב ואינו מחליף את שערי האיכות של VelvetOS.

Upstream: `getopenpost/openpost`  
Release baseline: **v4.31.0** (2026-09-13)  
Role: **scheduler + queue + retry/delivery status + multi-channel publication control + analytics collector**.

## החלטת ארכיטקטורה

OpenPost נכנס **בתוך `vfigos` הקיים** ולא כ-pack/runtime שני.

```text
Content decision / creative pipeline
  -> Media Vault + exact versionApproval
  -> Photo Retouch -> Brand/Content Styling -> Text/Layout QA -> Final Visual QA
  -> PREFLIGHT v2 + exact artifact/package hash
  -> OpenPost queue/schedule/apply
  -> direct Instagram MCP live verification (`list_media` / `get_media`)
  -> liveVerified + ledger
  -> Insights / learning loop
```

OpenPost רשאי לקבל רק artifact שכבר קיבל `publication_quality.publishAuthorized=true`. הוא **לא** רשאי ליצור bypass ל-VISIBLE_TEXT, Brand Guardian, PREFLIGHT, rights/privacy, versionApproval או exact-hash binding.

## Instagram / Meta

Velvet Factory כבר משתמשת בחיבור Facebook/Meta לחשבון Instagram Business; לכן דרישת OpenPost ל-Instagram API with Facebook Login אינה blocker עבורנו.

- חשבון יעד: `@velvets_cloud`
- Direct/canonical Instagram MCP נשאר `adelaidasofia/instagram-mcp` לצורכי קריאה, live verification ו-failover ישיר.
- OpenPost מיועד לשכבת orchestration של publication, לא להחלפת מקור האמת של Instagram capabilities.
- אין auto-DM, אין boost/Ads, אין המצאת Insights/₪, ואין claim של `liveVerified` מתשובת OpenPost בלבד.

## מצבי הפעלה

1. `shadow` — OpenPost מקבל/מאמת payloads ותזמון ללא החלפת הנתיב הקנוני.
2. `staging` — publish tests מבוקרים: post, carousel, reel, story, schedule, forced failure/retry, analytics ingest.
3. `primary-control-plane` — לאחר שכל הבדיקות עוברות; direct Instagram MCP נשאר verify/failover.
4. `degraded` — כשל OpenPost מחזיר מיד ל-direct Instagram MCP לפי `SEND.md`; אין idle.

## Release / upgrade policy

לא משתמשים ב-`latest` ב-production. הגרסה ננעצת (`pinnedVersion`) ומתקדמת רק לאחר review.

לכל release חדש:

1. לקרוא release notes + breaking changes + migration notes.
2. לסווג השפעה על: Instagram/Meta auth, API/MCP, media limits, scheduler/queue/retry, analytics, database/schema, storage, security.
3. לבצע backup לפני upgrade שמכיל migration/schema change.
4. לעדכן staging לגרסה המדויקת, לא ל-`latest`.
5. smoke: health/auth + queue/schedule + post/carousel/reel/story contract + retry + verify + analytics read.
6. להריץ `python3 scripts/check-all.py` לאחר שינוי catalog/pack/rule ב-VelvetOS.
7. רק אם אין breaking regression והבדיקות PASS — לקדם production pin.
8. אם release אינו רלוונטי לאינטגרציה שלנו, לעדכן `lastReviewedVersion` בלבד ולא לבצע rollout מיותר.

## Release priority

- `security` / auth / data-loss / Instagram publishing fix: **urgent review**.
- Meta/Instagram, scheduler, retry, queue, analytics, MCP/API: **high relevance**.
- editors / AI writing / unrelated UI: **low relevance**, אלא אם משפיע על runtime stability.

## Truth / status

OpenPost upload/schedule/publish response אינו הוכחת live. עבור Instagram, `list_media`/`get_media` מה-MCP הקנוני הם עדיין ראיית ה-live שלנו. סטטוסים קנוניים: `publishRequested` -> `publish_pending_verification` -> `liveVerified`.

Version state: [`data/openpost-release-watch.json`](data/openpost-release-watch.json).
