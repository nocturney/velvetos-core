# PIPELINE — כתיבת content candidate

אין runtime חדש. זה סדר הקריאה/העבודה שכל agent שמפיק קופי מ־`vfcopy` חייב לעקוב אחריו.

## שלבים

| # | שלב | מקור אמת | פלט חלקי |
|---|---|---|---|
| 1 | הקשר מאומת | Drive / `print.done` / הזמנה / מדיה מאושרת | מה רואים · מק״ט · מצב (WIP/גמור) |
| 2 | Business truth | `constitution/` · `PUBLIC_CTA.md` · `STUDIO.md` | אילוצים · CTA מותר |
| 3 | Brand + voice | `VOICE.md` · `VOICE-CHART.md` · `voice/approved/` | מצב קול · דוגמאות |
| 4 | Reader-first | `hq/reader-first-he.md` | מה האדם רואה/מרגיש · הדרך הכי פשוטה להגיד את זה |
| 5 | Writer לפי type | `hq/templates/ig-caption.md` · `organic-reel.md` · `ig-stories.md` · רעיונות carousel/reel מ־ADAPTATION | שלד |
| 6 | Hook / visual microcopy | פרט מהרצפה / מהסרטון — לא סלוגן; ל־cover/overlay: 3–5 מועמדים + `NO_TEXT` | hook / cover / overlay candidates |
| 7 | **velvet-hebrew-copy** | `skills/velvet-hebrew-copy/SKILL.md` | טיוטה בעברית טבעית |
| 8 | Style / Humanizer / AI-tells | `hq/ai-tells-he.md` + `python3 scripts/check-vfcopy.py lint` | לינט · rewrite אחד · מבחן מאפייה |
| 9 | Visual copy decision | השוואה ל־`NO_TEXT` | `TEXT_WINS` עם נימוק או `NO_TEXT` |
| 10 | Factual validation | מחיר / משלוח / זמן / לקוח / Insights | pass או `needs_input` |
| 11 | מסירה | `#vfgrowth` draft + `#vfigos` review | `content_candidate` |

`hq/reader-first-he.md` אינו אופציונלי ל־hook/cover/overlay; הוא שלב חובה לפני ניסוח.  
`vfmskill` copywriting / copy-editing יכול לשמש מסגרת נוספת, אבל אינו עוקף `velvet-hebrew-copy`, `ai-tells-he.md`, `VOICE.md` או את החוקה.

## חוק טקסט על ויזואל

טקסט על cover / first frame / carousel slide / overlay אינו קישוט ואינו ברירת מחדל.

1. מתחילים מ־`NO_TEXT` כ־baseline אמיתי.
2. מייצרים 3–5 ניסוחים רק אם יש פואנטה להוסיף.
3. כל ניסוח עובר reader-first + velvet-hebrew-copy + Humanizer/AI-tells.
4. ניסוח שניתן להלביש על מאפייה/מספרה/פוסט אחר כמעט בלי שינוי נכשל.
5. ניסוח שרק מתאר את מה שכבר רואים נכשל.
6. אם אף ניסוח לא משפר את העצירה/הבהירות/הפואנטה מול הוויזואל הנקי — בוחרים `NO_TEXT`.
7. בחירת בעלים מפורשת היא preference חזקה ונרשמת במניפסט; אין להחליף אותה אוטומטית בניסוח “יותר שיווקי”.

## פלטים חוקיים

- `content_candidate` — גוף מוכן לסקירה (לא לפרסום אוטומטי).
- `needs_input` — חסר עובדה הכרחית; שאלת אדם; **בלי המצאה**.
- `TEXT_WINS` — רק כשנרשם למה הטקסט מוסיף יותר מגרסת No Text.
- `NO_TEXT` — החלטה קריאייטיבית מלאה, לא fallback.

## אחרי candidate

`vfcanva` / `vfcovers` → exact visual render → Brand Guardian → `vfigos` (review / schedule / send via tools per `constitution/SEND.md`).  
שינוי cover/overlay text אחרי render מבטל את ה־exact-final QA ואת package digest הקודם.  
אין auto-DM. אין boost בלי ראש צוות. אין Print מ־HQ.
