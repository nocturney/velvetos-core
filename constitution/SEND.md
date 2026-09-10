# שליחה מ־HQ · כלים, לא אדם ולא Grok Bot

נעילה 31.8.2026 (Asia/Jerusalem) — הבעלים:  
Treg לא רלוונטי. Drive יוצר מסמכים לפי צורך.  
**ג׳ימייל ואינסטגרם יוצאים מ־HQ דרך כלים** — לא דרך כריסטיאן ולא דרך Grok Bot.  
פיילאובר מלא: כלי נפל → כלי גיבוי באותו תור. אסור להישאר בלי תוצאה.

לא פק חדש. לא מושב שישי.

## מי שולח

| ערוץ | מי | כלי | לא |
|---|---|---|---|
| ג׳ימייל | **סוכן HQ** | `send_message` / `reply` / `forward` על `nocturney@gmail.com` | לא מחכים לגרוק. לא מחכים לאדם ללחוץ Send |
| אינסטגרם `@velvets_cloud` | **סוכן HQ** דרך כלי מחובר | **adelaidasofia/instagram-mcp** `publish_image` / `publish_carousel` / `publish_reel` / `publish_story` אחרי שערי creative+Canva+vault+PREFLIGHT v2 | לא LIVE-PACKET לאדם כברירת מחדל. לא אוטו־DM. לא Metricool כתלות |
| וואטסאפ לקוח | אדם `050-2517000` | Core: MCP חיפוש/טיוטה. VF `send=false` | HQ לא ממציא בוט |
| מדפסות | רצפה | `vfprod` | HQ לא לוחץ Print |
| בוסט / אוטו־DM | — | נעול | נעול תמיד |

Grok Bot הוא **גיבוי אופציונלי**, לא השולח היחיד ולא שער חובה.

## לפני Instagram publish — שני שערים נפרדים

### 1. Transport readiness

אבחון חיבור בלבד:

```bash
python3 scripts/vf_send_preflight.py --gate instagram --transport-only
```

הצלחה כאן אומרת רק שהכלי/transport זמינים. **היא אינה הרשאת publish.**

### 2. Exact-package creative approval

לפני כל `publish_*` חובה להריץ:

```bash
python3 scripts/vf_send_preflight.py --gate instagram \
  --content-id <GID> \
  --format <story|reel|carousel|post> \
  --approval-ref packages/vfgrowth/preflight/<GID>.md \
  --package-sha256 <SHA256-OF-EXACT-FINAL-PACKAGE>
```

רק exit `0` ובפלט `publication_quality.publishAuthorized=true` מאפשרים Publish.  
exit `1/2` = **לא מפרסמים**. מתקנים את התוצר או את ה־transport לפי הסיבה.

PREFLIGHT לפרסום חדש חייב להיות schema v2. בסטורי: `brand_guardian`, `copy_qa`, `readability`, `contrast` = `PASS`; Rubric ≥20/25; `artifact_digest`; `final_package_sha256`. אין waiver ל״רכה אבל קריאה״ / ״לא חוסם״. שינוי מהותי אחרי QA מבטל approval.

## פריפלייט כללי לכלי HQ

```bash
python3 scripts/vf_send_preflight.py
python3 scripts/vf_send_preflight.py --gate gmail
```

בדיקות כלי אינן מחליפות `vfgrowth/PREFLIGHT.md`.

## ג׳ימייל — מותר עכשיו

- בריף 07:00 ל־`nocturney@gmail.com`
- תשובה בשרשור פנייה שכבר נקרא (בלי ₪ מומצא)
- חבילת LIVE / כיתוב / קישור Canva / קישור Drive
- `reply` / `forward` כשזה מקדם את הצינור

אסור: דיוור המוני, חוב בלי ראש צוות, סודות, אוטו־DM / `send_dm`.

## בריף 07:00 — לולאה לפני שליחה

`python3 scripts/vfops_loop.py brief --write` מרכיב את החריצים מפקים חיים. אחר כך `render_mail.py`. המעבר הזה לא מפרסם IG.

## נעילת כריסטיאן — לפני שיבוץ / חי

משטח: **החלטה** · **חסם קשיח** · **פרסום חי שדורש אותו בלבד**.  
אסור: מדדים חלשים · «רמה נמוכה» · נתיחת איכות אחרי פרסום · דוח בושה על כלי שלא נצרך.

לפני שיבוץ או Publish: ארטיפקט `vfgrowth/preflight/<id>.md` לפי [`PREFLIGHT.md`](../packages/vfgrowth/PREFLIGHT.md). נכשל-סגור → **לא משבצים ולא מפרסמים**.

## אינסטגרם — מותר דרך כלי

1. **קופי + creative QA + שער עריכה** — VOICE/Brand Guardian/רובריקה, Canva/vfcovers/vfcanva, ואז בדיקת final render.
2. **PREFLIGHT v2** — קשור ל־hash של החבילה המדויקת. approval ישן/חסר digest אינו תקף לפרסום חדש.
3. `vfcopy` נותן כיתוב + **PUBLIC_CURRENT_CTA**. לא וואטסאפ בכיתוב ציבורי.
4. אם Instagram MCP מחובר — מריצים exact-package gate, ורק אחרי PASS מפרסמים ב־`publish_*`.
5. אחרי publish מאמתים ב־`list_media`/`get_media`; רק אז `liveVerified`.
6. אם אין Publish MCP חי — failover Drive+Gmail באותו תור; לא טוענים שעלה.
7. לא סרק. לא «תעלה ידנית». לא ממציאים שנשלח לפיד אם לא עלה.

## Drive — יוצרים לפי צורך

`create_file`: מסמך / גיליון / מצגת למשרד. לא פותחים תיקיות אישיות/רפואיות/משפטיות. לא ממציאים שורות מחיר.

## Organic Growth Control Plane — לא מפרסם

[`ORGANIC_GROWTH.md`](ORGANIC_GROWTH.md): מפעל טיוטות + Decision Pack 07:00. אישור אדם ≠ פרסום. שליחת IG חיה נשארת פעולה נפרדת אחרי שערי האיכות וה־publish.

## עדיין אסור

אוטו־DM, בוסט בלי ראש צוות, ₪ / Insights מומצאים, גוף חסום מומצא, משלוח ארצי, סוד בגיט, `fcc-server` ב־Cloud Agent, או Publish על בסיס transport readiness בלבד.
