# מחקר · aliargun/mcp-server-gemini · 5.9.2026

מושב: תפעול / מחקר. פק `vfmcp`. לא פק חדש. לא סוד בגיט.

מקור: [aliargun/mcp-server-gemini](https://github.com/aliargun/mcp-server-gemini)  
README + `ENHANCED_FEATURES.md` + GitHub API (`pushed_at` 2025-07-14, last commit `d90346a` 14.7.2025).  
מודלי API חיים (דוקומנטציה `ai.google.dev`, ספטמבר 2026): Gemini 3.x (`gemini-3.5-flash`, `gemini-3.1-pro-preview`, …) ליד 2.5.

## שאלה 1 — האם זה מחליף דפדפן למנוי Gemini?

**לא.** השרת דורש `GEMINI_API_KEY` מ־[Google AI Studio](https://aistudio.google.com/apikey). זה מוצר נפרד ממנוי Plus/Advanced ב־`gemini.google.com`.

| מנוי הדפדפן | Gemini API |
|---|---|
| Gems, Canvas, Deep Research | אין |
| Connected Apps (Gmail/Drive/YouTube) | אין — אצלנו כבר Gmail/Drive/Calendar MCP |
| סשן Google Account | מפתח + חיוב API נפרד |
| חומת הזדהות ב־Cloud Agent (2.9.2026) | לא נפתרת ע״י MCP הזה |

חיבור המנוי עצמו ל־Cursor בלי דפדפן **לא קיים** בריפו הזה. OAuth ל־`gemini.google.com` / Gems אינו חלק מהשרת.

## שאלה 2 — מה מפגר?

- Freeze יולי 2025: מודלים קשיחים 2.5/2.0/1.5; «thinking» של 2.5 בלבד.
- MCP spec `2024-11-05`.
- שישה כלים: generate / vision / count / list / embed / help. בלי Files API, בלי code execution, בלי Interactions API, בלי image-gen native, בלי Veo.
- `list_models` אצלם הוא קטלוג מקומי, לא `GET /v1beta/models`.
- Google Cloud מפרסם MCP ארגוני (`aiplatform.googleapis.com/mcp/…`) — לא המנוי, לא AI Studio key, לא על שולחן VF.

## מה הוטמע (גשר על פק קיים)

| פער | גשר |
|---|---|
| מנוי ≠ API | `packages/vfmcp/CONNECT-GEMINI.md` |
| מודלים קשיחים | `scripts/vf_gemini.py models` — רשימה חיה |
| דפדפן נחסם בתזמורת | `vf_gemini.py orchestra` אם יש מפתח; אחרת ChatGPT+Perplexity+WebSearch |
| התקנת vendor MCP + מפתח בגיט | אסור. לא aliargun ב־`.cursor/mcp.json` |
| בלי מפתח על Cloud | «חסר מפתח Gemini» · אין גוף מומצא |

לא הותקן aliargun. לא Veo. לא Canva שני.

## Failover שבוצע במחקר

GitHub README נקרא. דוקו מודלים מ־`ai.google.dev` (3.x + 2.5). לא הומצא גוף דפדפן. מפתח API **חסר** בסביבה הזו — `vf_gemini.py status` חייב להחזיר «חסר מפתח Gemini».
