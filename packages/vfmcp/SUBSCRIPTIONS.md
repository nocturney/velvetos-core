# מנויי מחקר · בלי דפדפן פנימי

לא פק חדש. פק `vfmcp`.  
המטרה: שולחנות Gemini ו־ChatGPT **קבועים** בלי התראות «גישה לא מורשית» לחשבון Google / OpenAI.

## למה הדפדפן הפנימי מפיל אזעקות

Cloud Agent ו־Grok Bot נכנסים ל־`gemini.google.com` / `chatgpt.com` מ־IP של חוות שרתים שמשתנה כל ריצה.  
Google ו־OpenAI רואים לוגין חדש ממכונה זרה → התראות אבטחה, 2FA, ניתוק סשן.  
שמירת עוגיות / פרופיל כרום / «להישאר מחוברים» **אסורה** — זה נראה כמו גניבת סשן, לא פותר את ה־IP, ומפר «אין סוד בגיט».

**דין HQ:** Cloud Agent **לא** פותח את אתרי המנוי. Gems / GPTs / Canvas / Deep Research של הדפדפן נשארים על המק/הטלפון של הבעלים בלבד.

## מה כן — API, לא מנוי דפדפן

| שולחן בדפדפן | מוצר HQ | מפתח (מחוץ לגיט) | פקודה |
|---|---|---|---|
| Gemini Plus/Advanced ב־`gemini.google.com` | Google AI Studio **API** | `GEMINI_API_KEY` | `python3 scripts/vf_gemini.py orchestra` |
| ChatGPT Plus/Pro ב־`chatgpt.com` | OpenAI **API** | `OPENAI_API_KEY` | `python3 scripts/vf_chatgpt.py orchestra` |

המנוי **לא** כולל את ה־API. זה חיוב נפרד ([ChatGPT Plus ≠ API](https://help.openai.com/en/articles/6950777) · Gemini AI Studio key ≠ Google One).  
ה־API **לא** נכנס לחשבון Gmail/ChatGPT — לכן אין התראות «מישהו התחבר לחשבון».

פלייבוקים: [`CONNECT-GEMINI.md`](CONNECT-GEMINI.md) · [`CONNECT-CHATGPT.md`](CONNECT-CHATGPT.md).

## מה הבעלים עושה פעם אחת

1. [Google AI Studio → API key](https://aistudio.google.com/apikey) → `GEMINI_API_KEY` בסוד Cloud / `~/.cursor` — לא בגיט.
2. [OpenAI platform → API key](https://platform.openai.com/api-keys) + בילינג API נפרד → `OPENAI_API_KEY` אותו מקום.
3. Cursor Desktop (המק בשדרות): Settings → Models → Google / OpenAI אם רוצים מודל מקומי. זה ערוץ נפרד מהתזמורת 06:15.
4. **לא** להתחבר ל־`gemini.google.com` / `chatgpt.com` מדפדפן של Cloud Agent או Grok Bot.

בלי מפתח: **חסר מפתח Gemini** / **חסר מפתח ChatGPT**. Failover מיידי ל־WebSearch + השולחן הפתוח. אין גוף מומצא.

## מה לא מתקינים

| ריפו | למה לא |
|---|---|
| [aliargun/mcp-server-gemini](https://github.com/aliargun/mcp-server-gemini) | freeze יולי 2025 · 2.5 קשיח · עדיין API |
| [RLabs-Inc/gemini-mcp](https://github.com/rlabs-inc/gemini-mcp) | מעודכן יותר (Gemini 3, יולי 2026) אבל **עדיין** `GEMINI_API_KEY`. 37 כלים + **Veo** (נעול ב־HQ). לא פותר מנוי דפדפן. לא npx ב־Cloud |
| Antigravity CLI `agy auth login` | OAuth למנוי Google **על המק בלבד**. טוקן בענן = שוב IP זר + אזעקות. לא מעתיקים `ANTIGRAVITY_TOKEN` ל־Cloud Agent |
| שמירת cookies / Playwright login | אסור |

## תזמורת 06:15 (Cloud)

```
python3 scripts/vf_chatgpt.py orchestra
python3 scripts/vf_gemini.py orchestra
```

Perplexity נשאר WebSearch / חומה.  
`constitution/ORCHESTRA.md`.
