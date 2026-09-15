# Velvet Research Seat · 2026-09-15

**cutoff_state:** `ready_for_brief`
**freshness:** `GREEN body evidence` — same-day public research body actually ran.
**target consumer:** 09:00 Morning Brief.

## Authority / current state

- `vfgrowth/CALENDAR.md`: RESET active; no future content is scheduled just to satisfy cadence.
- `vfsku/SHELF.json`: all 5 repeatable SKU slots are still empty.
- Live `VF HQ · jobs`: no unfinished print queue was found in the current rows; delivered receivables remain open. No customer names are needed in research output.
- `vfprod/MATERIAL.md`: material families are listed but current spool quantities are not counted, so Research Seat cannot authorize a physical test print.
- Best Skills: `standingForever=true`, `lastPass=2026-09-14`; ~48h refresh is **not due** today.
- OpenPost: consumed current local state only; upstream checking remains owned by `OpenPost Release Watch` and was not duplicated.
- HyperFrames: current exact pin remains 0.8.34; no due/release evidence requiring research or upgrade today.
- VoiceStudio: local authority remains exact v0.5.2. Public latest release is still v0.5.2 (2026-09-10); newer 2026-09-14 commits are unreleased, so no upgrade.
- Mac-Office is offline; no new Mac slicer/runtime verification is claimed.

## Same-day external evidence

| מקור | source/publication date | מה נלקח | confidence / limitation |
|---|---|---|---|
| https://www.printables.com/model/1699407-fidget-spiral | updated 2026-09-06; checked 2026-09-15 | kinetic desk/fidget; no supports; PLA; 0.2mm; 0.900mm clearance | high on source facts; local demand unknown |
| https://www.printables.com/model/1822290-rolldesk-360-360deg-rotating-desk-school-makeup-or | updated 2026-09-05; checked 2026-09-15 | support-free but base + disc + 6 rollers + organizer body | high on geometry/assembly facts; no local demand claim |
| https://www.printables.com/model/1833983-customizable-desktop-pencil-case | updated 2026-09-06; checked 2026-09-15 | many parts, linkage, one supported part, possible glue | high on source facts; comparison only |
| https://www.play3d.co.il/ | observed 2026-09-15 | file printing + custom design + batch entry paths | medium; supplier positioning, not conversion data |
| https://sunny3d.co.il/ | observed 2026-09-15 | ready product / photo / idea; send file, photo or description | medium; supplier positioning |
| https://nsf3d.co.il/ | observed 2026-09-15 | design from scratch or file; description/photo/idea/STL/STEP | medium; supplier positioning |
| https://www.3dfactory.co.il/ | observed 2026-09-15 | file upload is a prominent entry action | medium; supplier positioning |
| https://adi3d.co.il/ | observed 2026-09-15 | existing file/technical requirement plus modeling when needed | medium; supplier positioning |
| https://www.heyorca.com/blog/trending-audio-for-reels-tiktok | edition/source date 2026-09-11; checked 2026-09-15 | current mechanic normalizes beginner/client questions to make expertise approachable | medium on transferable mechanic; no own-account performance evidence |
| https://help.heyorca.com/en/articles/16023674-add-trending-audio-to-instagram-and-tiktok-posts | checked 2026-09-15 | IG trending audio is Reel-only in this tool; business availability can rotate | high for HeyOrca/API workflow; we do not use it to publish |
| https://github.com/OthmanAdi/planning-with-files/releases/tag/v3.18.0 | published 2026-09-13 | read-only saved-plan inventory before choosing/resuming plan | high; pattern only, no upstream runtime install |
| https://github.com/debpalash/VoiceStudio/releases/tag/v0.5.2 | published 2026-09-10 | latest stable release remains v0.5.2 | high; upstream main is ahead but unreleased |
| https://github.com/mvanhorn/last30days-skill/releases/tag/v3.24.0 | published 2026-09-09 | X search via official API/Grok connector | high source fact; not needed by current VF stack |

## ממצאים

## Top 3 for the 09:00 brief

### 1. פנייה צריכה להתחיל ב־route, לא בשאלון מלא

**ממצא:** במספר ספקי 3D ישראליים ציבוריים חזרה אותה הבחנה: לקוח עם קובץ מוכן לעומת לקוח שמגיע עם תמונה/רעיון וצריך מידול. זה לא מוכיח uplift, אבל זו התאמה טובה למבנה העבודה הקיים של `vfconvert`.

**מה עשינו:** הוטמע low-risk בתוך `packages/vfconvert/hq/PLAYBOOK.md`: קודם `יש קובץ` / `יש תמונה או רעיון` / `צריך מידול`, ואז שואלים רק את השדות החסרים למסלול. לא הוקם CRM/flow חדש ואין auto-DM.

