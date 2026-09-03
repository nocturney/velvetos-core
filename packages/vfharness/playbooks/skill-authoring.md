# Skill authoring — כתיבת מיומנויות HQ

מקורות דפוס (LinklyAI/best-skills):

- [anthropics/skills `skill-creator`](https://github.com/anthropics/skills)
- [obra/superpowers `writing-skills`](https://github.com/obra/superpowers)

**לא** `npx skills` על Cloud Agent. סקילים חיים ב־`.cursor/skills/<name>/SKILL.md` + פלייבוק בפק.

## מתי ליצור / לעדכן סקיל

**כן:** טכניקה לא מובנת מאליה · חוזרת בין סשנים · רחבה מעבר לקונבנציית פרויקט אחת.  
**לא:** פתרון חד־פעמי · מה שאפשר לאכוף בסנסור regex · פק חדש לרעיון (ממפים לפק קיים).

## מחזור (TDD על תהליך)

1. **לחץ** — תרחיש שבו הסוכן נכשל בלי הסקיל (רשום את התירוצים).
2. **טיוטה** — `SKILL.md` שמכסה את הכשלים האלה.
3. **אימות** — להריץ את אותו תרחיש עם הסקיל; לתקן פרצות.
4. **סנסור** — אם הכלל חייב להחזיק כל ריצה → `scripts/check-*.py`.

## אנטומיה

```
.cursor/skills/<name>/
  SKILL.md          # frontmatter: name + description (מתי להפעיל)
packages/<pack>/…   # playbook / templates שהסקיל מצביע אליהם
```

- **description** = מתי להפעיל (קצת «דוחף» — מניעת under-trigger).
- גוף < ~500 שורות; פירוט ב־`references/` או פלייבוק בפק.
- Progressive disclosure: מטא־דאטה תמיד · גוף כשמופעל · קבצים נלווים לפי צורך.

## חוקי VF

- הטמעה על פק **קיים** באותו יום
- נעילות: אין אוטו־DM, אין ₪ מומצא, HQ שולח דרך כלים
- אחרי שינוי: `python3 scripts/check-all.py`
- רישום מקור חיצוני ב־`vfresearch/LINKS.json` או `BEST-SKILLS.json`

## בדיקת תיאור (trigger)

אם הסקיל לא נדלק כשצריך — לחזק את ה־description עם מילות מפתח שהמשתמש באמת אומר (עברית+אנגלית).
