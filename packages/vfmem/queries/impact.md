# impact

מקור: `trace_path` + `detect_changes`.  
אצלנו: מה נשבר אם נוגעים בפק / סוכן / קובץ.

## מתי

לפני שינוי פק, כלל שולחן, או סקיל. אחרי דיפ מקומי.

## הרצה

```bash
python3 scripts/vfmem.py impact vfsales
python3 scripts/vfmem.py impact studio-operations
python3 scripts/vfmem.py impact --git
```

`impact --git` ממפה `git diff --name-only HEAD` לפקים ולסוכנים. בלי המצאת סיכון.

## קריאה

- `d1` = קשר ישיר (מושב, פק, כלי)
- `d2` = שכנה שנייה
- warehouse לא נמחק כי הופיע ב־blast radius

## אסור

לא לתייג «dead code» על 245 סוכני מחסן. הם בכוונה כבויים.
