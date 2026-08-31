# VelvetOS — ליבה + מודולים

**VelvetOS** = כלי ניהול עסק + עמודי סושיאל אוטונומיים.  
הריפו הזה = **VelvetOS — Velvet Factory** (מופע / instance).  
מודולים לכל האנכיים יושבים **תמיד** בליבה — לא «יעדים פעילים/לא פעילים».

## ארכיטקטורה

```
velvetos-core (ליבה)          instance repos
─────────────────────         ─────────────────────────────
laws · seats · packs          VelvetOS — Velvet Factory  ← זה הריפו
modules/* (הכל טעון)          VelvetOS — <Business Name> ← ריפו נפרד בעתיד
presets (הרכב מומלץ)          שואב מהליבה רק מה שרלוונטי
```

היום הליבה והמופע VF חיים באותו ריפו (`hostsCore: true`). פיצול לריפו ליבתי נפרד — ראו `REPOS.md`.

## שכבות

| שכבה | איפה | תפקיד |
|---|---|---|
| Core laws | `KERNEL` + constitution | שליחה, 5 מושבים, בלי ₪/Insights מומצאים |
| Modules | `modules/` | יכולות מוכנות מראש (print, appointment, document, multi-IG…) |
| Presets | `presets/` | הרכב מומלץ למופע עתידי — **לא** מתג הפעלה כאן |
| Instance | `INSTANCE.json` + `instance/` | הזהות של *המשרד הזה* |

## מודולים (תמיד מאחורי הקלעים)

ראו `modules/catalog.json`. כל מודול קיים בדיסק גם אם המופע הנוכחי לא צורך אותו.

## כלל ברזל

1. עובדים כאן כ־**VelvetOS — Velvet Factory** בלבד.
2. עסק חדש = ריפו מופע חדש (או סביבה חדשה) על בסיס הליבה — לא tenant שני בתוך הריפו הזה.
3. לא ממציאים ₪ / Insights / handles.
4. לא אוטו־DM / בוסט.
5. מודולים נטענים מראש; preset ≠ סביבה חיה.
