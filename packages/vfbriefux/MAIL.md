# מייל בריף · V10.3 · Ink & Candy · Hybrid Responsive

V10.3 שומר על ה־V10.2 image-first וה־RTL, אבל הופך את המייל ל־**hybrid responsive אמיתי**: מובייל נשאר צפוף ונוח, ובדסקטופ — במיוחד Outlook for Windows — הבריף מקבל canvas רחב יותר, טיפוגרפיה גדולה יותר ופריסת side-by-side יציבה.

## המטרה

תוך 20–30 שניות צריך להיות ברור:
1. האם צריך ממני משהו עכשיו.
2. מה השתנה מאז הבריף הקודם.
3. מה קורה בעבודות, כסף וייצור.
4. מה כבר היה אמור לקרות היום.
5. מה קרה בפועל ב־Instagram ובתוכן.
6. מה המחקר מצא ומה עושים עם זה.
7. מה VelvetOS ביצעה בפועל.
8. האם יש תקלה מערכתית אמיתית.

## Responsive / Outlook contract

- Desktop canvas: `780px`.
- Mobile breakpoint: `680px` ומטה → `width:100%` וערימת KPI/cards/split cells.
- Classic Outlook מקבל MSO conditional wrapper ברוחב 780px כדי לא להישען על `max-width` בלבד.
- טיפוגרפיה תפעולית לא אמורה לרדת מתחת לכ־11–12px; body סביב 14–15px; כותרות 20px+.
- `mso-line-height-rule:exactly` משמש בבלוקים קריטיים כדי לצמצם עיוותי line-height ב־Outlook Windows.
- תמונות מקבלות גם width מפורש וגם `width:100%;max-width:...` כדי לעבוד גם ב־Word rendering וגם בלקוחות מודרניים.
- בדסקטופ split cards נשארים side-by-side; במובייל הם נערמים.
- Mobile Gmail/iOS נשאר source-of-truth לחוויה הצרה; Outlook desktop מקבל layout רחב ולא scaling של גרסת מובייל.

## עברית תחילה

עברית היא שפת ברירת המחדל. אנגלית נשארת רק למונחים טבעיים: `Instagram`, `Reel`, `Canva`, `Insights`, `VelvetOS`, `V10.3`.

כותרות ברירת מחדל:
- `תמונת היום`
- `תמונת מצב עכשיו`
- `מה השתנה מאז הבריף הקודם`
- `צריך ממך`
- `מצב הכסף`
- `עבודות חיות`
- `היום / בהמשך`
- `מצב העמוד`
- `רדאר תוכן`
- `שולחן המחקר`
- `הזדמנות קרובה`
- `פעילות VelvetOS`

## סדר מידע

1. Hero: תאריך, מצב העסק, בריאות מערכת.
2. `hero_visual` / תמונת היום — רק אם יש asset אמיתי.
3. עד 4 KPI מאומתים.
4. תמונת מצב במשפט אחד.
5. עד 4 דלתאות משמעותיות.
6. צריך ממך — אם יש.
7. כסף / עבודות / היום.
8. Instagram + רדאר תוכן עם visual proof.
9. מחקר — עד 3 findings עם תמונה מאותו source כשזמינה.
10. הזדמנות קרובה — רק אות אמיתי.
11. פעילות VelvetOS — receipts ושינויים שבוצעו בפועל.

## תמונות והוכחה ויזואלית

תמונה אינה קישוט. היא evidence של אותו פריט.

מקורות עדיפות:
1. studio / WIP / finished asset אמיתי.
2. Instagram `thumbnail_url` / `media_url` חי.
3. Canva thumbnail אמיתי.
4. Drive/Media Vault דרך CID.
5. source image אמיתי של finding מחקרי.

אין stock/filler. אם אין תמונה אמיתית — הכרטיס נשאר טקסטואלי או לא מופיע.

### `hero_visual`

