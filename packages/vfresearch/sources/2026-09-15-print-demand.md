# Print-Demand · 2026-09-15

מושב: מחקר · Asia/Jerusalem
מדף חומרים: `packages/vfprod/MATERIAL.md` קיים, אבל אין בו ספירת יתרה עדכנית ל־PLA/PETG; לכן אין אישור הדפסה מתוך המחקר.

## ויזואל 3D

| אות | מקור | התאמה לרצפה | פעולה |
|---|---|---|---|
| kinetic / fidget חד־חלקי | https://www.printables.com/model/1699407-fidget-spiral · updated 2026-09-06 | no supports, PLA, 0.2mm, clearance של 0.900mm; תנועה נותנת reveal ברור בווידאו | מועמד ל־slice + test print אחד אחרי אישור חומר ברצפה |
| organizer מסתובב | https://www.printables.com/model/1822290-rolldesk-360-360deg-rotating-desk-school-makeup-or · updated 2026-09-05 | support-free אבל כולל base, disc, 6 rollers וגוף; יותר חלקים/הרכבה | benchmark בלבד לפני SKU ראשון |
| pencil case מכני | https://www.printables.com/model/1833983-customizable-desktop-pencil-case · updated 2026-09-06 | 12+ חלקים, linkage, support לחלק אחד ואפשרות לדבק | לא first-test למרות appeal ויזואלי |

**כלל triage מחקרי של הבעלים:** רישיון של יוצר זר אינו מסנן מועמד. יוצר/מותג ישראלי עובר `vlicense`/stop. אין כאן אישור משפטי או Print command.

## Demand IL

החיפוש הציבורי לא הוכיח ביקוש מקומי בשדרות למוצר מדף מסוים. כן נמצא pattern עקבי באופן שבו ספקי 3D ישראליים פותחים פנייה: קובץ מוכן מול תמונה/רעיון/צורך במידול.
| מקור ציבורי | מה הופיע | חוזק האות |
|---|---|---|
| https://www.play3d.co.il/ · observed 2026-09-15 | FDM + custom design למי שאין STL + batch orders | בינוני · positioning של ספק, לא conversion data |
| https://sunny3d.co.il/ · observed 2026-09-15 | מוצר מוכן / תמונה / רעיון; אפשר לשלוח קובץ, תמונה או תיאור | בינוני |
| https://nsf3d.co.il/ · observed 2026-09-15 | "עיצוב מאפס או מקובץ"; תיאור/תמונה/רעיון או STL/STEP | בינוני |
| https://www.3dfactory.co.il/ · observed 2026-09-15 | העלאת קובץ בולטת בכניסה | בינוני |
| https://adi3d.co.il/ · observed 2026-09-15 | קובץ קיים או דרישה טכנית + שירות מידול כשצריך | בינוני |

**פעולה:** הוטמע ב־`vfconvert/hq/PLAYBOOK.md` split ראשון: `יש קובץ` / `יש תמונה או רעיון` / `צריך מידול`, ואז שואלים רק שדות חסרים. אין auto-DM ואין claim של uplift עד שנמדוד פניות שלנו.

## סאונד / Social mechanics

מקור שבועי: https://www.heyorca.com/blog/trending-audio-for-reels-tiktok · edition/source date 2026-09-11, checked 2026-09-15.

אות שימושי: current Instagram trend מנרמל "שאלת לקוח שנשמעת טיפשית" כדי להראות שהמותג נגיש ומסביר בלי jargon. ל־Velvet Factory לוקחים **רק את המכניקה**: first beat עם קטגוריית שאלה אמיתית שכבר התקבלה, ואז proof אמיתי מהמודל/ההדפסה/reveal. לא מעתיקים wording, creator, footage או branding; לא ממציאים customer quote. אין שיבוץ בזמן RESET.

Audio availability בפועל לא נבדקה בחשבון ולכן אין שם track לביצוע. אם רעיון כזה יגיע ל־preflight, זמינות audio נבדקת ב־Instagram עצמו לפני publish.

## תיק הפקה (≤3 מועמדים)

| # | רעיון | חומר | מצב |
|---|---|---|---|
| 1 | Fidget Spiral — kinetic desk object | המקור ממליץ PLA; מלאי מקומי לא נספר | `slice/test-only`, לא stock |

## נעול / limitations

- local Sderot demand: `nothing-solid`; אין הפיכת פופולריות Printables ל־Insight שלנו.
- אין הדפסה עד בדיקת חומר, slice מקומי, grams/minutes בפועל ו־test quality.
- own `@velvets_cloud` metrics לא נסרקו ולא הומצאו.
- RESET פעיל: אין שיבוץ תוכן רק בגלל שנמצא mechanic.
