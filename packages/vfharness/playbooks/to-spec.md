# To-spec — רשומת החלטות לפני פיצול סשנים

מקור דפוס: [mattpocock/skills `to-spec`](https://github.com/mattpocock/skills/tree/main/skills/engineering/to-spec) (trending LinklyAI 2026-09-11).  
**דפוסים בלבד** — לא `npx skills add`. לא issue-tracker חובה. לא runtime שני.

## מתי

אחרי ש־`brainstorm-gate` / grill סיימו **החלטות**, והעבודה **לא נכנסת לסשן אחד**.  
לפני `writing-plans` / `executing-plans` כשצריך מסמך ששורד ניקוי חלון הקשר.

| מצב | מה לעשות |
|---|---|
| עוד לא הוחלט | `brainstorm-gate` / grill — לא כאן |
| הוחלט, נכנס לסשן אחד | ישר ל־`executing-plans` / יישום — דלג על spec |
| הוחלט, חוצה סשנים / סוכנים | **to-spec** → אחריו `writing-plans` או כרטיסי משימה ב־`state/` |

## מה זה כן / לא

- **כן:** סינתזה של מה שכבר הוחלט בשיחה + קוד + `domain-glossary` + ADR רלוונטי.
- **לא:** סיבוב שאלות חדש. כל טענה שלא נאמרה בשיחה = פגם ב־spec.
- **לא:** פרסום חובה ל־GitHub Issues (אין דסק triage GH ב־VF). שומרים ב־`packages/vfharness/state/<task-id>/spec.md`.

## תפרים (seams) לפני פרוזה

1. צייר 1–3 תפרי בדיקה ברמה הגבוהה ביותר האפשרית (עדיף תפר קיים).
2. אשר עם ראש צוות / בעלים שהתפרים נכונים.
3. רק אז כתוב את ה־spec. תפר שלא אושר → ממצא ב־review, לא הפתעה ביישום.

## תבנית קצרה (VF)

```markdown
# <שם> — spec

**Problem:** … (מזווית המשתמש/המשרד)
**Solution:** … (מה שכבר הוחלט)
**Seams:** …
**In scope / Out of scope:** …
**Implementation decisions:** מודולים, חוזים, ADR — בלי נתיבי קבצים שבירים
**Testing decisions:** התנהגות חיצונית בלבד; לא פרטי מימוש
**Constraints:** אין ₪ מומצא · אין Insights מומצא · אין runtime שני · אין npx ·
  PUBLIC_CURRENT_CTA = הודעת Instagram · BUSINESS_CONTACT_RECORD וואטסאפ פנימי בלבד
**Glossary:** מונחים מ־domain-glossary / TEAM בלבד
```

## שרשרת

`brainstorm-gate` → **to-spec** (רב־סשן) → `writing-plans` → `executing-plans` → `verification-before-claim`

## אסור

- המצאת דרישות שלא נאמרו
- AFK שמריץ את כל ה־spec בלי כרטיסים/תוכנית
- `npx` / OpenClaw / סוכן־על חיצוני
- CTA ציבורי בוואטסאפ / `050-2517000`
