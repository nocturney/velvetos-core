# מייל בריף · Brief V6 App Dashboard

המשך ישיר ל־`תצוגה 3` (תאימות CI/renderer), אבל מבנה המידע משתנה לפי החלטת בעלים 10.9.2026: הבריף הוא **מסך שליטה ניהולי**, לא מסמך 01–07 ולא פתק טקסט.

## מטרה

תוך 20–30 שניות כריסטיאן צריך לדעת:
1. האם צריך ממנו משהו עכשיו.
2. איפה הכסף/ההזמנות/הייצור תקועים.
3. מה קורה היום.
4. מה מצב העמוד והתוכן לפי Insights חיים.
5. מה החוקרים מצאו ומה עושים עם זה.
6. האם יש תקלה מערכתית אמיתית.

## סדר הופעה — נעול לפי ערך ניהולי

| עדיפות | אזור | כלל |
|---:|---|---|
| 0 | Hero | זמן רענון + GREEN/YELLOW/RED + שורה תחתונה אחת |
| 1 | **צריך ממך** | מופיע מיד אחרי Hero אם יש החלטה/אישור/חסם בעלים; לא נקבר בתחתית |
| 2 | כסף + דחוף | גבייה מאומתת, due/overdue, עבודות פעילות/בהדפסה/חסומות |
| 3 | היום | timeline אחד: ייצור, איסופים, תוכן, Calendar, followups |
| 4 | הזמנות וייצור | 3–6 עבודות לפי דחיפות/הכנסה/חסם |
| 5 | Instagram Insights | נתוני account + media חיים; thumbnails וקישור לפוסט |
| 6 | תוכן על המסך | candidate/scheduled/verified-live + תמונה אמיתית בתוך הכרטיס |
| 7 | מחקר ורעיונות | עד 3 findings, כל אחד thumbnail + מקור + תאריך + link + `מה עושים עם זה` |
| 8 | מה השתנה | עד 4 שינויים משמעותיים מאז אתמול |
| 9 | בריאות מערכת | footer קטן; פרטים טכניים רק כשיש degradation |

אם `צריך ממך` ריק — מציגים שורת GREEN קטנה בלבד. לא ממציאים משימה.

## תמונות בתוך הכרטיסים

תמונה היא חלק מהכרטיס, לא attachment דקורטיבי.

מסלול מועדף:
- `packages/vfops/gmail_brief_send.py` → MIME `multipart/related` → `cid:<filename>`.
- `filename` של קובץ התמונה חייב להיות זהה ל־Content-ID שה־HTML מפנה אליו.

מסלול connector/live:
- Instagram: `thumbnail_url` / `media_url` שהוחזרו מ־VelvetOS Instagram, בתוך `<img>` ובתוך `<a href="permalink">`.
- מקור מחקר ציבורי: thumbnail/hero/OG אמיתי של אותו מקור, clickable ל־source URL.
- Drive פרטי בלבד: CID כשהקובץ ניתן לחומרה/הורדה. אם לא — preview link מסומן; **לא** מציגים attachment כאילו הוא inline.

לכל תמונה: `alt`, caption קצר, וקישור כשיש יעד אמיתי.

## Instagram · מצב העמוד

הבריף חייב לבצע probe חי דרך VelvetOS Instagram בכל בוקר:
- `account_info` / profile: followers/media count.
- `get_account_insights`: reach/profile views/total interactions לפי מה ש־Graph מחזיר בפועל.
- `list_media` + `get_media_insights` ל־2–3 פריטים מייצגים/אחרונים: reach/views/interactions/saved/shares כשזמין.

אין `אין ספירה` אם ה־connector כן מחזיר נתון חי. אין השלמה או inference למדד שלא הוחזר.

כרטיס media כולל thumbnail אמיתי, סוג (Reel/Carousel/Post), זמן, נתוני lifetime/period עם תווית ברורה וקישור ישיר ל־Instagram.

## Research cards

Research = GREEN רק עם `packages/vfresearch/sources/<YYYY-MM-DD>-orchestra.md` של אותו יום שמוכיח body run אמיתי.

כל אחד מעד 3 הכרטיסים:
- thumbnail אמיתי מאותו מקור (או source-logo fallback).
- source/domain.
- תאריך מקור.
- כותרת אמיתית.
- משפט ממצא אחד.
- `מה עושים עם זה` — משפט אחד.
- `למקור ↗` direct URL.

אסור למחזר artifact ישן כאילו הוא היום. stale = YELLOW + fallback מסומן.

## שפה ויזואלית

- RTL מלא.
- מעטפת navy כהה; cards קרם/לבן; gold רק להיררכיה/פעולה.
- state pills: green/yellow/red ברורים גם בטקסט, לא רק בצבע.
- mobile-first; זרימה אנכית. KPI יכול להיות grid קצר כל עוד קריא בטלפון.
- body 12–16px; כפתורים/קישורים tappable; thumbnails בערך 80–120px בכרטיסי media/research.
- מידע חשוב גלוי ללא hover.
- dark-mode resilient; אין טקסט קריטי כתמונה.
- מייל לא ארוך ללא צורך: פרטים עמוקים עוברים לקישור המקור/Instagram/GitHub.

## מקור השראה / מחקר פורמט · 10.9.2026

החלטות העיצוב נשענות על:
- Litmus inverted-pyramid email: כותרת רחבה שמכוונת לפעולה החשובה.
- Mailchimp mobile email guidance: single-column/stacking, קריאות ו־tap targets גדולים.
- RGE Studio: mobile stacking, dark-mode preview, grid/padding עקבי.

היישום אצלנו: **owner action → money/urgency → today/operations → Insights/content → research → system health**.

## שליחה

Production renderer: `packages/vfbriefux/render_mail.py` + `MAIL.html`.

CID production path:
```bash
PYTHONPATH=packages python3 -m vfops.gmail_brief_send \
  --html PATH --images DIR --to nocturney@gmail.com --subject TEXT
```

חוזה Gmail/MCP: `docs/SEND-BRIEF-MCP.md`. אם נתיב השליחה אינו מסוגל CID, מותר להשתמש בתמונת HTTPS אמיתית בתוך HTML; אין לשלוח attachment ולדווח שהוא inline.

אין המצאת ₪, Insights, סטטוס פרסום, לקוח או השלמת ייצור. `scheduled/uploaded != verified live`.
