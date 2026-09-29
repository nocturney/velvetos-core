# Research Seat · 2026-09-30 · orchestra

מושב: Velvet Research Seat PRODUCTION · Asia/Jerusalem  
Cutoff: לפני 07:00 · רזולוציה: `ready_for_brief`  
Path: Cloud Agent launch (bc-a1401752…) + live WebSearch/WebFetch + gh shallow-clone failover prep  
Anti-recycle: לא הועתקו ממצאים מ־PR #405 (28.9), #430 (29.9) או מ־research.md של 27.9 על main.

## שאלה (DAILY.md)

Velvet Factory — סטודיו קטן להדפסות תלת־ממד בשדרות. איסוף בלבד. IG @velvets_cloud. אין משלוח ארצי. אין מחיר מומצא. אין אוטו-DM.

## חיפושים שבוצעו

| # | חיפוש / מקור | תוצאה |
|---|---|---|
| 1 | WebSearch · 3D print QC checklist first article / pre-ship 2026 | GoodPrints FAI + GP3D Asset 04 |
| 2 | WebFetch · GP3D Asset 04 (2026-04-24) | גוף חי — pre-ship QC |
| 3 | WebFetch · GoodPrints first-article (2026-04-13) | גוף חי — mating-part + reapproval |
| 4 | WebFetch · PrintCal quote message templates (2026-05-24) | גוף חי — תבניות הודעה |
| 5 | WebFetch · Versely AI video makers 2026 (2026-05-13) | גוף חי — נלקחו רק דפוסי cadence/אורך; נדחו AI-fake / auto-DM |
| 6 | WebFetch · Prusa LTT/LMG BTS (2024-12-19) | גוף חי — תוכן מתהליך רצפה אמיתי |
| 7 | LinklyAI best-100.csv + trending-7d.csv + linkly.ai/skills | דירוג חי (data commit 2026-09-29) |
| 8 | MakerWorld commercial-license collection + model page | HTML התקבל; רישיון Standard Digital File על מועמד |
| 9 | Printables.com WebFetch/curl | Cloudflare challenge — דולג |
| 10 | `vf_upstream_watch.py check --write` | 44 pending / 33 newDetection |

## ממצאים (5)

### 1 · רשימת QC לפני שחרור מהספסל (pre-ship)
- **מקור:** [GP3D Asset 04 — Production QC Checklist…](https://www.goodprints3d.com/blogs/3d/gp3d-asset-04-production-qc-checklist-for-3d-print-orders-before-they-leave-your-bench) · 2026-04-24
- **מה למדנו:** לפני אריזה/מסירה — להריץ צ'קליסט מול הגרסה המאושרת: כמות, פיצ'רים קריטיים למידה, גימור, תווית, pack-out. אם משהו לא ברור — hold, לא לשחרר על הנחה. לתעד סוג פגם כדי לתקן upstream.
- **מה עושים ב־VF:** דפוס ב־`vfprod` (PRINT-DONE / QC לפני `ready_for_pickup`); איסוף שדרות — לא משלוח.
- **ביטחון:** גבוה על התהליך; יישום מקומי נדרש. **לא** מועתק מ־#405/#430.

### 2 · תבניות הודעת הצעה קצרות (בלי אוטו-DM)
- **מקור:** [PrintCal — 3D printing quote message templates](https://printcal.co/en/blog/3d-printing-quote-message-templates/) · 2026-05-24
- **מה למדנו:** תבניות קצרות לפי מצב: קובץ חסר / תמונה בלבד / בלי מידות / חלק טכני / הפרדת מידול מהדפסה / דדליין דחוף / אישור scope. לא לתמחר לפני קנה-מידה ושימוש. לא לשלוח בלוק ענק לכל פנייה.
- **מה עושים ב־VF:** `vfconvert`/`vfcopy` — Saved Replies ידניים; CTA ציבורי = הודעת IG ל־@velvets_cloud; **אין** auto-DM.
- **ביטחון:** גבוה לדפוס שיחה; אין ₪.

### 3 · First-article: הוכחת התאמה לחלק מזדווג + טריגרי אישור מחדש
- **מקור:** [GoodPrints — First Article Approval](https://www.goodprints3d.com/blogs/3d/how-to-approve-a-first-article-or-sample-before-a-custom-3d-printing-production-run) · 2026-04-13
- **מה למדנו:** אישור דגימה ≠ «נראה טוב». לבדוק מול חלק מזדווג/מד; לרשום חריגים; להגדיר במפורש מה פותח אישור מחדש (גיאומטריה, חומר, חומרה קריטית, אוריינטציה, גימור, pack-out).
- **מה עושים ב־VF:** `vfprod`/`vfsales` — טופס אישור דגימה קצר + רשימת reapproval. **מובחן** מ־#405 (sample-approved+hold): כאן דגש על mating proof וטריגרים.
- **ביטחון:** גבוה.

### 4 · תוכן ממעגל עבודה אמיתי: לולאת תהליך + ריביל קצר
- **מקורות:** [Versely maker video playbook](https://www.versely.studio/blog/ai-video-for-3d-printing-and-maker-businesses-2026) · 2026-05-13 (דפוסי אורך/מבנה בלבד); [Prusa — LTT/LMG behind the scenes](https://blog.prusa3d.com/behind-the-scenes-3d-printing-at-ltt-and-lmg_107549/) · 2024-12-19
- **מה למדנו:** לולאת תהליך 15–25ש׳ + ריביל 12–18ש׳; מבנה brief→תהליך→הקשר שימוש. תוכן אמין נבנה מצילום רצפה אמיתי (לא מסך סלייסר כגיבור). **נדחה מ־Versely:** AI-fake timelapse כברירת מחדל, pitch-reel אוטומטי ב־DM, משלוח/Etsy funnel ארצי.
- **מה עושים ב־VF:** `vfgrowth`/`vfom`/`vfcopy` — קליפים מעבודות אמיתיות; CTA = הודעת IG.
- **ביטחון:** בינוני-גבוה על cadence; נמוך על טענות המרה של ספק AI.

### 5 · MakerWorld יום ד׳ — רישיונות UNPROVEN / Printables חומה
- ראו `2026-09-30-makerworld-scan.md`. אין שם להציע למדף. Commercial License Membership = מחקר בלבד, לא SKU.

## Best Skills
ראו `2026-09-30-best-skills.md`. due (~72ש מ־lastPass 2026-09-27 על main). `lastResult=no-embed-existing-coverage`.

## Upstream
- `upstream-watch-latest.json`: pendingUpdates=44, newDetections=33 (checkedAt 2026-09-29T23:08:25Z).
- `upstream-review-latest.json`: wait=10 / review=5 / ignore=29 / update=0; כל ה־pending עם reviewedRemoteHead/Release תואמים.
- מייל עדכוני כלים: יירוץ `vf_upstream_email.py render --arm --consume-notify` (יש newDetection).

## מגבלות
- אין ₪ / Insights / לקוחות מומצאים.
- PR #405/#430 נשארים פתוחים — לא מוזגו (CI אדום / standing rule).
- Cloud Agent הושק; failover מוכן על gh clone.

## מה דולג
- Printables (Cloudflare challenge).
- העתקת ממצאי 27–29.9.
- אימוץ/ack upstream בלי smoke.
- מייל מחקר לבעלים (ברירת מחדל NO).
