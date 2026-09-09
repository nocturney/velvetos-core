# PIPELINE — כתיבת content candidate

אין runtime חדש. זה סדר הקריאה/העבודה שכל agent שמפיק קופי מ־`vfcopy` חייב לעקוב אחריו.

## שלבים

| # | שלב | מקור אמת | פלט חלקי |
|---|---|---|---|
| 1 | הקשר מאומת | Drive / `print.done` / הזמנה / מדיה מאושרת | מה רואים · מק״ט · מצב (WIP/גמור) |
| 2 | Business truth | `constitution/` · `PUBLIC_CTA.md` · `STUDIO.md` | אילוצים · CTA מותר |
| 3 | Brand + voice | `VOICE.md` · `VOICE-CHART.md` · `voice/approved/` | מצב קול · דוגמאות |
| 4 | Writer לפי type | `hq/templates/ig-caption.md` · `organic-reel.md` · `ig-stories.md` · רעיונות carousel/reel מ־ADAPTATION | שלד |
| 5 | Hook | שורה ראשונה מהרצפה / מהסרטון — לא סלוגן | הוק |
| 6 | **velvet-hebrew-copy** | `skills/velvet-hebrew-copy/SKILL.md` | טיוטה בעברית טבעית |
| 7 | Style / AI-tells | `hq/ai-tells-he.md` + `python3 scripts/check-vfcopy.py lint` | לינט · rewrite אחד |
| 8 | Factual validation | מחיר / משלוח / זמן / לקוח / Insights | pass או `needs_input` |
| 9 | מסירה | `#vfgrowth` draft + `#vfigos` review | `content_candidate` |

אופציונלי לפני טיוטה: `hq/reader-first-he.md` (תחושת קורא).  
אופציונלי מסגרת: `vfmskill` copywriting / copy-editing — החוקה מנצחת.

## פלטים חוקיים

- `content_candidate` — גוף מוכן לסקירה (לא לפרסום אוטומטי).
- `needs_input` — חסר עובדה הכרחית; שאלת אדם; **בלי המצאה**.

## אחרי candidate

`vfcanva` / `vfcovers` → `vfigos` (review / schedule / send via tools per `constitution/SEND.md`).  
אין auto-DM. אין boost בלי ראש צוות. אין Print מ־HQ.
