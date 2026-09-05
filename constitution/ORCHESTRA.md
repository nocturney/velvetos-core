# תזמורת הכלים החיצוניים

פלייבוק משרד. לא פק חדש. לא סוכן חדש.

נעול 30.8.2026 ~17:55 (Asia/Jerusalem):  
הצ'אט ב־Grok = **החלטות בלבד**. ראש צוות לא חוקר, לא כותב, לא גולש.  
סוסי העבודה: **Cursor + ChatGPT + Gemini + Perplexity**. משתמשים בהם עכשיו — לא כהצעה.

## שלושה שולחנות, בית אחד

| שולחן | מה שואלים | מה לא מבקשים |
|---|---|---|
| **ChatGPT** | מערכות, סדר, שרשרת, מה לייעל במשרד הקיים | חיבור חי לוואטסאפ/אינסטגרם, מחיר ₪ |
| **Gemini** | הזדמנות מוצר, המרה בלי לעצור מדפסות, בריף | ManyChat, אוטו־DM, Meta Suite |
| **Perplexity** | מקורות חיים, מק״ט קל־להדפסה/קל־למכירה, ציטוטים | גוף מומצא אם Cloudflare חוסם |

## Failover — אסור להישאר בלי תוצאה

נעול 30.8.2026 ערב (Asia/Jerusalem):  
כלי נפל / אין גישה / חומה / `needsAuth` / שגיאת MCP → **מעבירים את המשימה לכלי גיבוי באותו רגע.**  
לא מחכים בסרק. לא סוגרים את המעבר בלי ארטיפקט.  
Failover ≠ המצאה: אסור למלא גוף חסום, ₪, או Insights במקום הכלי שנפל.

### שולחנות מחקר (06:15)

| כלי שנפל | מעבירים מיד ל־ | מה רושמים |
|---|---|---|
| **Perplexity** (Cloudflare / רובוט / סשן פרטי) | WebSearch / WebFetch. **לא** `perplexity-user-mcp` / vscode-perplexity-mcp מ־Cloud | «דולג — חומה» ב־`vfresearch/sources/` · אין גוף מומצא · לא עוגיות |
| **ChatGPT** (אין מפתח / שגיאת API) | `python3 scripts/vf_chatgpt.py orchestra` אם יש `OPENAI_API_KEY` · אחרת Gemini API + Perplexity + WebSearch | Plus ≠ API. **לא** פותחים `chatgpt.com` מ־Cloud. בלי מפתח: «חסר מפתח ChatGPT» |
| **Gemini** (אין מפתח / שגיאת API) | `python3 scripts/vf_gemini.py orchestra` אם יש `GEMINI_API_KEY` · אחרת ChatGPT API + Perplexity + WebSearch | מנוי ≠ API. **לא** פותחים `gemini.google.com` מ־Cloud. בלי מפתח: «חסר מפתח Gemini» |
| שני שולחנות נפלו | השולחן הפתוח נושא את כל העומס עכשיו | מטמיעים רק מגוף אמיתי |
| שלושתם נפלו | פקים שכבר על הדיסק + בלוק `05` = «אין חדש במשרד» | הסלמה לראש צוות על חומות · בלי גוף מומצא |

הזדהות למנוי בדפדפן: **לא מ־Cloud Agent.** רושמים לראש צוות וממשיכים ב־API / WebSearch. לא «מחכים לבעלים» בלי תוצאה. לא שומרים עוגיות.

### כלי HQ חיים (MCP / סטודיו)

