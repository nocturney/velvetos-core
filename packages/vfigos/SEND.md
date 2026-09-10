# שליחת אינסטגרם מ־HQ

מושב: **צמיחה**. לא מחכים לגרוק. לא מחכים לכריסטיאן.

פרוטוקול מלא: `constitution/SEND.md`.  
MCP קנוני: [`CONNECT-IG.md`](CONNECT-IG.md) (`adelaidasofia/instagram-mcp`).  
Transport קנוני למדיה פרטית: [`PUBLISH-BRIDGE.md`](PUBLISH-BRIDGE.md) + [`PUBLISH-BRIDGE.json`](PUBLISH-BRIDGE.json).

## סדר

1. כיתוב סופי ב־`vfcopy` — **PUBLIC_CURRENT_CTA** = הודעת Instagram / «הזמנות» / איסוף שדרות (`constitution/PUBLIC_CTA.md`). לא «שלחו DM». לא וואטסאפ בכיתוב. מקסימום 5 האשטגים. לא אוטו־DM. לא ₪ מומצא.
2. מדיה: גרסה מאושרת במאגר (`docs/MEDIA-VAULT.md` · `packages/vfmedia/catalog.json`) עם `versionApproval` לגרסה המדויקת; תיקיית מאושר לבד אינה הוכחה. יצירה/עריכה ב־Canva (מחובר) או `studio/render.py` / Superdesign חוזרת למסלול נגזרת→אישור.
3. **Publish Bridge** — כאשר הנגזרת אינה כבר ב־HTTPS ציבורי מתאים, מעבירים **רק את הנגזרת שאושרה לפרסום** דרך `PUBLISH-BRIDGE.md`: normalize → strip metadata → content hash → stage בענף `publish-bridge` → external fetch verify. אסור לשנות שיתוף של המקור ב־Drive. `staged`/`fetch_verified` ≠ published. `main` לעולם אינו יעד ל־publish binaries.
4. **פריפלייט שליחה** — `python3 scripts/vf_send_preflight.py --gate instagram` (exit `2` = failover מיד). אחר כך **אימות לפני שליחה (validate)** — checklist ב־`vfagents/playbooks/reflection-before-send.md` + וידוא שיש כלי Publish חי או failover מוכן. לא ממציאים ערוץ שלא מחובר. `remote_access: pending` בלי סשן MCP חי ≠ סרק משרד — ממשיכים הכנה.
5. **Instagram MCP מחובר** → HQ מפרסם לפי פורמט:
   - תמונה → `publish_image`
   - קרוסלה → `publish_carousel`
   - ריל/וידאו → `publish_reel` / `publish_video`
   - סטורי → `publish_story` (אותו MCP; עדיין שער Canva/vfcovers — בלי JPEG גולמי מה־intake)
6. **אימות אחרי שליחה (verify)** — `list_media` / `get_media` (או מקבילה חיה) שמאשרים שהמדיה קיימת/חיה. רק אז `#נשלח-מ-HQ` **ו־`liveVerified`**. אם publish החזיר success בלי אימות חי → `publish_pending_verification` / `#ממתין-ל-כלי-IG` — **לא** live.
7. **אין Publish MCP חי** (Cloud בלי remote / Codespace כבוי) → failover באותו תור:
   - `Drive create_file` — מסמך חבילה (כיתוב + קישורי Canva/export/bridge כשהם כבר קיימים)
   - `Gmail send_message` אל `nocturney@gmail.com` עם אותה חבילה
   - שורה `#נשלח-מ-HQ` + `#ממתין-ל-כלי-IG` אם הפיד עצמו עוד לא עלה
8. אסור לכתוב שעלה לפיד אם לא עלה. Calendar / upload / bridge staging / publishRequested ≠ live. אסור בוסט. אסור אוטו־DM.

## Publish Bridge — כללי בטיחות

- source of truth למדיה נשאר Drive/Media Vault; ה־bridge הוא transport בלבד ואינו קטלוג שני.
- `approved_for_public_release` הוא שער קשיח. upload או folder placement לא מספיקים.
- correlation בנתיב חייב להיות non-PII; לא שם לקוח.
- metadata ציבורי שומר hash של source reference, לא URL פרטי של Drive/Canva.
- cleanup יומי מסיר נכסים ישנים מראש הענף אחרי חלון retention; הוא **לא** secure erase מהיסטוריית Git.
- לכן בענף מותרת רק נגזרת שממילא מותר לפרסם לציבור. חומר פרטי/רגיש/לא מאושר לא נכנס אליו אף פעם.
- `wsrv.nl` מותר כ־converter/fallback לנכס שכבר ציבורי ומאושר; הוא לא SoT ולא ברירת מחדל.

## תגיות תור

| תג | משמעות |
|---|---|
| `#נשלח-מ-HQ` | כלי HQ ביצע שליחה (ג׳ימייל ו/או Publish) |
| `#ממתין-ל-כלי-IG` | failover Gmail+Drive; או publish בלי verify חי |
| `#מוכן-ל-Grok` | גיבוי אופציונלי בלבד — לא ברירת מחדל |
| `#נשלח-בידי-Grok` | Grok שלח כגיבוי, אחרי אישור שנשלח |

## דפוס validate → transport → apply → verify

| שלב | כאן |
|---|---|
| validate | exact version approval + rights/privacy + PREFLIGHT + reflection checklist |
| transport | Publish Bridge רק לנגזרת מאושרת; HTTPS fetch verified |
| apply | `publish_*` **או** Drive+Gmail אותו תור |
| verify | `list_media` / `get_media` · לא «פורסם» בלי ראיה · אין Insights מומצאים |

לא מתקינים SocialClaw / `npx skills` על Cloud Agent. לא blast ל־X/LinkedIn/TikTok מ־HQ בלי ראש צוות. Meta DevTools MCP ≠ Publish.

## אסור

- סרק / «תעלה ידנית» כברירת מחדל
- להפוך מקור/תיקיית Drive לציבוריים כדי לפתור transport
- לשים publish binaries על `main`
- להכניס ל־`publish-bridge` חומר שלא עבר `approved_for_public_release`
- להמציא Insights אחרי «שליחה»
- לטעון live מ־publish tool בלי verify
- Treg · אוטו־DM · `INSTAGRAM_MCP_DM_ENABLED`
