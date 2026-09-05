# מנויי מחקר · בלי דפדפן פנימי

לא פק חדש. פק `vfmcp`.  
המטרה: שולחנות מחקר קבועים בלי התראות «גישה לא מורשית» לחשבון Google / OpenAI / Perplexity.

**בעלים 5.9.2026:** אין חיוב API נפרד. מנויי Plus/Pro בדפדפן **לא** כוללים מפתח מפתחים, והבעלים לא רוצה אחד. בלי מפתח HQ כותב «חסר מפתח …» ועובר ל־WebSearch. לא דוחקים מפתח. לא ממציאים גוף.

## למה הדפדפן הפנימי מפיל אזעקות

Cloud Agent ו־Grok Bot נכנסים ל־`gemini.google.com` / `chatgpt.com` מ־IP של חוות שרתים שמשתנה כל ריצה.  
Google ו־OpenAI רואים לוגין חדש ממכונה זרה → התראות אבטחה, 2FA, ניתוק סשן.  
שמירת עוגיות / פרופיל כרום / «להישאר מחוברים» **אסורה** — זה נראה כמו גניבת סשן, לא פותר את ה־IP, ומפר «אין סוד בגיט».

**דין HQ:** Cloud Agent **לא** פותח את אתרי המנוי.  
**גישה מלאה וקבועה בלי חיוב API** = מק ייעודי בשדרות כמארח (לא PC ווינדוס יומי). פלייבוק: [`HOST.md`](HOST.md).

## מה כן — API, לא מנוי דפדפן

| שולחן בדפדפן | מוצר HQ | מפתח (מחוץ לגיט) | פקודה |
|---|---|---|---|
| Gemini Plus/Advanced ב־`gemini.google.com` | Google AI Studio **API** | `GEMINI_API_KEY` | `python3 scripts/vf_gemini.py orchestra` |
| ChatGPT Plus/Pro ב־`chatgpt.com` | OpenAI **API** | `OPENAI_API_KEY` | `python3 scripts/vf_chatgpt.py orchestra` |

המנוי **לא** כולל את ה־API. זה חיוב נפרד ([ChatGPT Plus ≠ API](https://help.openai.com/en/articles/6950777) · Gemini AI Studio key ≠ Google One).  
ה־API **לא** נכנס לחשבון Gmail/ChatGPT — לכן אין התראות «מישהו התחבר לחשבון».

פלייבוקים: [`CONNECT-GEMINI.md`](CONNECT-GEMINI.md) · [`CONNECT-CHATGPT.md`](CONNECT-CHATGPT.md).

## מה הבעלים עושה

בלי חיוב API: מארח אחד — מק ייעודי בשדרות (לא הווינדוס). [`HOST.md`](HOST.md):

1. **על המק:** Chrome פרופיל קבוע + לוגין לשלושת האתרים (לוגין בווינדוס לא עובר). אחר כך `agent worker --computer-use --name "sderot-mac" start`.
2. על המק: Gemini = Antigravity `agy` (אומת 5.9: Google AI Plus, Gemini 3.8 Flash High). Codex = `0.153.4` מחובר (`Successfully logged in`, ChatGPT Plus). לא מפתח API. לא מעתיקים `ANTIGRAVITY_TOKEN` / `~/.codex`.
3. Cloud משתמש ב־`WebSearch` / `WebFetch` וקורא `vfresearch/sources/` אחרי שהמק שמר תוצר.
**לא** להתחבר ל־`gemini.google.com` / `chatgpt.com` / `perplexity.ai` מדפדפן Cloud Agent או Grok Bot.

אם יום אחד יופיע מפתח ב־env (בלי שנבקש): `vf_gemini.py` / `vf_chatgpt.py` עובדים. בלי מפתח: **חסר מפתח Gemini** / **חסר מפתח ChatGPT**. Failover מיידי ל־WebSearch. אין גוף מומצא.

## מה לא מתקינים

| ריפו | למה לא |
|---|---|
| [aliargun/mcp-server-gemini](https://github.com/aliargun/mcp-server-gemini) | freeze יולי 2025 · 2.5 קשיח · עדיין API |
| [RLabs-Inc/gemini-mcp](https://github.com/rlabs-inc/gemini-mcp) | מעודכן יותר (Gemini 3, יולי 2026) אבל **עדיין** `GEMINI_API_KEY`. 37 כלים + **Veo** (נעול ב־HQ). לא פותר מנוי דפדפן. לא npx ב־Cloud |
| Antigravity CLI `agy auth login` | OAuth למנוי Google **על המק בלבד**. טוקן בענן = שוב IP זר + אזעקות. לא מעתיקים `ANTIGRAVITY_TOKEN` ל־Cloud Agent |
| שמירת cookies / Playwright login | אסור |
| [Automations-Project/VSCode-Perplexity-MCP](https://github.com/automations-project/vscode-perplexity-mcp) (`perplexity-user-mcp`) | **כן** צורך מנוי Pro בלי מפתח API — דרך patchright + עוגיות Cloudflare ב־`~/.perplexity-mcp`. Experimental. ToS של Perplexity. auto-config כותב ל־`.cursor/mcp.json`. **אסור ב־Cloud** (IP זר + vault). לא מעתיקים עוגיות. מק אופציונלי רק אחרי ראש צוות |

## קונספט «מנוי בלי API» (Perplexity browser MCP)

[vscode-perplexity-mcp](https://github.com/automations-project/vscode-perplexity-mcp) (last push `2026-07-17`) הוא **ההפך** מ־aliargun / RLabs / `@perplexity-ai/mcp-server`:

| | MCP רשמי / Sonar API | vscode-perplexity-mcp |
|---|---|---|
| חיוב | מפתח API נפרד מהמנוי | צורך Free/Pro/Max שכבר שולם |
| איך | `Authorization: Bearer` | Chromium + patchright מול `perplexity.ai/rest/sse/…` |
| Cloudflare | אין | Turnstile + `cf_clearance` ב־vault |
| יציבות | חוזה API | נקודת REST פרטית שעלולה להישבר |
| Cloud Agent | מפתח ב־env (הבעלים דחה) | אסור — אותן אזעקות / גניבת סשן |

הקונספט נכון לבעיה («אני משלם Plus, לא רוצה API»). המימוש **לא** שייך ל־Cloud Agent ולא ל־Grok Bot. אותו דפוס ל־Gemini/ChatGPT (סשן כרום בענן) כבר הפיל התראות Google/OpenAI.

שולחן Perplexity ב־HQ: `WebSearch` / «דולג — חומה». לא ממציאים גוף.

## תזמורת 06:15

- **מק (Cursor Desktop):** שלושת המנויים לפי [`HOST.md`](HOST.md).
- **Cloud:** בלי מפתחות API — `WebSearch` / `WebFetch` בלבד. אם יש מפתח ב־env: `python3 scripts/vf_chatgpt.py orchestra` · `python3 scripts/vf_gemini.py orchestra`.

`constitution/ORCHESTRA.md`.
