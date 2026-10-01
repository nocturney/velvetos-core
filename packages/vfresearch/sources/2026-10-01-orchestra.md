# Research Seat · Orchestra · 2026-10-01

מושב: צמיחה · Asia/Jerusalem · cutoff 07:00  
תבנית: `packages/vfresearch/DAILY.md` · VF = סטודיו שדרות, איסוף בלבד, IG @velvets_cloud  
סמכות: לא למחזר ממצאי #405/#430/#438 (28–30.9 פתוחים) ו־main 27.9.

## יומן חיפוש

| # | חיפוש / מקור | תוצאה |
|---|---|---|
| 1 | WebSearch · easy-print/easy-sell organizers batch 2026 | Printforge 2026-03-09 + LayerMath snapshot |
| 2 | WebFetch · crm.printforge.com.au/blog/most-profitable-3d-prints-to-sell | גוף חי — קטגוריות פונקציונליות / מה להימנע |
| 3 | WebSearch · inquiry→order conversion pickup Instagram | Homegrown 2026-09-27 + Fenfair 2026-06-01 |
| 4 | WebFetch · fenfair.com custom-order-workflow | גוף חי — 7 שלבים / deposit / scope |
| 5 | WebFetch · findhomegrown.com Instagram DM orders alternative | גוף חי — הזמנה מחוץ ל־DM + pickup |
| 6 | WebSearch · FDM farm efficiency FPY QC 2026 | Sovol 2026-04-28 + Printie 2026-02-11 |
| 7 | WebFetch · sovol3d.com swarm printing small-batch | גוף חי — FPY / פרופילים / batch by constraint |
| 8 | WebFetch · printie.com QC checklist 2026-02-11 | גוף חי — רמות QC + gold photo + weekly review |
| 9 | WebSearch · content from real print batch timelapse | Dirks Instruments LinkedIn 2026-01-06 (אותנטיות רצפה) |
| 10 | WebFetch · estimator.tryar.in | Cloudflare — דולג |
| 11 | LinklyAI best-100 / trending-7d / social-buzz | dataDate 2026-09-30 |
| 12 | MakerWorld scan | **דולג** — יום ה׳ (cadence א׳–ד׳) |
| 13 | `vf_upstream_watch.py check --write` | pendingUpdates=48 · newDetections=37 |

## ממצאים (5)

