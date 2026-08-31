# מייל בריף · תצוגה 3 vfops

לא מחליפים מבנה. זה החוזה שננעל אחרי תצוגה → תצוגה 2 → תצוגה 3 (30.8.2026).

מקור חי: `תצוגה 3 vfops — לא בריף 07:00` · thread `1a052a15806aedad` · message `1a052a334330df0c`.

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