**ביטחון:** medium-high על pattern השוק; **לא ידוע** אם זה ישפר conversion אצל Velvet Factory עד שנצטברו פניות שלנו להשוואה.

### 2. לניסוי המדף הבא עדיף אובייקט חד־חלקי עם תנועה, לא organizer מרובה חלקים

**ממצא חדש:** Fidget Spiral הוא מועמד טרי מהסריקה: no-support, PLA, 0.2mm ו־0.900mm clearance לפי היוצר. בהשוואה, שני organizers חדשים שנבדקו דורשים 4–12+ חלקים/הרכבה ולעיתים glue/support.

**מה עושים:** מועמד ל־slice + test print **אחד בלבד**, לא stock ולא SKU אוטומטי. לפני Print נדרשים מלאי חומר מאומת, slice מקומי, grams/minutes בפועל, tolerance check ותמונה אמיתית. כרגע `MATERIAL.md` אינו מכיל ספירת גלילים, ולכן המחקר לא שולח Print command.

**ביטחון:** high על printability שהיוצרים מתארים; medium על התאמה תפעולית; **low/unknown** על ביקוש בשדרות.

**כלל בעלים:** רישיון של יוצר זר לא שימש כקריטריון פסילה/דירוג. יוצר/מותג ישראלי נשאר stop/`vlicense` לפני שימוש.
### 3. תוכן: שאלה אמיתית של מתחיל → proof, בלי להעתיק trend

**ממצא:** HeyOrca של השבוע מציג mechanic שבו מותג מנרמל שאלה של לקוח שנשמעת "בסיסית" כדי להפוך expertise לנגיש יותר.

**התאמה ל־Velvet Factory:** כשיש עבודה אמיתית מתאימה, first beat יכול להיות קטגוריית שאלה שכבר התקבלה בפועל (`יש לי רק תמונה`, `יש לי STL — מה חסר?`), ואז עוברים מהר ל־proof מהמודל/ההדפסה/reveal. לא משתמשים בציטוט לקוח מומצא, לא מעתיקים wording/creator/footage/branding, ולא משבצים בזמן RESET. Audio נבדק ב־Instagram עצמו רק אם הקונספט עובר preflight.

**ביטחון:** medium כמכניקת תוכן חיצונית; אין own-account metric שמוכיח retention/engagement אצלנו.

## Social Intelligence

- external reference נשמר כמכניקה בלבד עם URL/date/provenance.
- own `@velvets_cloud` metrics לא נסרקו מה־Web ולא הומצאו; Instagram MCP נשאר authority.
- אין global virality score ואין extrapolation ממספרי יוצרים חיצוניים.
- אין שיבוץ תוכן חדש בזמן RESET.

## Tool / skill maintenance

הסקירה השבועית ב־`LINKS.json` הייתה overdue ולכן בוצעה היום כחלק מאותו Research Seat: 74 רשומות due נבדקו; 26 GitHub sources הראו push חדש מאז 2026-09-08; 6 מקורות Web החזירו 403/429 ונשמרו כ־wall בלי claim על הגוף.

הטמעה אחת בלבד נמצאה מוצדקת: דפוס inventory read-only מ־planning-with-files v3.18.0 הוסף ל־`packages/vfharness/PLANNING-FILES.md`, כדי לא לפתוח state כפול כשמשימה קיימת. VoiceStudio נשאר pinned v0.5.2; last30days v3.24.0 לא הוטמע; agency-agents/codebase-memory updates לא מצדיקים runtime נוסף. פירוט: `packages/vfresearch/sources/2026-09-15-weekly-links.md`.

Best Skills לא due; OpenPost upstream לא נבדק כאן כדי לא להכפיל את ה־Release Watch.

## Deliberate skips / limitations

- Printables/contest activity היא marketplace signal, לא ביקוש מקומי.
- public Israeli competitor pages הן positioning/supply-side evidence, לא conversion benchmark.
- לא בוצע Print: חסרה ספירת חומר מקומית עדכנית, ואין side effect פיזי מתוך Research Seat.
- לא הומצאו prices, Insights, customer quotes או shipping offer.
- Mac-Office offline; לא נטען runtime/slicer verification חדש על Mac.

## Brief payload

`ready_for_brief` — להעביר עד שלושת הממצאים לעיל. Same-day body קיים עם מקורות חיצוניים חיים; אין recycling של 14.9 כאילו הוא fresh.

Freshness: **2026-09-15 · GREEN body evidence**.
