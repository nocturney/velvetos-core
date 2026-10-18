# סריקת MakerWorld / Printables · א׳ + ד׳

מושב: **מחקר** (`@research-synthesist`) → **ייצור** (`vlicense` / `vfsku` / `vfcost`).  
לא פק חדש. לא סוכן אוטונומי. צוות קיים: `vfe2b/crews/research.md`.  
CLI לבריף 03: `python3 scripts/vfsku.py scan`.

## מתי

ראשון ורביעי בלבד, Asia/Jerusalem, **כאשר scan מופעל במפורש או כחלק מ־Office Loop רלוונטי**. אין גוף מחקר יומי ואין cutoff 07:00; התוצר יכול להזין Morning Brief הבא אם הוא מופעל ורלוונטי.
יום אחר → השורה היא בדיוק «לא יום סריקה» — לא ממלאים שם דגם.

## מה עושים ביום סריקה

1. פותחים MakerWorld / Printables **רק** אם יש קישור שהבעלים / הרצפה נתנו, או דף פומבי שנפתח ב־WebSearch/WebFetch (גוף אמיתי או «אין גוף»).
2. לכל מועמד כותבים כרטיס מחקר תחת `vfresearch/sources/YYYY-MM-DD-makerworld-scan.md`: URL · יוצר · license metadata אם זמין · תמונת אגודל אם יש.
3. שער `vlicense/GATE.md` **לפני** `vfsku`: הוא בודק בעיקר provenance והאם היוצר/מותג ישראלי; license metadata של יוצר לא־ישראלי אינו blocker למחקר/showcase.
4. NC / CC BY-NC / ND / Standard Digital File / unknown license נשמרים כ־metadata בלבד. הם לא חוסמים מחקר, showcase, פוסט/ריל, שימוש אישי ובבית, או מכירה. יוצר/מותג ישראלי = `human_required` מול Christian.
5. סלייס: **רצפה** (Orca / Prusa). HQ רושם גרם/דקות מפלט סלייסר בלבד (`vfcost/SLICE.md`). אין שליחת STL אוטומטית מהענן לסלייסר. אין Print מ־HQ.
6. כרטיס מדף ב־`SHELF.json` אחרי provenance + GATE + סלייס. בלי source אמיתי: «אין שם להציע» בחריץ 03.

## מה לא

- שם MakerWorld מהאוויר / סיטונאות בלי URL
- מחיר מכירה / כמות לפני סלייס + ראש צוות
- Orca כדמון HQ · חיבור למדפסת
- שימוש בחומר גנוב/פיראטי/דלוף או עקיפת גישה

## בלוק לבריף (03)

מגיע מ־`python3 scripts/vfsku.py scan` + `vfsku.py brief`. לא בחריץ 02.

## סיום משמרת

`worker_done` — ארטיפקט סריקה + שורת מדף בלי שם מומצא.  
`escalation` — חומה על כל הדפים / חסר קישור.  
`decision_gate` — ₪ מכירה (לא כאן).