| כלי שנפל | מעבירים מיד ל־ | לא עושים |
|---|---|---|
| **Canva** (`needsAuth` / אין כלים) | `packages/vfcanva/studio/render.py` → אם גם זה נכשל: Superdesign | לא ממציאים קישור Canva |
| **Superdesign** | Canva אם מחובר · אחרת `studio/render.py` | לא עוצרים את חבילת התוכן |
| **Mobbin** (אין namespace) | `vfbriefux/MAIL.html` · `hq/brief-email.html` (effective-html) · `render_mail.py --diagram` (diagram-maker) · Superdesign | לא ממציאים מסכי אפליקציה |
| **Treg** | **לא בשימוש.** WebSearch / תזמורת / «אין ספירה» | לא login · לא `call` |
| **WebSearch / WebFetch** (`tools.web`) | תזמורת ChatGPT+Gemini+Perplexity | לא ממציאים גוף חסום |
| **Gemini API** (`vf_gemini.py`) | ChatGPT API + Perplexity + WebSearch | לא ממציאים גוף. בלי מפתח: «חסר מפתח Gemini». **לא** דפדפן `gemini.google.com` |
| **ChatGPT API** (`vf_chatgpt.py`) | Gemini API + Perplexity + WebSearch | לא ממציאים גוף. בלי מפתח: «חסר מפתח ChatGPT». **לא** דפדפן `chatgpt.com` |
| **GenerateImage** (`tools.image`) | Canva `generate-design` → Superdesign → `studio/render.py` | לא ממציאים קישור Canva |
| **Gmail** MCP | Drive `create_file` את הגוף · ממשיכים · **send_message מותר** | לא ממציאים פנייה · לא דיוור המוני |
| **Calendar** MCP | שואלים חלון איסוף / «חסר לוח» וממשיכים בריף מג׳ימייל | לא ממציאים שעות תור |
| **Drive** MCP | קובץ/שם שהמשתמש נתן בצ׳אט | לא פותחים תיקיות אישיות |
| **FCC** (לא על Cloud Agent) | תזמורת ChatGPT+Gemini+Perplexity + thrift ב־`vffcc` | לא מתקינים `fcc-server` כאן |
| **3D AI Studio** (MCP לא מחובר / אין קרדיט) | אתר [3daistudio.com](https://www.3daistudio.com) + Drive + `vfprod/3DAISTUDIO.md` | לא ממציאים מפתח / URL / ₪ · לא מדפיסים מ־HQ |

### Grok Bot (מכסה שבועית / לא זמין)

| מה נפל | מעבירים מיד ל־ | לא עושים |
|---|---|---|
| **Grok Bot** — טיוטות / מחקר / בריף | Cursor HQ + תזמורת + **Gmail send** (בריף = `htmlBody` תצוגה 3) | לא סרק · לא המצאה |
| **Grok Bot** — פרסום | `vfigos/SEND.md` · `#נשלח-מ-HQ` | לא מחכים לגרוק · לא בוסט · לא אוטו־DM |
| **Grok Bot** — **פרסום חי** | `LIVE-PACKET` + כלים (Canva+Gmail+Drive) | אדם רק אם הכלים נפלו |
| דחוף ללקוח (שיחה) | אדם וואטסאפ `050-2517000` (טיוטה: MCP חיפוש או `vf_office.py`) | אין שליחה מ־HQ |

נוהל מלא: `packages/vfharness/playbooks/grok-failover.md` · `docs/GROK-FAILOVER.md`.  
ארטיפקט מעבר: `packages/vfresearch/sources/YYYY-MM-DD-grok-failover.md`.

כל מעבר failover: שורה בארטיפקט היומי (`sources/YYYY-MM-DD-orchestra.md`) — מה נפל · למה · לאיזה כלי עבר · מה הוטמע.

## 06:15 כל בוקר (Asia/Jerusalem)

Cursor, לא Grok:

1. קורא את בריף אתמול + לוח `vfgrowth` + `vfsku` הפתוח.
2. **מק בשדרות** = מארח המנויים, **מק ייעודי** לא PC ווינדוס ([`vfmcp/HOST.md`](../packages/vfmcp/HOST.md)): כרום ו/או Codex `login` + Gemini CLI Login with Google + Perplexity בטאב. **Cloud** לא פותח אתרי מנוי (התראות אבטחה) — קורא `vfresearch/sources/` או `WebSearch`. בלי מפתח API: לא `vf_chatgpt.py` / `vf_gemini.py` חיים. תבנית: `vfresearch/DAILY.md`. [`vfmcp/SUBSCRIPTIONS.md`](../packages/vfmcp/SUBSCRIPTIONS.md).
3. כלי נפל באמצע → **failover מיד** (טבלה למעלה). לא מחכים לסיום כל השלושה אם אחד כבר חסום.
4. מטמיע רק מה ששימושי **מיד** בפק קיים. אין פק לרעיון.
5. כותב שורת «מה נבנה / יועל» ל־`packages/vfops/data/research.md` (בלוק `05-משרד` בבריף 07:00; כולל «failover: X→Y» אם היה).
6. ריק או אין הטמעה = **«אין חדש במשרד»** בדיוק. לא ממלאים רעש.

מעבר ערב (כמו 30.8 אחרי הנעילה): אותה פרוצדורה, התוצר נופל לבריף **למחרת** 07:00.

## מיפוי — לא פק כפול

| סוג ממצא | נופל ל־ | לא נופל ל־ |
|---|---|---|
| שגרה, בריף, שרשרת, תור | `vfops` | פק «מנהל» חדש |
| רתמה / מדריך / סנסור / לולאה | `vfharness` + `AGENTS.md` | מסגרת סוכנים שנייה |
| רשימת orchestrators / ADE / נחיל | `vfe2b` + `vfharness` (דפוס על `crews/run.md`) | פק תזמורת חדש, amux, OpenClaw |
| מק״ט חוזר, קל להדפסה, כרטיס בלי ₪ | `vfsku` + `vlicense` | קטלוג מחירים |
| פנייה → וואטסאפ → איסוף | `vfconvert` | ManyChat / בוט 24/7 |
| כיתוב, FAQ, ארבעה שדות בירור | `vfcopy` | שליחה חיה |
| לוח תוכן מהעבודה (טיימלאפס / לפני־אחרי / הדרכה) | `vfgrowth` + `vfcovers` | בוסט, הזזת לוח משובץ |
| סלייס, תמיכות, סיכון כשל | `vfcost` + `vfprod` | ווידג׳ט תשלום |
| מודל AI (3D AI Studio / Meshy / Tripo) | `vfprod/3DAISTUDIO.md` + `vlicense` | קטלוג / באצ׳ / מחיר מקרדיטים |
| B2B / אתר / מנוי חדש | `vfbiz` נעול עד בלוק `01` | קנייה מ־HQ |
| מספר עמוד אחרי פרסום | `vfinsights` | Insights מהאוויר |
| מקור גולמי של השאלה | `vfresearch/sources/` | שכפול כ־PR נפרד לכל כלי |

## מה נחשב «שימושי מיד»

רוח שיתופי 30.8 (מערכות / חוקה / הזדמנות מוצר) — לא האקי צמיחה:

- קשור להכנסה, לחיסכון זמן, או למניעת טעות על הרצפה.
- נכנס לצ'ק־ליסט, שדה, כרטיס, או שורת בריף **בלי** מחיר ובלי שליחה.
- לא דורש כלי שליחה חדש, לא Meta Suite, לא שכפול חנות, לא סוכן שישי.

## מה מדלגים תמיד

| הצעה | למה |
|---|---|
| אוטו־DM / מענה אוטומטי / «כמה זה עולה?» → טופס | הסטודיו סוגר ב־050-2517000 |
| Meta Business Suite / בוסט / הזזת לוח | נעול. `#משובץ` נשאר |
| מחיר ₪, ווידג׳ט תשלום, «הצעה תוך שניות» | בלי סכום מראש צוות אין באצ׳ |
| צ׳אטבוט 24/7, אתר מ־HQ, שכפול חנות | לא הבית הזה |
| פק חדש לכל רעיון | «לא לפתוח פק כפול» |
| גוף Perplexity אחרי Cloudflare | לא ממציאים |
| Free Claude Code כשולחן רביעי / `fcc-server` ב־HQ | פרוקסי מקומי לא מקטין Cursor Cloud. מפה ב־`vffcc`. התקנה רק על המק אחרי ראש צוות |

## ארטיפקט יומי

אחרי כל מעבר:

```
packages/vfresearch/sources/YYYY-MM-DD-orchestra.md
```

מה נשאל · מה חזר (או «דולג — חומה/הזדהות») · **failover שבוצע** · מה הוטמע · לאיזה פק · מה דולג.

בלוק `05` לבריף — `vfops/data/research.md` (תבנית: `vfops/BRIEF.md`).

## פעם בשבוע — קישורי השראה (לא צ'אט חדש)

בנוסף ל־06:15: חוזרים על הקישורים שנשלחו להשראה והטמעה (שיתופים + ריפוזי מקור). הם מתעדכנים; בלי מעבר שבועי מפספסים שינויים.

1. רישום: `packages/vfresearch/LINKS.json`
2. פלייבוק: `packages/vfresearch/WEEKLY.md`
3. ארטיפקט: `packages/vfresearch/sources/YYYY-MM-DD-weekly-links.md`
4. מטמיעים עדכונים **במקום** על פק קיים. שואלים «מה חדש לחקור ולנצל». בלי פק חדש, בלי גוף מומצא, בלי ₪.

שורת בלוק `05`: «שבועי קישורים — …» או «שבועי קישורים — אין חדש במשרד».

## כל יומיים — דירוג Best Skills (לא צ'אט חדש)

מקור חי: [LinklyAI/best-skills](https://github.com/LinklyAI/best-skills) (Top 100 מתעדכן יומית).  
מעבר שבועי לא מספיק — הדירוגים זזים. **כל ~48 שעות** רצים את הסקירה.

**Standing order (בעלים 2026-09-03):** דופק **קבוע לנצח** עד הודעה מפורשת לעצור / לשנות קצב.  
חידוש טיימר חובה בסוף כל מעבר: `packages/vfresearch/TIMER.md` (`vf-best-skills-bi-daily`).

1. פלייבוק: `packages/vfresearch/BEST-SKILLS.md`
2. מצב: `packages/vfresearch/BEST-SKILLS.json` (`standingForever: true`)
3. מיומנות: `.cursor/skills/vf-best-skills/SKILL.md`
4. ארטיפקט: `packages/vfresearch/sources/YYYY-MM-DD-best-skills.md`
5. מטמיעים **דפוסים** על פקים קיימים. אין `npx skills` על Cloud Agent. אין runtime שני.
6. מחדשים את הטיימר — בלי זה הדופק נשבר אחרי ~7 ימים.

שורת בלוק `05`: «best-skills — …» או «best-skills — אין חדש במשרד».

### פתיחת מגבלות (אושר בעלים 2026-09-03)

מותר לעדכן חוקה / מדריכים כשהדירוג חושף דפוס עמיד שמשפר את המשרד, כל עוד נשארים:

- HQ שולח דרך כלים · אין אוטו־DM · אין בוסט בלי ראש צוות · אין Print מ־HQ
- אין ₪ / Insights / גוף חסום מומצאים
- CTA = וואטסאפ `050-2517000` / איסוף שדרות
- אתר שיווקי ציבורי נעול · קונסולה פנימית מותרת
- גילוי סקילים ציבורי = סריקה + הטמעת דפוס בגיט (לא התקנת vendor על Cloud)
