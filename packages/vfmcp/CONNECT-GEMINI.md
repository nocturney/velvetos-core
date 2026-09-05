# איך מחברים Gemini API (לא מנוי הדפדפן)

לא ב־`.cursor/mcp.json` של הריפו — צריך `GEMINI_API_KEY`. שמים **בסביבת המשתמש / סוד Cloud**, לא בגיט.

**מנוי Gemini Plus / Advanced / Google AI Pro ב־`gemini.google.com` ≠ Gemini API.**  
המנוי נותן צ'אט בדפדפן, Gems, Canvas, Deep Research, Connected Apps (Gmail/Drive/YouTube).  
ה־API (Google AI Studio) נותן `generateContent` עם מפתח, חיוב נפרד, בלי Gems ובלי אפליקציות Workspace של המנוי.

גשר HQ (בלי vendor MCP): `python3 scripts/vf_gemini.py`.  
בלי מפתח: **חסר מפתח Gemini**. לא ממציאים גוף. לא Veo מ־HQ.

## למה לא [aliargun/mcp-server-gemini](https://github.com/aliargun/mcp-server-gemini)

נבדק 5.9.2026:

| | aliargun | כאן |
|---|---|---|
| מוצר | Gemini **API** (AI Studio key) | אותו מוצר — לא המנוי |
| עדכון אחרון | push `2025-07-14` · «latest as of July 2025» | רשימת מודלים **חיה** מה־API |
| מודלים | קשיחים 2.5 / 2.0 / 1.5 | 3.x כשמופיעים ברשימה; בלי שמות מומצאים |
| פרוטוקול MCP | `2024-11-05` | לא מתקינים את השרת |
| חסר אצלם | image-gen, Files, code exec, Interactions API, Veo | image-gen/Veo נעולים ב־HQ; Files/code לא נדרשים לתזמורת |
| סוד | `GEMINI_API_KEY` ב־npx | אותו מפתח ב־env; **לא** ב־mcp.json של הפרויקט |

אל תתקינו `npx github:aliargun/mcp-server-gemini` על Cloud Agent ולא ב־`.cursor/mcp.json`.

MCP רשמי של Google Cloud (`aiplatform.googleapis.com/mcp/…`) הוא **Gemini Enterprise / GCP** — לא מנוי הצרכן, לא על השולחן הזה.

## Desktop / Cloud — מפתח

1. [Google AI Studio](https://aistudio.google.com/apikey) — צרו מפתח. זה **לא** לוגין ל־`gemini.google.com`.
2. ייצאו למשתמש בלבד:

```bash
export GEMINI_API_KEY="…"   # מחוץ לגיט
python3 scripts/vf_gemini.py status
python3 scripts/vf_gemini.py models
python3 scripts/vf_gemini.py orchestra
```

3. Cloud Agent: סוד סביבה אחרי ראש צוות — לא בקובץ הפרויקט. בלי סוד: failover מיידי ל־ChatGPT + Perplexity + `WebSearch`.
4. Cursor Desktop כ־**מודל** (Settings → Google) זה ערוץ נפרד; עדיין לא מחליף את שולחן התזמורת 06:15.

## פקודות

| פקודה | מה |
|---|---|
| `status` | יש מפתח? אף פעם לא מדפיסים אותו |
| `models` | רשימה חיה של מודלי טקסט `generateContent` |
| `ask "…"` | קריאה אחת. `--pro` / `--model` / `--ground` |
| `orchestra` | שולחן 06:15 → `packages/vfresearch/sources/YYYY-MM-DD-gemini-api.md` |

מודל ברירת מחדל = הגבוה ביותר ברשימה החיה (Flash לתזמורת, `--pro` ל־Pro). אין ID מומצא אם הרשימה ריקה.

## Failover

דפדפן `gemini.google.com` נחסם / הזדהות → `vf_gemini.py orchestra` אם יש מפתח → אחרת ChatGPT + Perplexity + `WebSearch`.  
אין גוף → **אין גוף** / דולג. לא ממציאים.  
`constitution/ORCHESTRA.md`.

## VF

לא `mcpBind` חדש. לא שרת ב־`.cursor/mcp.json`.  
אינסטגרם עדיין Canva קודם. אין Veo/Kling מ־HQ.
