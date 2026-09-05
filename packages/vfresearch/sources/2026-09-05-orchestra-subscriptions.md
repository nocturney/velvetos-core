# מחקר · מנויי Gemini/ChatGPT בלי דפדפן · 5.9.2026

מושב: תפעול. פק `vfmcp`.

## 1. RLabs-Inc/gemini-mcp מול aliargun ומול HQ

מקור: [rlabs-inc/gemini-mcp](https://github.com/rlabs-inc/gemini-mcp) · last push `2026-07-08` · `@rlabs-inc/gemini-mcp` · `GEMINI_API_KEY` חובה.

| | aliargun | RLabs | `vf_gemini.py` |
|---|---|---|---|
| מוצר | Gemini API | Gemini API | Gemini API |
| מנוי `gemini.google.com` | לא | לא | לא |
| עדכון | 2025-07-14 | 2026-07-08 | רשימה חיה |
| מודלים | 2.5 קשיח | 3 preview קשיח + כלים רחבים | `GET /v1beta/models` |
| כלים | 6 | 37 כולל **Veo**, image 4K, TTS | תזמורת טקסט בלבד |
| סוד | npx env | npx env | env, לא mcp.json |

RLabs **עדיף מ־aliargun** כקטלוג API (מעודכן, Gemini 3, Deep Research, חיפוש).  
**לא תורם יותר לבעיית המנוי** — אותו מפתח AI Studio.  
לא מותקן ב־HQ: Veo נעול, 37 כלים מטביעים את השולחן, npx לא רץ בענן, Canva כבר image.

## 2. גישה קבועה למנוי בלי אזעקות

דפדפן פנימי (Cursor Cloud / Grok Bot) על `gemini.google.com` / `chatgpt.com` = IP חווה + לוגין חדש = התראות Google/OpenAI.  
שמירת סשן / cookies **אסורה**.

דין: Cloud לא פותח אתרי מנוי. Gems/GPTs על המק של הבעלים. HQ = `GEMINI_API_KEY` + `OPENAI_API_KEY` (חיוב API נפרד מהמנוי).

ChatGPT Plus רשמית **לא** כולל API. Gemini Plus **לא** כולל AI Studio key.

Antigravity `agy auth login` = OAuth מנוי **על המק בלבד**. לא מעתיקים טוקן לענן.

## מה הוטמע

`SUBSCRIPTIONS.md` · `CONNECT-CHATGPT.md` · `scripts/vf_chatgpt.py` · תזמורת API-first.
