# Verification before claim — אין «סיימתי» בלי ראיה

מקור דפוס: [obra/superpowers `verification-before-completion`](https://github.com/obra/superpowers) (Top repos ב־LinklyAI/best-skills).  
רתמה: `vfharness`. לא runtime שני.

## חוק ברזל

```
אין טענת הצלחה בלי אימות טרי באותו מעבר
```

לפני «עובד» / «ירוק» / «הוטמע» / «נשלח»:

1. **IDENTIFY** — איזו פקודה או כלי מוכיחים?
2. **RUN** — להריץ עכשיו (לא להסתמך על ריצה קודמת בזיכרון).
3. **READ** — קוד יציאה + גוף הפלט.
4. **VERIFY** — האם הפלט באמת תומך בטענה?
5. **ONLY THEN** — לטעון, עם הראיה.

## במשרד שלנו

| טענה | אימות |
|---|---|
| סנסורים ירוקים | `python3 scripts/check-all.py` (או הסנסור הספציפי) — exit 0 |
| בריף נשלח | תוצאת Gmail `send_message` / id הודעה |
| IG פורסם | validate → apply → verify (`vfigos/SEND.md`): כלי publish החזיר confirmed · אחרת `#ממתין-ל-כלי-IG` — **לא** «פורסם» מ־accepted בלבד |
| הטמעה | קובץ בגיט + שורת ארטיפקט `sources/` |
| ₪ / Insights | מקור מאומת · אחרת `X ₪` / «אין ספירה» |

## דגלים אדומים

- «אמור לעבוד» / «נראה תקין» בלי ריצה
- שביעות רצון לפני סנסור
- אמון בדוח סוכן בלי לבדוק דיף / לוג
- דילוג «רק הפעם»

## קשר

- סנסורים: `AGENTS.md` · `scripts/check-*.py`
- פלט מלא: `playbooks/full-output-enforcement.md`
- Orca-style: pulse / verify / artifact ב־`vfe2b`
