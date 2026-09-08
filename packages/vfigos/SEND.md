# שליחת אינסטגרם מ־HQ

מושב: **צמיחה**. לא מחכים לגרוק. לא מחכים לכריסטיאן.

פרוטוקול מלא: `constitution/SEND.md`.

## סדר

1. כיתוב סופי ב־`vfcopy` — **PUBLIC_CURRENT_CTA** = הודעת Instagram / איסוף שדרות (`constitution/PUBLIC_CTA.md`). לא וואטסאפ בכיתוב. לא אוטו־DM. לא ₪ מומצא.
2. מדיה: גרסה מאושרת במאגר (`docs/MEDIA-VAULT.md` · `packages/vfmedia/catalog.json`) עם `versionApproval` לגרסה המדויקת; תיקיית מאושר לבד אינה הוכחה. יצירה/עריכה ב־Canva (מחובר) או `studio/render.py` / Superdesign חוזרת למסלול נגזרת→אישור. קישור שיתוף Drive אינו בהכרח קישור הורדה: יש לאמת שהכלי מקבל את קובץ המדיה בפועל.
3. **פריפלייט שליחה** — `python3 scripts/vf_send_preflight.py --gate instagram` (exit `2` = failover מיד). אחר כך **אימות לפני שליחה (validate)** — checklist ב־`vfagents/playbooks/reflection-before-send.md` + וידוא שיש כלי Publish או failover מוכן. לא ממציאים ערוץ שלא מחובר. `needsAuth` ≠ סרק משרד — ממשיכים הכנה.
4. **ig-mcp מחובר** (`CONNECT-IG.md`) → HQ מפרסם ב־`publish_media` ל־`@velvets_cloud` → **אימות אחרי שליחה (verify)** — קריאת תוצאת הכלי / id / permalink. רק אז `#נשלח-מ-HQ` **ו־`liveVerified`** ב־`QUEUE.md` / `PUBLICATION-STATES.md`. אם הכלי החזיר accepted אבל לא confirmed → `#ממתין-ל-כלי-IG` / `uploadAccepted` או `publishRequested` — **לא** live.
5. **אין Publish MCP** → failover באותו תור:
   - `Drive create_file` — מסמך חבילה (כיתוב + קישורי Canva/export)
   - `Gmail send_message` אל `nocturney@gmail.com` עם אותה חבילה
   - שורה `#נשלח-מ-HQ` + `#ממתין-ל-כלי-IG` אם הפיד עצמו עוד לא עלה
6. אסור לכתוב שעלה לפיד אם לא עלה. Calendar / upload / publishRequested ≠ live. אסור בוסט. אסור אוטו־DM.

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
