# Best Skills — דופק 48 שעות דרך Research Seat

**Standing order (בעלים 2026-09-03):** סקירת Best Skills כל ~48 שעות **לנצח**, עד הודעה מפורשת לעצור או לשנות קצב.

סמכות תזמון: **Velvet Research Seat**.  
יעד רעננות: `48h` · grace: `4h`.  
מצב קנוני: `packages/vfresearch/BEST-SKILLS.json` (`lastPass`, `lastArtifact`, `lastResult`).

אין תלות ב־`cursor-subscriptions` או במנוי חיצוני. Research Seat של 02:00 בודק בכל ריצה האם `lastPass` עבר את חלון ה־48h; אם כן הוא מריץ את `vf-best-skills` כחלק מאותה ריצת מחקר. אסור לפתוח automation נוסף רק עבור Best Skills.

## חובה בכל מעבר

בסוף כל סקירת best-skills, גם אם התוצאה היא «אין חדש במשרד»:

1. לכתוב `packages/vfresearch/sources/YYYY-MM-DD-best-skills.md`.
2. לעדכן `BEST-SKILLS.json`: `lastPass`, `dataDate`, `lastArtifact`, `lastResult`.
3. לעדכן בלוק `05` ב־`packages/vfops/data/research.md` כשיש חומר לבריף.
4. אחרי שינוי pack/rule/catalog להריץ `python3 scripts/check-all.py`.
5. לאמת freshness דרך state/artifact — לא דרך receipt של timer חיצוני.

`lastPass` ישן מ־52 שעות הוא מצב stale: Research Seat חייב לבצע את המעבר הבא או לדווח blocker אמיתי. אין המצאת מעבר ואין סימון fresh ללא artifact תואם.

## מה Research Seat מריץ

1. קורא `BEST-SKILLS.md` + `BEST-SKILLS.json` + קובץ זה.
2. מושך את דירוגי LinklyAI/best-skills ממקור ציבורי מאומת.
3. משווה ל־`lastPass` / `watchlist` / `embedded`.
4. מטמיע רק דפוסים שימושיים בתוך packs קיימים; לא `npx skills`, לא runtime שני.
5. כותב artifact ועדכון state כאמור למעלה.

## איך הבעלים עוצר

הודעה מפורשת («עצור best-skills» / «שנה קצב») →

1. `BEST-SKILLS.json` → `"standingForever": false` + `"stoppedAt"` + סיבה.
2. עדכון ב־owner memory לפי כללי הזיכרון.
3. Research Seat מפסיק את בדיקת ה־48h עד הוראה חדשה.

בלי הוראה כזו — ממשיכים.
