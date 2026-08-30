# vffcc — Free Claude Code fit

מפה של [Alishahryar1/free-claude-code](https://github.com/Alishahryar1/free-claude-code) אל משרד Velvet Factory.

FCC הוא פרוקסי מקומי (MIT) לסוכני קוד: Claude Code, Codex, Pi, OpenCode ועוד. הוא מנתב בקשות למפתחות **של הבעלים** אצל ספקים עם שכבה חינמית (NVIDIA NIM, Groq, Gemini, OpenRouter, …). הפרויקט מצהיר שהוא ToS-friendly ו־BYOK — לא גניבת טוקנים של Anthropic.

## התשובה הקצרה

| שאלה | תשובה |
|---|---|
| אפשר לחסוך מכסת Cursor Cloud עם FCC? | **לא.** הריצה הזו עדיין על מודל Cursor. |
| אפשר להתקין FCC כאן ב־HQ? | **לא.** נעילת `vfe2b`: אין משרד קידוד שני. |
| אפשר להוריד טיוטות קוד זולות במחשב של כריסטיאן? | **כן, אחרי ראש צוות.** מפתחות רק ב־`~/.fcc/`. |
| מה כן חוסך מכסה **עכשיו** בלי התקנה? | נוהל `playbooks/cursor-thrift.md` — שולחן לא מחסן, בלי MCP כפול, בלי סוכן ענן לשאלת קטלוג. |

פירוט: [`docs/FCC-FIT.md`](../../docs/FCC-FIT.md).

## מה כן אצלנו

| דפוס מ־FCC | פק | מה עושים |
|---|---|---|
| פרוקסי מקומי + מפתח חינם | `vfbiz`, `vfops` | ראש צוות מחליט אם להתקין **על המק**. לא ב־Cloud Agent |
| RTK / פחות טוקני טרמינל | `vfops` | דפוס: לקצר פלט. לא מתקינים RTK ב־HQ |
| נפילת ספק → מודל גיבוי | `vfops` | כבר יש: תזמורת ChatGPT + Gemini + Perplexity |
| Gemini / ChatGPT כספק | `vfresearch` | נשארים שולחנות 06:15. לא שכפול כפרוקסי |
| Discord / Telegram / Voice | — | דולג. HQ לא שולח |

## מה לא

ראה [`LOCK.md`](LOCK.md): אין `fcc-server` כאן, אין מפתחות בגיט, אין בוט שליחה, אין «קלוד חינם» מ־Cursor Cloud.

## קבצים

| קובץ | תפקיד |
|---|---|
| [`catalog.json`](catalog.json) | ספקים + לקוחות + נעילות, קריא למכונה |
| [`playbooks/cursor-thrift.md`](playbooks/cursor-thrift.md) | חיסכון מכסת Cursor בלי FCC |
| [`playbooks/local-offload.md`](playbooks/local-offload.md) | התקנה מקומית אחרי ראש צוות |
| [`playbooks/route.md`](playbooks/route.md) | מתי נשארים ב־Cursor ומתי (אם בכלל) יורדים למק |
| [`scripts/check-vffcc.py`](../../scripts/check-vffcc.py) | בדיקת עקביות מול `packages/manifest.json` |

## איך מפעילים

ב־Cursor:

```
@vffcc route
@vffcc thrift
@vffcc local-offload
```

או פותחים את הנוהל ב־`playbooks/`.

`python3 scripts/check-vffcc.py` — צפי: `OK providers playbooks locks`.
