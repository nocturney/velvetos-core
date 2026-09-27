# Instagram scheduling mirror — Google Calendar

Cloudflare Publisher הוא מקור האמת היחיד לתזמון Instagram. Google Calendar הוא **mirror תפעולי לקריאה**, לא queue ולא מנגנון פרסום.

## יומן קנוני

- בעלים: `nocturney@gmail.com`.
- יומן משני ייעודי: **`אינסטגרם`**.
- timezone: `Asia/Jerusalem`.
- כל job פעיל ב־Publisher חייב להופיע ביומן הזה.
- עריכה ידנית, מחיקה או הזזה ב־Google Calendar **אינן משנות** את ה־Publisher ולעולם אינן נחשבות approval.

## סנכרון

כיוון יחיד: `Cloudflare Publisher D1 -> Google Calendar`.

- `scheduled` / `retry` / `publishing` / `reconcile_required` / `published_verified` / `dead_letter`: upsert של אותו event לפי `job_id`.
- `cancelled`: מחיקת event mirror.
- reschedule אינו PATCH ל־job: מבטלים את ה־job הישן ויוצרים job חדש עם authorization חדש; ה־mirror עוקב בהתאם.
- event start = `scheduled_at`; end = +30 דקות.
- האירוע שקוף (`free`) וללא reminders.
- כותרת: `Instagram · <content_id> · <format> · <status>`.
- תיאור כולל `job_id`, status, permalink אם קיים, והבהרה שמקור האמת הוא Publisher.

## אמינות

כשל Calendar **אינו חוסם פרסום שכבר מתוזמן**. הוא מסומן כ־mirror drift ומדווח ב־Morning Green עד תיקון. אין לשנות תזמון כדי "להתאים" ליומן.

Morning Green קורא את Publisher ישירות; הוא אינו מסתמך על Calendar כדי להחליט אם פוסט מתוזמן.

## רשת התוכן

`CALENDAR.md` נשאר מדיניות המשבצות/קצב. ברגע שנוצר job בפועל, `scheduled_at` ב־Publisher הוא העובדה הקנונית. אין OpenPost/instagram.com queue חדש.