```json
{
  "hero_visual": {
    "cid": "photo.jpg",
    "href": "https://...",
    "eyebrow": "תמונת היום",
    "title": "העבודה המרכזית",
    "caption": "מה חשוב לראות"
  }
}
```

אפשר `url`/`src` במקום `cid`. אם אין `hero_visual` מפורש, ה־renderer רשאי לקדם תמונה אמיתית קיימת מתוך העבודה/תוכן/Instagram לפי סדר עדיפות. תמונה שקודמה לא משוכפלת בכרטיס המקורי.

### Split card

לעבודות וייצור ניתן להשתמש ב־`layout=split`: בערך 38% תמונה ו־62% טקסט בדסקטופ; במובייל הכול נערם.

### `cards[]`

רדאר תוכן, מחקר והזדמנויות יכולים לקבל עד 3 mini-cards:

```json
{
  "cards": [
    {
      "url": "https://...",
      "href": "https://...",
      "kicker": "מאומת חי",
      "title": "כותרת",
      "text": "הממצא החשוב",
      "action": "מה עושים עכשיו"
    }
  ]
}
```

בדסקטופ שלושה cards יכולים להישאר בשורה; במובייל הם נערמים אוטומטית.

## סטטוסים ודלתא

- `מצב העסק` — החלטה, כסף, חסם או follow-up ניהולי.
- `בריאות מערכת` — Gmail / GitHub / Drive / Instagram / Media Intake / Research / automations.
- `changes[]` מציג רק שינוי אמיתי מאז הריצה הקודמת.
- `slots[].delta` מציג שינוי מקומי בכרטיס.
- `density=compact` מקצר אזור יציב.

## Instagram

כאשר החיבור זמין:
- profile/account info.
- Insights חיים לפי המדדים שהוחזרו בפועל.
- `list_media`.
- `get_media_insights` לפריטים רלוונטיים.

פריט media רצוי שיופיע עם thumbnail וקישור ישיר.

`scheduled/uploaded != verified live`.

אם מועד עבר ואין proof חי — המצב משתנה ל־`דורש אימות`/`התאוששות`.

## שולחן המחקר

עד 3 findings בלבד. כל כרטיס צריך לכלול, כשקיים במקור:
- thumbnail מאותו source.
- source/domain ותאריך.
- כותרת/ממצא.
- רמת ביטחון כשיש בסיס.
- `מה עושים עם זה`.
- link ישיר.

מחקר stale מסומן stale. אין recycling כאילו הוא חדש.

## פעילות VelvetOS

הבלוק מתאר **מה בוצע בפועל**: סנכרון, routing, state repair, media ranking, follow-up, anomaly detection או receipt אחר. בדרך כלל אין צורך בתמונה כאן.

אם לא קרה משהו משמעותי, הכרטיס מתקצר.

## Living Studio

`render_mail.py` רשאי להשלים שדות V10.3 חסרים מתוך `packages/velvetos/living-studio/data/pulse-latest.json` בלבד. זהו projection fallback; הוא אינו מקור אמת חדש ואינו מנצח שדה מפורש ב־brief.

## שליחה

Production renderer:
- `packages/vfbriefux/render_mail.py`
- `packages/vfbriefux/MAIL.html`

CID path:

```bash
PYTHONPATH=packages python3 -m vfops.gmail_brief_send \
  --html PATH --images DIR --to nocturney@gmail.com --subject TEXT
```

במסלול production התמונות צריכות להיכנס כ־CID/multipart-related כשנדרש inline rendering. attachment רגיל אינו inline.

## חוקי אמת

- אין המצאת ₪.
- אין המצאת Insights.
- אין המצאת לקוח/סטטוס ייצור/פרסום.
- `scheduled/uploaded != verified live`.
- `0` אינו תחליף למידע חסר.
- תמונה חייבת לתמוך באותו item/source.
- כל delta חייב להיות ניתן לגיבוי במקור אמת.

עקרונות העיצוב: `hq/DESIGN.md`.
