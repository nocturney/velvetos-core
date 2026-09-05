# סוף יום — רטרו משרד (ראש צוות)

מודול: `office-learning`.  
**ראש הצוות** (`@studio-operations` / `@chief-of-staff`) מבקש מכל המושבים לעבור על השיחות של היום — לא כדי לשפוט, אלא כדי שהמשרד יהיה חי ומשתפר.

**פעם ראשונה / לפני שהרוטינה הייתה קיימת:** הרץ `INITIAL-RETRO.md` (catch-up מ-CHANGELOG + checkpoints).

## מתי

כל ערב, אחרי 18:00 Asia/Jerusalem (או לפני סגירת משמרת).  
5–15 דקות. לא דורש כלי חיצוני — רשימת בדיקה + עדכון זיכרון.

## הודעה לצוות (תבנית)

> עברו על כל השיחות מהיום. מה למדנו על הבעלים / הסטודיו / הלקוחות?  
> מה לשמור לזיכרון המשותף? מה לתקן מחר?  
> כתבו שורה אחת לפחות ל־`vfops/data/owner-memory.md` אם זה עובר לכולם.

## רשימת בדיקה לכל מושב

| מושב | שאלות |
|---|---|
| ראש צוות | החלטות פתוחות? סנסור אדום? מה נשלח מ־HQ? |
| סטודיו | פניות שלא נסגרו? טון שהבעלים אהב / לא אהב? |
| צמיחה | מה יצא ללוח? הוק שעבד? חסר proof? |
| תפעול | חשבונות חדשים? ₪ רק ממקור — לא המצאה |
| ייצור | mesh שנכשל? תור? רישיון חסר? |

## טריגרי self-improving (באותו ערב)

דפוס מ־ClawHub `self-improving` (דירוג best-skills) — **בלי** runtime `~/self-improving/`. על המשרד הקיים:

| מתי | מה לעשות |
|---|---|
| משתמש תיקן / דחה תוצר | שורה ב־`owner-memory.md` + אם חוזר → ANTI-PATTERN |
| כלי / פקודה נכשלו | לרשום failover אמיתי; לא «אמור לעבוד» |
| גילינו גישה טובה יותר | לעדכן פלייבוק/סקיל בפק הקיים **אותו יום** אם זה חוזר |
| דירוג best-skills חשף דפוס | `BEST-SKILLS.md` · הטמעה במקום |
| טענת הצלחה בלי אימות | Mastery gate — `verification-before-claim.md` · `MASTERY-MEMORY.md` |
| אותה טעות פעמיים | Question-bank → ANTI-PATTERN או `LEARNING-RECORDS.md` |

## פלט חובה

1. **שורת יום** ב־`packages/vfops/data/owner-memory.md` (תאריך + תובנה אחת)
2. **Checkpoint** אם job רב־שלבי פתוח — `vfharness/state/<task-id>.json`
3. **תיקון מדריך** — אם אותה טעות פעמיים → שורת ANTI-PATTERN ב־`AGENTS.md` (מחר, לא הלילה)
4. **אימות** לפני «סיימנו את הרטרו» — `playbooks/verification-before-claim.md`

## מה לא לשמור

- סודות, מפתחות, PHI
- תיקיות אישיות / רפואיות / משפטיות בדרייב
- ₪ / Insights / מגמות בלי מקור
- העדפות חד־פעמיות שלא חוזרות

## קישורים

- `packages/vfmem/MEMORY-UPDATE.md` — איך כותבים לזיכרון המשותף
- `packages/vfharness/playbooks/daily-learning.md` — לולאת למידה לסוכן
- `.cursor/skills/vf-daily-learning/SKILL.md` — הפעלה ב־Cursor
- `packages/vfops/hq/MASTERY-MEMORY.md` — DeepTutor: mastery gate + L1/L2/L3 (דפוס בלבד)

## בוקר למחרת

בריף 07:00 קורא את `owner-memory.md` (בלוק קצר) — לא תיבת דואר.  
`python3 scripts/vfmem.py who "daily retro"` → מסלול זה.
