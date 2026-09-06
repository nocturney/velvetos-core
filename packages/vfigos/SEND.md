# שליחת אינסטגרם מ־HQ

מושב: **צמיחה**. לא מחכים לגרוק. לא מחכים לכריסטיאן.

פרוטוקול מלא: `constitution/SEND.md`.

## סדר

1. כיתוב סופי ב־`vfcopy` — CTA וואטסאפ `050-2517000` / איסוף שדרות. לא «שלחו DM». לא ₪ מומצא.
2. מדיה: Canva (מחובר) או `studio/render.py` / Superdesign.
3. **אימות לפני שליחה (validate)** — checklist ב־`vfagents/playbooks/reflection-before-send.md` + וידוא שיש כלי Publish או failover מוכן. לא ממציאים ערוץ שלא מחובר.
4. **כלי Publish מחובר** → HQ מפרסם ל־`@velvets_cloud` → **אימות אחרי שליחה (verify)** — קריאת תוצאת הכלי / id / סטטוס. רק אז `#נשלח-מ-HQ` ב־`QUEUE.md`. אם הכלי החזיר accepted אבל לא confirmed → `#ממתין-ל-כלי-IG`, לא «פורסם».
5. **אין Publish MCP** → failover באותו תור:
   - `Drive create_file` — מסמך חבילה (כיתוב + קישורי Canva/export)
   - `Gmail send_message` אל `nocturney@gmail.com` עם אותה חבילה
   - שורה `#נשלח-מ-HQ` + `#ממתין-ל-כלי-IG` אם הפיד עצמו עוד לא עלה
6. אסור לכתוב שעלה לפיד אם לא עלה. אסור בוסט. אסור אוטו־DM.

## תגיות תור

| תג | משמעות |
|---|---|
| `#נשלח-מ-HQ` | כלי HQ ביצע שליחה (ג׳ימייל ו/או Publish) |
| `#ממתין-ל-כלי-IG` | החבילה יצאה דרך Gmail+Drive; הפיד עצמו מחכה ל־Publish MCP · או Publish החזיר accepted בלי confirmed |
| `#מוכן-ל-Grok` | גיבוי אופציונלי בלבד — לא ברירת מחדל |
| `#נשלח-בידי-Grok` | Grok שלח כגיבוי, אחרי אישור שנשלח |

## דפוס validate → apply → verify

מקור דפוס (הטמעה בלבד): social-media-publisher / SocialClaw-style skills — `packages/vfresearch/sources/2026-09-05-social-media-publisher.md`.

| שלב | כאן |
|---|---|
| validate | reflection checklist + כלי מחובר או failover מוכן |
| apply | Publish MCP **או** Drive+Gmail אותו תור |
| verify | תוצאת כלי / message id · לא «פורסם» בלי ראיה · אין Insights מומצאים |

לא מתקינים SocialClaw / `npx skills` על Cloud Agent. לא blast ל־X/LinkedIn/TikTok מ־HQ בלי ראש צוות. Meta DevTools MCP ≠ Publish.

## אסור

- סרק / «תעלה ידנית» כברירת מחדל
- להמציא Insights אחרי «שליחה»
- Treg
- לטעון פיד חי מ־`accepted` בלי אימות