### 1 · FPY כמדד יחיד + פרופילים מגרסאים + batch לפי אילוץ
- **מקור:** [Sovol — 3D Print Farm Management: Swarm Printing for Small-Batch Production](https://www.sovol3d.com/blogs/news/3d-print-farm-management-swarm-printing-for-small-batch-production) · 2026-04-28
- **מה למדנו:** First-pass yield (עובר QC בניסיון ראשון ÷ סה״כ) הוא המדד שמונע «תפוקה גבוהה = בזבוז מהיר». לנעול baseline profile לכל חומר/נחיר עם שם גרסה; לנתב תורים לפי אילוץ (חומר / סיכון / post-process) ולפזר זמני סיום כדי לא לחסום מיטות.
- **מה עושים ב־VF:** דפוס ב־`vfprod`/`vfops` — שורת FPY פשוטה בלוח ייצור + שמות פרופיל מגרסאים; batch צבע/חומר קיים מתחזק. סטודיו קטן — לא «farm של 200».
- **ביטחון:** גבוה על התהליך; יישום מקומי נדרש. **לא** מועתק מ־#405/#430/#438.

### 2 · מסלול הזמנה מותאמת ב־7 שלבים + deposit לפני ייצור + scope כתוספת בתשלום
- **מקור:** [Fenfair — Custom Order Workflow for Handmade Makers (2026)](https://fenfair.com/blog/pillars/custom-order-workflow) · 2026-06-01
- **מה למדנו:** Inquiry→Qualify→Quote→Deposit→Make→Proof→Ship/Pickup. לא מתחילים חומר/הדפסה לפני deposit. ציטוט פורמלי עם תפוגה + סבב תיקונים אחד; שינוי מחוץ ל־scope = תוספת כתובה. קאדנס תקשורת קצר בזמן ייצור מונע «יש עדכון?».
- **מה עושים ב־VF:** `vfconvert`/`vfsales` — מחזקים שער qualify + hold עד deposit; proof לפני `ready_for_pickup`. **אין** ₪ מומצא; אין auto-DM. CTA ציבורי נשאר הודעת IG ל־@velvets_cloud.
- **ביטחון:** גבוה לדפוס; מחיר/אחוזי deposit — החלטת בעלים בלבד.

### 3 · רמות QC לפי מוצר + תמונת gold-standard + סקירת פגמים שבועית 15ד׳
- **מקור:** [Printie — 3D Printing Quality Control Checklist for Sellers](https://printie.com/blog/2026-02-11-3d-printing-quality-control-checklist) · 2026-02-11
- **מה למדנו:** לא כל מק״ט אותו חומרה: Level 1 קוסמטי / Level 2 +fit / Level 3 +פונקציה. תמונת «זהב» להשוואת drift; בדגימת אצווה — ראשון/אמצע/אחרון על הפלטה. סקירה שבועית קצרה: Top 3 מק״ט לפי פגם + סוג כשל נפוץ.
- **מה עושים ב־VF:** `vfprod` — רמות QC על מק״טים חוזרים + תיקיית reference photo; לוג פגמים קל (לא חייב כלי חדש). **מובחן** מ־#438 pre-ship checklist ומ־FAI של GoodPrints.
- **ביטחון:** גבוה.

### 4 · מק״טים פונקציונליים קצרים להדפסה — החלפות/ארגונים; להימנע מסטנדים גנריים
- **מקור:** [Printforge — Most Profitable 3D Prints to Sell in 2026](https://crm.printforge.com.au/blog/most-profitable-3d-prints-to-sell) · 2026-03-09
- **מה למדנו:** עדיפות לפונקציונלי, קשה להשיג בקופסה, זמן הדפסה קצר: replacement parts, trade organisers, home functional clips/hooks. להימנע מ־phone stands / fidgets / דקור גנרי / הדפסות 24ש+ בלי הצדקה. עיצוב פעם אחת = נכס מק״ט לריפrint.
- **מה עושים ב־VF:** `vfsku` — רשימת מועמדים למדף איסוף מקומי (בדיקת רישיון נפרדת ביום MakerWorld). **אין** העתקת מחירי המקור כ־₪ VF; תמחור רק במסלול המורשה.
- **ביטחון:** בינוני-גבוה על קטגוריות; נמוך על מספרי רווח של ספקים חיצוניים (לא לטעון כ־Insight של @velvets_cloud).

### 5 · הזמנה מחוץ לכאוס DM: לינק/טופס מובנה + תיעוד הזמנות; IG לתוכן
- **מקור:** [Homegrown — Instagram DM Orders Alternative](https://findhomegrown.com/blog/instagram-dm-orders-alternative) · 2026-09-27
- **מה למדנו:** DM טוב ל־&lt;10 לקוחות קבועים ואז נשבר (אין לוג הזמנות, אין מלאי, אין אישור תשלום). דפוס: שכבת שיווק ב־IG + שכבת הזמנה בלינק/טופס עם רשימת הזמנות מרכזית וחלונות איסוף. מעבר הדרגתי (שבועיים מקבילים) ואז הפניה ללינק.
- **מה עושים ב־VF:** `vfconvert`/`vfgrowth` — דפוס טופס/לינק קליטה (כבר בכיוון GRILL/inquiry); **לא** מתקינים Homegrown/OrderPost מ־HQ; **אין** auto-DM; CTA ציבורי נשאר הודעת IG. איסוף שדרות בלבד.
- **ביטחון:** גבוה על כאב ה־DM; בחירת כלי — בעלים.

## Best Skills
ראו `2026-10-01-best-skills.md`. due (~96ש מ־lastPass 2026-09-27). `lastResult=no-embed-existing-coverage`.

## MakerWorld
**דולג** — יום חמישי (cadence א׳–ד׳ לפי `hq/MAKERWORLD-SCAN.md`).

## Upstream
- `upstream-watch-latest.json`: pendingUpdates=48, newDetections=37 (checkedAt 2026-09-30T23:04:57Z).
- `upstream-review-latest.json`: wait=17 / review=10 / ignore=21 / update=0; כל ה־pending עם reviewedRemoteHead/Release תואמים.
- מייל עדכוני כלים: יש newDetection → להריץ `vf_upstream_email.py render --arm --consume-notify`.

## מגבלות
- אין ₪ / Insights / לקוחות מומצאים.
- PR #405/#430/#438 נשארים פתוחים — לא ממוחזרים.
- Cloudflare על tryar.in — דולג.
- אין אימוץ/ack upstream בלי smoke.

## מה דולג
- MakerWorld/Printables scan (לא ביום).
- העתקת ממצאי 27–30.9.
- מייל מחקר לבעלים (ברירת מחדל silent — אין blocker).
- install כלי הזמנות חיצוני / npx skills.
