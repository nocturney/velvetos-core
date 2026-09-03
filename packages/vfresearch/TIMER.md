# Best Skills — טיימר לנצח (עד שהבעלים עוצר)

**Standing order (בעלים 2026-09-03):** דופק כל ~48 שעות **לנצח**, עד הודעה מפורשת לעצור / לשנות קצב.

שם מנוי: `vf-best-skills-bi-daily`  
מרווח: `delaySeconds: 172800` (48 שעות)  
כלי: `cursor-subscriptions` → `subscribe_timer` (dedupe לפי name)

## חובה בכל מעבר

בסוף **כל** סקירת best-skills (גם אם «אין חדש במשרד»):

1. `list_subscriptions` — לוודא שהטיימר קיים.
2. אם חסר / פג / קרוב לפקיעה → `subscribe_timer` מחדש עם אותו `name` + הפרומפט למטה.
3. לרשום בארטיפקט: `timer: renewed` או `timer: ok`.

אל תסיים מעבר בלי חידוש/אימות טיימר. מנוי Cloud Agent פג אחרי ~7 ימים — **חידוש עצמי** הוא מה שמחזיק לנצח.

## פרומפט ל־subscribe_timer

```
הרץ את סקירת LinklyAI/best-skills (דופק קבוע לנצח עד שהבעלים יעדכן אחרת) לפי skill vf-best-skills ו-packages/vfresearch/BEST-SKILLS.md + TIMER.md.

1. קרא BEST-SKILLS.md + BEST-SKILLS.json + TIMER.md.
2. משוך דירוגי היום מ-https://github.com/LinklyAI/best-skills (best-100, trending-7d, social-buzz, top-repos).
3. השווה ל-lastPass/watchlist/embedded — הטמע דפוסים חדשים על פקים קיימים בלבד. מותר לעדכן חוקה אם דפוס עמיד משפר את המשרד (נעילות ליבה נשארות: אין אוטו-DM, אין npx על Cloud, אין runtime שני, אין ₪ מומצא).
4. כתוב packages/vfresearch/sources/YYYY-MM-DD-best-skills.md ועדכן BEST-SKILLS.json.
5. עדכן בלוק 05 ב-vfops/data/research.md.
6. אחרי שינויים: python3 scripts/check-all.py, commit, push, עדכן PR אם יש.
7. חובה: חדש את הטיימר vf-best-skills-bi-daily (delaySeconds 172800) עם הפרומפט מ-TIMER.md — דופק לנצח עד שהבעלים עוצר.
8. אל תתקין npx skills / OpenClaw. דפוסים בגיט בלבד.

קישור: https://github.com/LinklyAI/best-skills
standing: forever-until-owner-stops
```

פרמטרים:

```
name: vf-best-skills-bi-daily
delaySeconds: 172800
once: false
```

## איך הבעלים עוצר

הודעה מפורשת («עצור best-skills» / «שנה קצב») →:

1. `unsubscribe` על המנוי
2. `BEST-SKILLS.json` → `"standingForever": false` + `"stoppedAt"` + סיבה
3. שורה ב־`owner-memory.md`

בלי זה — ממשיכים.

## גיבוי

אם הטיימר נעלם בין מעברים: weekly links / morning desk שרואים `standingForever: true` חייבים להפעיל מחדש באותו מעבר (`TIMER.md`).
