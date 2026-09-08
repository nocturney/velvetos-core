# שליחת אינסטגרם מ־HQ

מושב: **צמיחה**. לא מחכים לגרוק. לא מחכים לכריסטיאן.

פרוטוקול מלא: `constitution/SEND.md`.  
MCP קנוני: [`CONNECT-IG.md`](CONNECT-IG.md) (`adelaidasofia/instagram-mcp`).

## סדר

1. כיתוב סופי ב־`vfcopy` — **PUBLIC_CURRENT_CTA** = הודעת Instagram / «הזמנות» / איסוף שדרות (`constitution/PUBLIC_CTA.md`). לא «שלחו DM». לא וואטסאפ בכיתוב. מקסימום 5 האשטגים. לא אוטו־DM. לא ₪ מומצא.
2. מדיה: גרסה מאושרת במאגר (`docs/MEDIA-VAULT.md` · `packages/vfmedia/catalog.json`) עם `versionApproval` לגרסה המדויקת; תיקיית מאושר לבד אינה הוכחה. יצירה/עריכה ב־Canva (מחובר) או `studio/render.py` / Superdesign חוזרת למסלול נגזרת→אישור. **רק נגזרת מאושרת** מקבלת URL HTTPS ציבורי זמני לפרסום — לא כל הכספת, לא מקור גולמי, לא שינוי שיתוף גלובלי ב־Drive.
3. **פריפלייט שליחה** — `python3 scripts/vf_send_preflight.py --gate instagram` (exit `2` = failover מיד). בדוק `cloud_autonomy_ready` (דורש `remote_access=ready` + `live/remote-health.json` ok) — Codespace stdio לבד **לא** אוטונומיית Cloud. אחר כך **אימות לפני שליחה (validate)** — checklist ב־`vfagents/playbooks/reflection-before-send.md` + וידוא שיש כלי Publish חי או failover מוכן. לא ממציאים ערוץ שלא מחובר. `remote_access: pending` בלי סשן MCP חי ≠ סרק משרד — ממשיכים הכנה. Remote: [`REMOTE.md`](REMOTE.md).
4. **Instagram MCP מחובר** → HQ מפרסם לפי פורמט:
   - תמונה → `publish_image`
   - קרוסלה → `publish_carousel`
   - ריל/וידאו → `publish_reel` / `publish_video`
   - סטורי → `publish_story` (אותו MCP; עדיין שער Canva/vfcovers — בלי JPEG גולמי)
5. **אימות אחרי שליחה (verify)** — `list_media` / `get_media` (או מקבילה חיה) שמאשרים שהמדיה קיימת/חיה. רק אז `#נשלח-מ-HQ` **ו־`liveVerified`**. אם publish החזיר success בלי אימות חי → `publish_pending_verification` / `#ממתין-ל-כלי-IG` — **לא** live.
6. **אין Publish MCP חי** (Cloud בלי remote / Codespace כבוי) → failover באותו תור:
   - `Drive create_file` — מסמך חבילה (כיתוב + קישורי Canva/export)
   - `Gmail send_message` אל `nocturney@gmail.com` עם אותה חבילה
   - שורה `#נשלח-מ-HQ` + `#ממתין-ל-כלי-IG` אם הפיד עצמו עוד לא עלה
7. אסור לכתוב שעלה לפיד אם לא עלה. Calendar / upload / publishRequested ≠ live. אסור בוסט. אסור אוטו־DM.

## תגיות תור

| תג | משמעות |
|---|---|
| `#נשלח-מ-HQ` | כלי HQ ביצע שליחה (ג׳ימייל ו/או Publish) |
| `#ממתין-ל-כלי-IG` | failover Gmail+Drive; או publish בלי verify חי |
| `#מוכן-ל-Grok` | גיבוי אופציונלי בלבד — לא ברירת מחדל |
| `#נשלח-בידי-Grok` | Grok שלח כגיבוי, אחרי אישור שנשלח |

## דפוס validate → apply → verify

| שלב | כאן |
|---|---|
| validate | reflection checklist + כלי מחובר או failover מוכן |
| apply | `publish_*` **או** Drive+Gmail אותו תור |
| verify | `list_media` / `get_media` · לא «פורסם» בלי ראיה · אין Insights מומצאים |

לא מתקינים SocialClaw / `npx skills` על Cloud Agent. לא blast ל־X/LinkedIn/TikTok מ־HQ בלי ראש צוות. Meta DevTools MCP ≠ Publish.

## אסור

- סרק / «תעלה ידנית» כברירת מחדל
- להמציא Insights אחרי «שליחה»
- לטעון live מ־publish tool בלי verify
- Treg · אוטו־DM · `INSTAGRAM_MCP_DM_ENABLED`
