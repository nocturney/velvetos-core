---
name: Velvet Factory Brief V10.2
version: "10.2"
tokens:
  color:
    ink: "#101828"
    ink-surface: "#151D2E"
    pink: "#FF4F91"
    periwinkle: "#6C7CFF"
    lime: "#B8F34A"
    cyan: "#45D7FF"
    coral: "#FF8C66"
    butter: "#FFD45A"
    paper: "#F4F6FB"
    white: "#FFFFFF"
    text-dark: "#171D2C"
    text-muted: "#697287"
  layout:
    max-width: "680px"
    direction: rtl
---

# Velvet Factory — Brief V10.2 · Ink & Candy

## עיקרון

V10.2 הוא **מגזין מודיעין יומי חי**, לא dashboard גנרי. הוא צריך להיות חד, עשיר בתמונות אמיתיות, קל לסריקה בטלפון ומושך מספיק כדי להרגיש כמו מוצר שאנשים אחרים היו רוצים לקבל.

עברית היא ברירת המחדל. אנגלית נשארת רק למונחים טבעיים כמו `Instagram`, `Reel`, `Canva`, `Insights`, `VelvetOS` ו־`V10.2`.

## פלטת Ink & Candy

- `#101828` — קנבס Ink כהה.
- `#151D2E` — מעטפת ו־Hero surface.
- `#FF4F91` — החלטה / צריך ממך / תוכן שדורש תשומת לב.
- `#6C7CFF` — מערכת / VelvetOS / מידע ניהולי.
- `#B8F34A` — תקין / הצלחה / אות חיובי.
- `#45D7FF` — מידע חי / Insights.
- `#FF8C66` — ייצור והדפסה.
- `#FFD45A` — כסף / הזדמנות / מעקב.
- `#F4F6FB` — משטח קריאה בהיר.

הצבעים סמנטיים. אין לצבוע כל כרטיס רק בשביל אפקט; צבע מדגיש משמעות.

## תמונות הן חלק מהגריד

V10.2 מבטל את הגישה של “כרטיס ואז אולי תמונה”. כל אזור ויזואלי משתמש בפריסת מדיה מפורשת:

1. `hero_visual` — **תמונת היום** גדולה, כמעט ברוחב מלא. מקור: studio/WIP/finished/live content אמיתי בלבד.
2. `layout=split` — כרטיס עבודה שבו כ־⅓ מהשטח מוקדש לתמונה וכ־⅔ למצב, חסם ושלב הבא.
3. `cards[]` — עד 3 mini-cards לתוכן/מחקר/הזדמנויות; כל כרטיס יכול להכיל thumbnail, כותרת, ממצא ופעולה.
4. `covers[]` — תמונות נוספות בתוך כרטיס כשבאמת נדרש.

אם אין asset אמיתי — אזור התמונה לא נוצר. אין placeholder בפרודקשן, stock או filler.

## בחירת תמונת היום

אם ה־payload מספק `hero_visual`, הוא מנצח. אחרת ה־renderer רשאי לקדם תמונה קיימת מתוך ה־brief לפי סדר עדיפות:

1. עבודה/ייצור פעיל.
2. תוכן רלוונטי.
3. Instagram/Insights חי.
4. הזדמנות/מחקר.

תמונה שקודמה ל־Hero לא משוכפלת שוב בכרטיס המקורי.

## היררכיה

1. Hero: תאריך, גרסה, מצב העסק ובריאות מערכת.
2. **תמונת היום** — כשיש asset אמיתי.
3. עד 4 KPI מאומתים.
4. תמונת מצב במשפט אחד.
5. מה השתנה מאז הבריף הקודם.
6. צריך ממך.
7. כסף / עבודות / היום.
8. רדאר תוכן עם visual proof.
9. שולחן המחקר — עד 3 findings, רצוי עם thumbnail מאותו source.
10. הזדמנות קרובה — רק אם Studio Pulse מחזיר אות אמיתי.
11. פעילות VelvetOS — receipts ושינויים שבוצעו בפועל; בדרך כלל בלי תמונות.

## שדות V10.2

### Hero

```json
{
  "hero_visual": {
    "cid": "IMG_123.jpg",
    "href": "https://...",
    "eyebrow": "תמונת היום",
    "title": "העבודה המרכזית",
    "caption": "מה חשוב לראות כאן"
  }
}
```

במקום `cid` אפשר `url`/`src` אמיתי.

### Split card

```json
{
  "kind": "production",
  "layout": "split",
  "title": "עבודה חיה",
  "covers": [{"cid": "job.jpg", "caption": "מצב נוכחי"}]
}
```

### Mini visual cards

```json
{
  "kind": "content",
  "title": "רדאר תוכן",
  "cards": [
    {
      "url": "https://...",
      "href": "https://...",
      "kicker": "מאומת חי",
      "title": "Reel אחרון",
      "text": "הנתון החשוב",
      "action": "מה עושים עכשיו"
    }
  ]
}
```

## חוקי אמת

- אין ₪ מומצא.
- אין Insights מומצאים.
- `scheduled/uploaded != verified live`.
- `0` אינו תחליף למידע חסר.
- תמונה היא evidence של אותו item/source.
- thumbnail מחקרי חייב להגיע מאותו מקור או להיעלם.
- פעילות VelvetOS מציגה פעולה/receipt שבאמת קרו.

## Gmail / mobile

- RTL מלא.
- 320–680px, mobile-first.
- table-based, Gmail-safe.
- split/cards נערמים במובייל.
- טקסט קריטי לעולם לא נצרב בתוך תמונה.
- תמונות לחיצות כאשר יש יעד אמיתי.

## תאימות

JSON ישן של 01–07 ממשיך לעבוד. שדות V10.2 אופציונליים. `Studio Pulse` נשאר projection fallback בלבד — לא מקור אמת חדש.
