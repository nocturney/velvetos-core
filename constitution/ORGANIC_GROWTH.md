# Organic Growth Control Plane

מושב: **צמיחה** על פקים קיימים (`vfgrowth` · `vfprod` · `vfcopy` · `vfcanva` · `vfbriefux` · `vfinsights` · `vfsales` · `vfops`).  
לא פק חדש. לא בוט אינסטגרם. לא runtime שני.

VelvetOS Core מייצר **תוכן, ניסויים, מדידה והמלצות**.  
בריף 07:00 מביא לראש הצוות חבילת **מאושרת־מוכנה** — לא פרסום חי.

## עיקרון

| שלב | Core עושה אוטונומית | נשאר אנושי |
|---|---|---|
| לכידת מדיה | קורא `print.done` אמיתי, בודק איכות, מסווג | צילום חריג / השלמת וידאו |
| יצירת תוכן | טיוטת Reel / Story / כיתוב / האשטגים / תעודה | אישור, עריכה, שינוי מסר |
| פרסום | קובץ / קישור / מסך העתקה + שעה מהלוח הקבוע | העלאה ל־`@velvets_cloud` |
| קהילה | מציע סקר → Work Order `pending_ops` | פרסום הסקר + אישור ביצוע מבחן |
| המרה | ייחוס **הסתברותי** לחשיפה↔פניית וואטסאפ | מענה, תמחור, סגירה |

אירוע רצפה = `print.done` (לא ניחוש מ־G-code). כינוי בטיוטות: `print_completed`.

## שער מצבים

```
draft
  → quality_checked
  → policy_checked
  → pending_human_approval
  → approved_for_manual_posting
  → posted_manually
  → performance_imported
  → attributed
  → learned
```

- **אישור** משנה רק ל־`approved_for_manual_posting`. לא מפרסם.
- Core **לא** מעביר `pending_human_approval` → `posted_manually`. רק אדם מסמן אחרי העלאה ב־instagram.com.
- בלי מדיה איכותית: אין Reel מומצא. בבריף: «אין Reel איכותי אוטומטי… נדרשים 15 שניות צילום ידני».
- לוח קבוע ב־`vfgrowth/CALENDAR.md` מנצח: ריל א׳/ג׳ 16:00 · סטוריז א׳–ה׳ 20:30 · אין פיד ו׳–ש׳ · **אין ריל כל יום עבודה**.

## מותר

- קליטת סטטוס הדפסה ומדיה אחרי `print.done`.
- טיוטות Reels / Stories / Covers / כיתובי `vfcopy`.
- כרטיס הנדסי + סט האשטגים (`hashtag_set_id`) + 1–2 גיאוטגים.
- ניתוח Insights **מיובאים** (סנאפשוט / CSV). חסר = «אין ספירה».
- סקרי קהילה כטיוטה; Work Order פנימי `pending_ops`.
- משימות רצפה למפעיל; בריף 07:00 עם [אישור] [עריכה] [דחייה].
- סימון `approved_for_manual_posting`.

## אסור

- פרסום אוטומטי באינסטגרם (ה־Control Plane לא קורא Publish API).
- DM / תגובה / Follow / Like / unfollow אוטומטיים.
- רכישת עוקבים, מעורבות או חשיפה.
- מודעות, Boost, קמפיין ממומן בלי ראש צוות.
- תיוג משתמשים בלי opt-in + אישור אדם.
- הצעת מחיר או תשובת וואטסאפ אוטומטית ללקוח.
- הצגת ייחוס הסתברותי כאמת מוחלטת.
- פרסום תצלום לקוח / שם / CAD / מידע עסקי בלי אישור.
- סקר→Print מ־HQ. Work Order ≠ הדפסה.
- המצאת ₪ / Insights / סצנת רצפה / חוזק/חום בלי מקור.

## CTA

וואטסאפ `050-2517000` / איסוף שדרות. לא «שלחו DM».  
קוד מקור אופציונלי שהאדם כותב כשהוא פונה: `REEL` / `STORY` / `MATERIAL` / `B2B` — לא הודעת בוט.

## מדידה

שלוש רמות ב־`vfinsights/ATTRIBUTION.md` + `vfsales/ORDERS.md`.  
`estimated_value_ils` / `closed_value_ils` נשארים `null` עד אימות אדם.  
ציון תוכן — רק ממספרים מיובאים; אחרת «אין ספירה».

## CLI

```
python3 scripts/vf_organic_growth.py brief [--write]
python3 scripts/vf_organic_growth.py policy
python3 scripts/vf_organic_growth.py queue
python3 scripts/vf_organic_growth.py score
```

בריף 07:00: `vfops_loop.py brief` מושך את ה־Decision Pack. שליחת המייל — `SEND.md` (Gmail). הבריף **לא** מפרסם IG.

## פקים

| שכבה | פק | קובץ |
|---|---|---|
| מדיניות | constitution | זה |
| מפעל תוכן | vfgrowth | `ORGANIC-GROWTH.md` · `GATE.md` · `HASHTAGS.md` · `COMMUNITY.md` |
| רצפה | vfprod | `PRINT-DONE.md` · `CLAIMS.md` |
| כיתוב | vfcopy | `hq/templates/organic-reel.md` |
| בריף | vfbriefux | `hq/GROWTH-BRIEF.md` |
| ייחוס | vfinsights + vfsales | `ATTRIBUTION.md` · `ORDERS.md` |

סנסור: `scripts/check-organic-growth.py`.
