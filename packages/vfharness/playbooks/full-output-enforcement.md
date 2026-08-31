# אכיפת פלט מלא

מושב: רתמה (`vfharness`). מקור: [taste-skill `output-skill`](https://github.com/Leonxlnx/taste-skill) (MIT) + `research/laziness/`.  
לא runtime שני. לא pack חדש.

## חוק אחד

**פלט חלקי = פלט שבור.** אין לקצר כדי «לחסוך טokens». אין skeleton כשביקשו קובץ מלא.

## דפוסים אסורים (hard fail)

**בקוד:** `// ...`, `// rest of code`, `// implement here`, `// TODO`, `/* ... */`, `// similar to above`, `...` במקום קוד

**בפרוזה:** «תגידו אם להמשיך», «for brevity», «the rest follows the same pattern», «I'll leave that as an exercise»

**מבני:** שלד במקום מימוש; רק ראש וסוף; תיאור במקום קוד

## תהליך

1. **Scope** — ספור deliverables (קבצים, סעיפים, תשובות). נעל מספר.
2. **Build** — כל deliverable במלואו.
3. **Cross-check** — לפני סגירה: השווה לבקשה המקורית. חסר → השלם.

## כשגובלים במגבלת tokens

- לא לדחוס סעיפים שנשארו.
- לא לדלג לסיכום.
- כתוב באיכות מלאה עד נקודת שבירה נקייה (סוף פונקציה / קובץ / סעיף).
- סיים ב:

```
[PAUSED — X מתוך Y. שלחו "continue" להמשך מ: שם הסעיף הבא]
```

על «continue» — המשך מאותה נקודה. בלי recap. בלי חזרה.

## checkpoint

משימה ארוכה עם `[PAUSED]` → עדכון `packages/vfharness/state/<task-id>.json` לפני סגירת התור.

## VF overrides

| taste-skill | HQ |
|---|---|
| קוד frontend מלא | גם חבילות markdown, sensors, HTML brief |
| אנגלית | עברית מוצר; משרד אנגלית+עברית |
| brandkit generator | **אסור** — לא hex/fonts מומצאים |
| שליחה | Gmail/IG רק לפי `constitution/SEND.md` |

## research/laziness — מה שווה לזכור

- **RLHF / compute** — נטייה לקצר; counter: scope lock + banned patterns.
- **Training placeholders** — `// ...` מדביק; counter: sensor + playbook.
- **Output limits** — `[PAUSED]` + checkpoint, לא «סיכמתי».
- **Architectural** — skills/playbooks נטענים לפי job; לא warehouse שלם.

## קישורים

- שתילה: `docs/TASTE-SKILL-EMBED-he.md`
- לולאה: `packages/vfharness/LOOP.md`
- escalation: `packages/vfharness/templates/escalation.md`
