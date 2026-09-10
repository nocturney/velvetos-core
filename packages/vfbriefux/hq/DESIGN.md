---
name: Velvet Factory Brief V10
version: "10.0"
tokens:
  color:
    canvas: "#080a14"
    surface-dark: "#11142a"
    surface-soft: "#f6f5fb"
    violet: "#7c5cff"
    cyan: "#20d9ff"
    pink: "#ff5fa2"
    coral: "#ff8a65"
    lime: "#a3e635"
    yellow: "#f5c451"
    text-dark: "#161a2d"
    text-muted: "#697386"
    white: "#ffffff"
  typography:
    display: "Arial, sans-serif"
    body: "Arial, sans-serif"
    label-size: "10px"
    body-size: "14px"
    title-size: "31px"
    bottom-line-size: "17px"
  spacing:
    outer: "18px 8px 34px"
    card-padding: "17px 20px"
    section-gap: "12px"
    accent-border: "4px"
  layout:
    max-width: "680px"
    direction: rtl
---

# Velvet Factory — Brief V10 Visual Identity

## עיקרון

הבריף הוא **מסך שליטה יומי שחי בתוך המייל**, לא memo ולא dashboard גנרי. הוא צריך להרגיש כמו מוצר מודרני של VelvetOS: חד, צבעוני, עשיר אך לא צעקני, וניתן לסריקה בטלפון תוך 20–30 שניות.

שפת ברירת המחדל היא **עברית**. אנגלית מותרת רק כמיקרו־לייבל קצר כאשר היא באמת מוסיפה אופי או מוכרת מונח מערכת; אין כותרות שלמות באנגלית כאשר יש ניסוח עברי טבעי.

## שפה חזותית

V10 מחליף את נעילת navy/gold הישנה בשפה רחבה יותר:

| צבע | שימוש |
|---|---|
| `#080a14` | קנבס חיצוני כהה מאוד |
| `#11142a` | מעטפת/hero כהה |
| `#7c5cff` | מערכת, משרד, VelvetOS, version |
| `#20d9ff` | מידע חי, Insights, תמונת מצב |
| `#ff5fa2` | צריך ממך / החלטה / תשומת לב |
| `#ff8a65` | ייצור והדפסה |
| `#a3e635` | כסף שהושלם/תקין/חיובי |
| `#f5c451` | הזדמנות/פרנסה/מעקב |
| `#f6f5fb` | משטח תוכן בהיר |

הצבעים הם **סמנטיים**, לא קישוט: אותו סוג מידע מקבל אותה משפחת צבעים לאורך הבריף. מותר gradient עדין ב־Hero בלבד; גוף המייל נשאר Gmail-safe ופשוט.

## היררכיה

1. Hero — תאריך, גרסה, מצב עסק, בריאות מערכת.
2. KPI — עד ארבעה נתונים בלבד, מאומתים.
3. **תמונת מצב עכשיו** — משפט אחד.
4. **מה השתנה מאז הבריף הקודם** — עד ארבעה delta משמעותיים.
5. צריך ממך — אם קיים, גבוה בדף.
6. כסף / ייצור / היום / הזמנות.
7. Instagram + תוכן חי עם thumbnails.
8. מחקר — רק findings עם פעולה מומלצת.
9. VelvetOS Activity — מה בוצע בפועל, לא רשימת שירותים כללית.
10. בריאות מערכת מפורטת רק כשיש degradation.

## צפיפות אדפטיבית

- בלוק שלא השתנה ובלי חריגה: `density=compact` או שורה קצרה.
- בלוק עם שינוי: מקבל `delta` מודגש.
- חריגה/חסם: עולה מוקדם יותר בתוך הנתונים שהקומפוזר מספק.
- אין להאריך את המייל רק כדי לשמר שבעה אזורים באותו גובה.
- אין להמציא שינוי כדי להצדיק צבע או badge.

## תמונות

תמונה היא **הוכחה ויזואלית**, לא filler.

מקורות נתמכים:
1. `cid:<filename>` לנכס פרטי/מקומי דרך Gmail sender.
2. `url`/`src` אמיתי שהוחזר מ־Instagram/Canva/public source.
3. `href` אופציונלי הופך את התמונה ללחיצה ישירה ליעד האמיתי.

לכל תמונה: `alt`, caption קצר, וקישור כשהוא קיים. אין stock images ואין תמונה לא קשורה רק כדי “להחיות” בלוק.

## עברית תחילה

מומלץ:
- `תמונת מצב עכשיו` במקום `NOW READ`
- `מה השתנה מאז הבריף הקודם` במקום `WHAT CHANGED`
- `צריך ממך` במקום `OWNER ACTION`
- `מצב הכסף` במקום `CASH STATE`
- `רדאר תוכן` במקום `CONTENT RADAR`
- `שולחן המחקר` במקום `RESEARCH DESK`
- `היום / בהמשך` במקום `TODAY / NEXT`
- `פעילות VelvetOS` במקום `VELVETOS ACTIVITY`

מותר להשאיר `V10`, `Instagram`, `VelvetOS`, `Reel`, `Canva`, `Insights` וכדומה כשהמונח עצמו טבעי יותר כך.

## סטטוסים

Hero מציג שני צירים נפרדים:

- `מצב העסק` — GREEN/YELLOW/RED מבחינת תשומת לב ניהולית.
- `בריאות מערכת` — תשתיות בלבד.

במייל עצמו הטקסט העברי קודם לצבע. צבע לעולם אינו הסימן היחיד למצב.

## כללי אמת

- אין ₪ מומצא.
- אין Insights מומצאים.
- scheduled/uploaded ≠ verified live.
- אין `0` במקום מידע חסר; משתמשים ב־`אין ספירה`/`לא זמין` לפי ההקשר.
- thumbnail של מקור מחקרי צריך להיות מאותו מקור; אם אין, משתמשים ב־logo fallback או בלי תמונה.
- פעילות VelvetOS מתארת receipt/שינוי שבאמת קרה מאז הריצה הקודמת.

## Gmail / mobile

- RTL בכל טבלאות התצוגה.
- 320–680px, mobile-first.
- מבנה table-based; CSS פשוט ו-inline ככל האפשר.
- כפתורים touch-friendly.
- dark-mode resilient.
- מידע קריטי לעולם לא כתמונה בלבד.

## תאימות לאחור

`render_mail.py` ממשיך לקבל JSON ישן של 01–07. שדות V10 חדשים הם אופציונליים:

- `attention`
- `system_health`
- `kpis[]`
- `changes[]`
- `slots[].kind`
- `slots[].density`
- `slots[].delta`
- `covers[].cid` או `covers[].url/src`
- `covers[].href`

כך אפשר לעבור ל־V10 בהדרגה בלי לשבור את לולאת הבריף הקיימת.

## Related files

| File | Role |
|---|---|
| `../MAIL.html` | מעטפת V10 החיה |
| `../render_mail.py` | renderer בעברית־תחילה + V10 fields |
| `../MAIL.md` | חוזה תוכן/מקורות/שליחה |
| `packages/vfops/hq/BRIEF-SLOTS.md` | מקורות המידע הקנוניים |
| `packages/vfmedia/catalog.json` | מדיה אמיתית |
| `packages/velvetos/living-studio/` | Studio Pulse / Living Studio inputs |