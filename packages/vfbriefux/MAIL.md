# מייל בריף · תצוגה 3 vfops

לא מחליפים מבנה. זה החוזה שננעל אחרי תצוגה → תצוגה 2 → תצוגה 3 (30.8.2026).

מקור חי: `תצוגה 3 vfops — לא בריף 07:00` · thread `1a052a15806aedad` · message `1a052a334330df0c`.

## תגובות שננעלו (29.8–30.8)

אין תשובת בעלים על thread תצוגה 3 (הודעה אחת בלבד, 30.8 12:27 UTC).  
סוכני המקור `bc-93fbfca6` / `bc-9e0be231` לא נגישים מכאן.  
התגובות הן האיטרציה עצמה — לא מחליפים אחרי זה:

| מייל | מה ננעל |
|---|---|
| `[ניסיון עיצוב]` 29.8 | כהה, זהב, ושקט. כריכות יושבות בתוך המייל |
| `[ניסיון כריכות]` 29.8 | כריכות למטה / בפנים / משובצות — לא קישור |
| `תצוגה vfops` 30.8 12:06 | RTL + טבלאות. לא בריף 07:00 |
| `תצוגה 2 vfops` 30.8 12:14 | `bgcolor` + סדר החלטה→כסף→הדפסה. `cid` אם ג׳ימייל מציג |
| `תצוגה 3 vfops` 30.8 12:27 · `1a052a334330df0c` | 01–07 מלא. חריץ 05: RTL, bgcolor, טבלאות, אגודל+קישור. חריץ 07: «בבריף 07:00 הן יושבות בגוף המייל אחרי הדבקה בג׳ימייל — לא כקישור». מצורפים G001/G002/G005.jpg |

## למה המייל יצא טקסט

פיילאובר 31.8 שלח `body` / `<br/>` מ־`MAIL-PACK.md`.  
תצוגה 3 היא **HTML טבלאות** (`htmlBody`) + כריכות בגוף. לא טקסט.

## חוזה ויזואלי (לא זז)

| שדה | ערך |
|---|---|
| RTL | `dir="rtl"` על מעטפת, כרטיס, תאים, פסקאות |
| רקע חיצוני | `bgcolor="#0b1224"` |
| כרטיס | 640px · `bgcolor="#f7f3eb"` |
| כותרת | `bgcolor="#101a35"` · פס זהב `border-right:6px solid #caa96b` |
| תוויות | Georgia · `#caa96b` |
| גוף | Arial · `#1b2438` |
| טבלאות | כותרת כהה/זהב · זברה `#fffdf8` / `#f7f3eb` |
| סדר | 01–07 לפי `vfops/BRIEF.md` |
| כריכות | `cid:` בגוף בחריץ 07. לא קישור. מצורף רגיל רק כגיבוי תצוגה |

## שליחה (פיילאובר Grok)

1. ממלאים JSON בלי ₪ מומצא. אין ספירה אם אין מקור.
2. `python3 packages/vfbriefux/render_mail.py packages/vfops/hq/brief-YYYY-MM-DD.json -o /tmp/brief.html`
3. Gmail `send_message` אל `nocturney@gmail.com`:
   - `htmlBody` = הקובץ שנוצר
   - `body` = טקסט חלופי קצר
   - כריכות: `attachments` עם `inline: true` ו־`filename` = ה־cid (למשל `G005.jpg`)
4. אין `reply` / `forward` / שליחה ללקוח.

תבנית: `MAIL.html`. ממלא: `render_mail.py`. בדיקה: `python3 packages/vfbriefux/render_mail.py --check`.  
דיאגרמת לוויין (לא `htmlBody`): `python3 packages/vfbriefux/render_mail.py --diagram pipeline|slots -o …` · מפה: `hq/DIAGRAM-MAKER.md`.
