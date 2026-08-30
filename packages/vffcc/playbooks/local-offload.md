# הורדה מקומית (מק של כריסטיאן)

רק אחרי שראש צוות אמר כן. לא רץ ב־Cloud Agent. לא חלק מ־06:15.

FCC ([README](https://github.com/Alishahryar1/free-claude-code)) הוא `fcc-server` על `localhost:8082` + לקוח (`fcc-claude`, `fcc-codex`, …). מפתחות נשארים אצל הבעלים.

## לפני התקנה

1. ראש צוות אישר הורדת **קידוד ניסיוני** מהמק — לא החלפת HQ.
2. אין מפתח בגיט, לא ב־`.env` של הריפו, לא בפריט Drive משותף.
3. העבודה לא צריכה Gmail / יומן / Drive / Canva / Treg. אם כן — נשארים ב־Cursor.

## התקנה (על המק, לא כאן)

הבעלים מריץ אחרי שקרא את הסקריפט (לא מצינור עיוור מ־HQ):

```bash
# review first:
# https://github.com/Alishahryar1/free-claude-code/blob/main/scripts/install.sh
curl -fsSL "https://raw.githubusercontent.com/Alishahryar1/free-claude-code/main/scripts/install.sh" | sh
fcc-server
```

ב־Admin UI מדביקים מפתח **אחד** להתחלה. סדר מומלץ לסטודיו (שכבה חינמית שפורסמה ב־README של FCC, 30.8.2026):

| עדיפות | ספק | למה |
|---|---|---|
| 1 | NVIDIA NIM | ברירת המחדל של FCC; מפתח ב־build.nvidia.com |
| 2 | Groq | שכבה חינמית; מהיר לטיוטות |
| 3 | Google AI Studio (Gemini) | כבר שולחן תזמורת; מפתח נפרד לפרוקסי |
| 4 | OpenRouter `openrouter/free` | מודלים חינמיים; איכות משתנה |

Fallback Models ב־Admin — לפי הסדר למעלה. ספק שנכשל עלול לצרוך גם מהבא אחריו.

## מה מריצים שם

רק סוכן קוד מקומי. מומלץ **אחד**: `fcc-claude` או `fcc-opencode`. לא את העשרה.

## מה אסור גם על המק

- לחבר Discord / Telegram
- Voice / Whisper
- להעתיק מפתחות לתוך קלונים של HQ
- לשלוח אינסטגרם / וואטסאפ / מייל
- לפתוח תיקיות רפואיות / משפטיות / אישיות
- לכתוב מחיר ₪ או Insights

## אחרי הניסוי

תוצר שימושי מיד → הטמעה בפק **קיים** (כמו תזמורת). אין פק «FCC runtime».  
לא שימושי → «אין חדש במשרד». כותבים שורה ב־`vfresearch/sources/` בלי להמציא מכסה.
