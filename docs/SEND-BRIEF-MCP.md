# שליחת Brief V6 — תמונות בתוך הכרטיסים

בריף משרד אל `nocturney@gmail.com` בלבד. אין ₪/Insights מומצאים ואין טענה ש־attachment הוא inline.

## עיקרון

Brief V6 דורש תמונות **בתוך** כרטיסי media/research/content. יש שני מסלולים תקינים:

1. **CID אמיתי — מועדף כשיש runner עם Gmail token/ADC**
2. **HTTPS image URL אמיתי בתוך HTML — מועדף דרך Gmail connector**

attachment רגיל הוא fallback תצוגה בלבד ואינו נחשב עמידה בדרישת inline.

## A · Runner CLI — CID `multipart/related`

מודול: `packages/vfops/gmail_brief_send.py`.

```bash
PYTHONPATH=packages python -m vfops.gmail_brief_send \
  --html PATH \
  --images DIR \
  --to nocturney@gmail.com \
  --subject "Velvet Factory — בריף הבוקר | YYYY-MM-DD"
```

המודול:
- קורא HTML ותמונות מהדיסק.
- בונה MIME `multipart/related`.
- כל filename הופך ל־Content-ID.
- HTML מפנה ל־`cid:<filename>`.
- `Content-Disposition: inline`.
- שולח הודעה אחת ב־Gmail API.

דוגמה:
```html
<a href="https://www.instagram.com/reel/.../">
  <img src="cid:reel-g003.jpg" alt="G003" width="108">
</a>
```
ובתיקיית `--images` חייב להיות `reel-g003.jpg`.

בלי `GOOGLE_TOKEN`/ADC הנתיב יוצא 2 ולא מתחזה להצלחה.

## B · Gmail connector — remote images

ה־Gmail connector הנוכחי מקבל `html_body` ו־`attachment_files`, אך אינו חושף flag של `inline`/`Content-ID` למצורף. לכן אין להשתמש במצורף רגיל כדי לטעון שהתמונה יושבת בכרטיס.

דרך connector משתמשים ב־HTTPS URL אמיתי בתוך `<img>`:

```html
<a href="SOURCE_OR_PERMALINK">
  <img src="REAL_HTTPS_THUMBNAIL" alt="..." width="108"
       style="display:block;border:0;border-radius:10px;width:108px;max-width:100%;height:auto">
</a>
```

מקורות מותרים:
- Instagram `thumbnail_url`/`media_url` שהוחזרו בזמן אמת מ־VelvetOS Instagram.
- hero/OG/preview image ציבורי מאותו מקור מחקר.
- asset ציבורי קנוני אחר רק אם הוא באמת שייך לפריט/מקור.

לא משתמשים ב־stock art לא קשור ולא ב־URL פרטי שסביר ש־Gmail image proxy לא יוכל לקרוא.

## Drive פרטי

ל־Drive asset פרטי:
- אם runner יכול להוריד את הקובץ → CID דרך מסלול A.
- אם אין CID → כרטיס מציג `preview unavailable` + קישור Drive אמיתי. אפשר לצרף את הקובץ בנוסף, אבל לא לקרוא לו inline.
- אסור להפוך מדיה פרטית לציבורית רק כדי להציג thumbnail במייל.

## Research preview card

כל finding שמופיע בבריף כולל:
- `source_title`
- `source_domain`
- `source_date`
- `source_url`
- `thumbnail_url` אם נמצא preview אמין מאותו מקור
- finding קצר
- `מה עושים עם זה`

התמונה והכפתור `למקור ↗` שניהם לחיצים לאותו source URL.

## Instagram preview card

הבריף מבצע live probe ומציג:
- thumbnail אמיתי
- permalink
- media type
- timestamp
- reach/views/interactions/saves/shares רק אם Meta החזירה אותם

## Mobile / email safety

- HTML table-based + inline CSS.
- `alt` לכל `<img>`; המסר חייב להישאר מובן גם כשהתמונות חסומות.
- width/height או width מפורש לתמונות כדי למנוע מתיחה בלקוחות מייל.
- CTA/קישורים גדולים ונוחים למגע.
- אין מידע קריטי שנמצא רק בתוך תמונה.

## אסור

- `LOAD_FROM_FILE` בתוך גוף המייל.
- base64 data-URI בתוך `<img>` כתחליף ל־CID.
- attachment + טענה שהוא inline.
- URL זמני/לא קשור בלי fallback טקסט.
- פרסום/DM/boost כתוצאה משליחת הבריף.
