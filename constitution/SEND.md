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
| אינסטגרם `@velvets_cloud` | **סוכן HQ** דרך כלי מחובר | **ig-mcp** `publish_media` אחרי Canva export (`vfigos/CONNECT-IG.md`). כשאין MCP — Gmail + Drive + Canva **באותו תור** | לא LIVE-PACKET לאדם כברירת מחדל. לא «מחכים למכסת Grok». לא אוטו־DM |
| וואטסאפ לקוח | אדם `050-2517000` | Core: MCP חיפוש/טיוטה (`vfmcp/CONNECT-WHATSAPP.md`). VF `send=false` | HQ לא ממציא בוט · לא Infobip/ManyChat |
| מדפסות | רצפה | `vfprod` | HQ לא לוחץ Print |
| בוסט / אוטו־DM | — | נעול | נעול תמיד |

Grok Bot הוא **גיבוי אופציונלי**, לא השולח היחיד ולא שער חובה.

## פריפלייט קל לפני שליחה

לפני `send_message` / Publish / קריאת API תזמורת — הרץ:

```bash
python3 scripts/vf_send_preflight.py
python3 scripts/vf_send_preflight.py --gate gmail        # 0=ready
python3 scripts/vf_send_preflight.py --gate instagram    # 2=failover Canva+Drive+Gmail
```

בודק סטטוס שולחן + נוכחות מפתח (מקומי בלבד, בלי רשת).  
יציאה `2` = **failover באותו תור** — לא סרק, לא המצאה.  
לא מחליף את `vfgrowth/PREFLIGHT.md` (שער איכות תוכן לפני שיבוץ).

## ג׳ימייל — מותר עכשיו

- בריף 07:00 ל־`nocturney@gmail.com`
- תשובה בשרשור פנייה שכבר נקרא (בלי ₪ מומצא)
- חבילת LIVE / כיתוב / קישור Canva / קישור Drive
- `reply` / `forward` כשזה מקדם את הצינור

אסור: דיוור המוני, חוב בלי ראש צוות, סודות, «שלחו DM».

## בריף 07:00 — לולאה לפני שליחה

`python3 scripts/vfops_loop.py brief --write` מרכיב את החריצים מפקים חיים.  
אחר כך `render_mail.py` + `send_message` (`htmlBody` תצוגה 3). המעבר הזה לא מפרסם IG.

## נעילת כריסטיאן — לפני שיבוץ / חי

משטח: **החלטה** · **חסם קשיח** · **פרסום חי שדורש אותו בלבד**.  
אסור: מדדים חלשים · «רמה נמוכה» · נתיחת איכות אחרי פרסום · דוח בושה על כלי שלא נצרך.

לפני שיבוץ או Publish: ארטיפקט `vfgrowth/preflight/<id>.md` לפי [`PREFLIGHT.md`](../packages/vfgrowth/PREFLIGHT.md) — VOICE + Canva/vfcovers + ציון עצמי + 2–3 קומפס.  
נכשל-סגור → **לא משבצים**. מתקנים במשרד. אל תפנה לכריסטיאן על מדדים חלשים.

## אינסטגרם — מותר דרך כלי

1. **פריפלייט + שער עריכה** — ארטיפקט כתוב (`PREFLIGHT.md`) ואז Canva MCP / `vfcovers` / `vfcanva` (`studio/render.py`). **לא** טקסט על JPEG גולמי (`STUDIO.md`, `vfgrowth/EDIT-GATE.md`). Gemini browser רק על המק. בלי שער עבור = נכשל-סגור.
2. `vfcopy` נותן כיתוב + CTA וואטסאפ / איסוף שדרות.
3. אם **ig-mcp** מחובר (`packages/vfigos/CONNECT-IG.md`) — HQ מפרסם ב־`publish_media`, **מאמת תוצאת כלי** (validate→apply→verify ב־`vfigos/SEND.md`), ורק אז מסמן `#נשלח-מ-HQ`.
4. אם אין Publish MCP / `needsAuth` — **failover מיד:** יוצרים מסמך Drive + שולחים ג׳ימייל עם המדיה/הכיתוב/קישור העריכה. מסמנים `#נשלח-מ-HQ` (מסלול כלים) + `#ממתין-ל-כלי-IG` אם הפיד עצמו עוד לא עלה.
5. לא סרק. לא «תעלה ידנית». לא ממציאים שנשלח לפיד אם לא עלה (accepted ≠ confirmed). לא `send_dm`.

## Drive — יוצרים לפי צורך

`create_file`: מסמך / גיליון / מצגת למשרד (בריף, חבילת שליחה, ספר בלי ₪ מומצא).  
לא פותחים תיקיות אישיות/רפואיות/משפטיות. לא ממציאים שורות מחיר.

## Treg

לא רלוונטי למשרד. לא login, לא `call`, לא failover דרכו.  
חיפוש חי: `WebSearch` / `WebFetch` / תזמורת. Insights: מקור מאומת או «אין ספירה». מוזיקה: `MUSIC.md` / HeyOrca.

## Organic Growth Control Plane — לא מפרסם

[`ORGANIC_GROWTH.md`](ORGANIC_GROWTH.md): מפעל טיוטות + Decision Pack 07:00.  
אישור אדם = `approved_for_manual_posting` — **לא** קריאת Publish ולא מעבר ל־`posted_manually`.  
בריף 07:00 עדיין יוצא ב־Gmail דרך כלים. שליחת IG חיה נשארת משרה נפרדת לפי הטבלה למעלה, רק אחרי אישור אדם — לא מה־Control Plane.

## עדיין אסור

אוטו־DM, בוסט בלי ראש צוות, ₪ / Insights מומצאים, גוף חסום מומצא, משלוח ארצי, סוד בגיט, `fcc-server` ב־Cloud Agent.
