# איך מחברים ChatGPT API (לא מנוי הדפדפן)

לא ב־`.cursor/mcp.json` של הריפו — צריך `OPENAI_API_KEY`. שמים **בסביבת המשתמש / סוד Cloud**, לא בגיט.

**מנוי ChatGPT Plus / Pro ב־`chatgpt.com` ≠ OpenAI API.**  
המנוי נותן צ'אט בדפדפן, GPTs, Canvas, Deep Research.  
ה־API (`platform.openai.com`) נותן `chat.completions` עם מפתח, **חיוב נפרד**. [עזרת OpenAI: Plus לא כולל API](https://help.openai.com/en/articles/6950777).

גשר HQ: `python3 scripts/vf_chatgpt.py`.  
בלי מפתח: **חסר מפתח ChatGPT**. לא ממציאים גוף.  
לא פותחים `chatgpt.com` מדפדפן Cloud Agent — זה מקור התראות האבטחה. פלייבוק: [`SUBSCRIPTIONS.md`](SUBSCRIPTIONS.md).

## Desktop / Cloud — מפתח

1. [OpenAI API keys](https://platform.openai.com/api-keys) — צרו מפתח. זה **לא** לוגין ל־ChatGPT Plus.
2. ייצאו למשתמש בלבד:

```bash
export OPENAI_API_KEY="…"   # מחוץ לגיט
python3 scripts/vf_chatgpt.py status
python3 scripts/vf_chatgpt.py models
python3 scripts/vf_chatgpt.py orchestra
```

3. Cloud Agent: סוד סביבה אחרי ראש צוות. בלי סוד: failover ל־Gemini API / Perplexity / `WebSearch`.
4. Cursor Desktop → Models → OpenAI הוא ערוץ נפרד; לא מחליף את 06:15.

## פקודות

| פקודה | מה |
|---|---|
| `status` | יש מפתח? אף פעם לא מדפיסים אותו |
| `models` | רשימה חיה של מודלי צ'אט |
| `ask "…"` | קריאה אחת. `--pro` / `--model` |
| `orchestra` | שולחן 06:15 → `packages/vfresearch/sources/YYYY-MM-DD-chatgpt-api.md` |

מודל ברירת מחדל = הגבוה ביותר ברשימה החיה. אין ID מומצא אם הרשימה ריקה.

## VF

לא `mcpBind` חדש. לא שרת ב־`.cursor/mcp.json`. אין שמירת עוגיות.
