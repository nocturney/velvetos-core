# Free Claude Code — מה נכנס למשרד

מקור: [Alishahryar1/free-claude-code](https://github.com/Alishahryar1/free-claude-code) (נקרא 2026-08-30).  
MIT. README מצהיר: ~50 ספקים, BYOK, «ToS friendly», לא משויך ל־Anthropic. כוכבים ביום הקריאה: ראו את הריפו — אנחנו לא ממציאים מכסת טוקנים שנותרה.

פק הקטלוג: [`packages/vffcc/`](../packages/vffcc/).  
מפה מכונה: [`packages/vffcc/catalog.json`](../packages/vffcc/catalog.json).  
בדיקה: `python3 scripts/check-vffcc.py`.

## מה זה באמת

FCC מריץ `fcc-server` על המחשב של המשתמש (`localhost:8082`) ומחבר אליו לקוחות קוד (Claude Code, Codex, OpenCode, …). הלקוח מדבר בפרוטוקול Anthropic/OpenAI; הפרוקסי שולח את הבקשה לספק שהבעלים הדביק לו מפתח (NVIDIA NIM, Groq, Gemini, OpenRouter, …).

זה **לא**:

- טוקנים גנובים של Claude Pro
- מחליף ל־Cursor Cloud Agent
- כלי שליחה (אינסטגרם / ג׳ימייל / וואטסאפ)
- שולחן רביעי בתזמורת 06:15

הריצה שכתבה את המסמך הזה רצה על מודל Cursor (`cursor-grok-4.6-high-fast`). FCC לא יכול להקטין את החשבון שלה.

## כבר יש אצלנו — לא לשכפל

| מה ב־FCC | אצלנו | למה לא פק/ראנטיים חדש |
|---|---|---|
| קטלוג מודלים + fallback | `constitution/ORCHESTRA.md` | ChatGPT + Gemini + Perplexity כבר שלושה שולחנות |
| Gemini / ChatGPT כספק | `vfresearch` | נפתחים בדפדפן ב־06:15 |
| סוכן קוד בטרמינל | המשרד הזה (Cursor) | נעילת `vfe2b`: אין משרד קידוד שני ב־HQ |
| דיסקורד / טלגרם / קול | אדם ב־`050-2517000` | HQ לא שולח |
| «1.3B+ free tokens» | — | טענת ספקים; אין ספירה אצלנו |

## להטמיע עכשיו (נהלים, לא בוט)

| # | רעיון | נוהל | חבילות |
|---|---|---|---|
| 1 | מתי Cursor ומתי מק | [route](../packages/vffcc/playbooks/route.md) | `vfops`, `vfbiz`, `vfresearch` |
| 2 | חיסכון מכסת Cursor בלי FCC | [cursor-thrift](../packages/vffcc/playbooks/cursor-thrift.md) | `vfops`, `vfbiz` |
| 3 | התקנה מקומית אחרי ראש צוות | [local-offload](../packages/vffcc/playbooks/local-offload.md) | `vfbiz`, `vfops` |

## ספקים — פסק דין קצר

| ספק | פסק | למה |
|---|---|---|
| NVIDIA NIM, Groq, Gemini API, OpenRouter free | `local` | שכבה חינמית שפורסמה ב־README; מפתח על המק בלבד |
| ChatGPT connect, Ollama/LM Studio | `later` | כפילות תזמורת / צריך חומרה |
| xAI, Azure/Bedrock/Vertex, Discord/Telegram/Voice | `skip` | שולח חי / ענן ארגוני / שליחה |
| שאר רשימת ה־BYOK | `later` | הבעלים בוחר מפתח אחד; HQ לא מוסיף |

פירוט: `packages/vffcc/catalog.json`. נעילות: `packages/vffcc/LOCK.md`.

## מה מדלגים תמיד

- `curl …/install.sh` מתוך Cloud Agent
- שכפול עץ FCC לגיט
- מפתחות בריפו
- טענה ש«עכשיו יש לנו קלוד חינם ב־Cursor»
- בוט דיסקורד/טלגרם, Whisper, OpenClaw-on-phone כערוץ סטודיו
