# Research Seat - 2026-09-15 - late catch-up

Run state: `ready_for_brief` (late).
Research cutoff: `2026-09-15T07:00:00+03:00`; `cutoff_met: false`.
Observed at: 2026-09-15T11:14:45.562861+00:00
Executed by the current assistant with public web search/open plus live business connectors; no separate researcher invocation is claimed.

## Findings and experiments

```json
[
  {
    "id": "RS-20260915-SEAM",
    "type": "experiment",
    "state": "ready_for_brief",
    "implementation_status": "not_implemented",
    "first_seen": "2026-09-15",
    "last_reviewed": "2026-09-15",
    "execution_owner": "system_for_preview; owner_for_print",
    "impact": "medium_unmeasured",
    "effort": "low_after_existing_3mf_and_profile_resolved",
    "source_url": "https://help.prusa3d.com/article/seam-painting_168620",
    "published_at": null,
    "observed_at": "2026-09-15T11:14:45.562861+00:00",
    "confidence": "high_tool_capability; studio_fit_unproven",
    "next_action": "Resolve existing approved 3MF and compatible profile, then compare seam placement previews without printing."
  },
  {
    "id": "RS-20260915-LAYER",
    "type": "experiment",
    "state": "ready_for_brief",
    "implementation_status": "not_implemented",
    "first_seen": "2026-09-15",
    "last_reviewed": "2026-09-15",
    "execution_owner": "system_for_preview; owner_for_print",
    "impact": "medium_unmeasured",
    "effort": "low_after_existing_3mf_and_profile_resolved",
    "source_url": "https://help.prusa3d.com/article/variable-layer-height-function_1750",
    "published_at": null,
    "observed_at": "2026-09-15T11:14:45.562861+00:00",
    "confidence": "high_method; studio_fit_unproven",
    "next_action": "Compare uniform and variable layer height on the same approved model/profile; record slicer estimates and compatibility."
  }
]
```

## Owner-facing research (exact gated text)

VELVET FACTORY · מודיעין יומי
מחקר וצעדים מעשיים
15.9.2026 · מחקר השלמה · לאחר שעת החיתוך
V10.3 · חי
●
מצב המחקר · שני ניסויים לבדיקה
●
עמידה בזמן · הושלם אחרי החיתוך
2
ניסויים מוצעים
0
שינויי ייצור שבוצעו
0
מק״טים חדשים שאומתו
תמונת מצב עכשיו
המחקר היום מציע שני ניסויי איכות ממוקדים: מיקום תפר וגובה שכבה משתנה. שניהם נשענים על תיעוד רשמי, אך עדיין לא נבדקו על דגם ופרופיל של הסטודיו. לא נמצא בסיס מספיק לקידום מוצר חדש למכירה.
מה השתנה מאז הבריף הקודם
●
בוצעה סריקת מקורות חדשה היום; מחקר אתמול אינו מוצג כמחקר חדש.
●
שתי ההמלצות נשארות לא מיושמות עד בדיקה על קובץ ופרופיל מאומתים של הסטודיו.
ניסוי 1 · מיקום התפר
להרחיק את התפר מאזורי המיקוד
מה נמצא: Prusa מתעדת ב־Seam painting סימון אזורים מועדפים לתפר ואזורים שבהם אין להציבו. הבחירה תלויה גם בהגדרת מיקום התפר. אין הבטחה שהתפר ייעלם.
הניסוי המוצע: באותו דגם מאושר, להשוות תצוגת מסלולים ללא ציור תפר לתצוגה שבה התפר מנותב לאזור פחות בולט. לשמור את יתר ההגדרות קבועות.
מה נמדוד: מיקום תחילות המסלול ביחס לפנים, ללוגו או לפרט המרכזי; לאחר אישור הדפסת ניסיון, להשוות את אותה זווית צילום.
המצב: לא יושם. נדרשים קובץ 3MF קיים ופרופיל תואם כדי לבדוק את ההתאמה אצלנו. לא הותקנה תוכנה ולא הופעלה מדפסת.
ביטחון: גבוה לגבי יכולת הכלי; התועלת בדגם שלנו עדיין לא נבדקה.
תיעוד Prusa: Seam painting
ניסוי 2 · גובה שכבה משתנה
לבדוק היכן כדאי להוסיף פירוט
מה נמצא: Prusa מתעדת שינוי אוטומטי או ידני של גובה השכבה לאורך הדגם, עם אפשרות להחליק מעברים. זו דרך לבחון פירוט מקומי בלי להחיל שכבות דקות על כל הגובה.
הניסוי המוצע: להשוות סלייס אחיד לסלייס עם גובה משתנה על אותו דגם, חומר ופרופיל. לבדוק קודם תאימות לגרסת הסלייסר ולתמיכות הנדרשות.
מה נמדוד: זמן וגרמים משוערים בתוכנה, אזורי שינוי הגובה ואיכות קווי המתאר בתצוגה. איכות פיזית תימדד רק אחרי הדפסת ניסיון מאושרת.
המצב: לא יושם. אין כרגע מספר חיסכון או שיפור שנמדד אצלנו; לא מבוצע מעבר ייצור ל־PrusaSlicer.
ביטחון: גבוה לגבי השיטה; בינוני לגבי התאמת הניסוי לפני שנבחר דגם.
תיעוד Prusa: Variable Layer Height
מוצרים חוזרים / מה לא קידמנו
סמני צמחים נשארים מחוץ לקטלוג
נבדק מועמד של סמני צמחי תבלין. רישום משני מציין תמונת כיסוי שנוצרה ב־AI והיעדר בדיקת הדפסה פיזית; עמוד המקור ב־Thingiverse לא נטען בבדיקה.
לכן לא אומתו רישיון המקור, ההדפסה או ביקוש מקומי. המועמד לא קיבל מק״ט, מחיר או אישור מכירה. תמונת כיסוי לבדה אינה הוכחת מוצר.
רישום המועמד שנבדק
מקור הדגם שלא נטען
מה יושם / מה הבא
תוכנית ניסוי מוכנה; ייצור ללא שינוי
שני הניסויים הם הצעות חדשות לבדיקה, לא הטמעות ולא ניסויים שכבר רצים. הכנת השוואת הסלייס היא עבודת המערכת כאשר הקבצים זמינים; הפעלת מדפסת נשארת פעולה אנושית.
בדיקת Best Skills האחרונה מתועדת ל־14.9; מרווח 48 השעות טרם חלף ולכן לא שוכפלה היום. בדיקת גרסאות OpenPost שייכת לאוטומציה הייעודית ולא שוכפלה כאן.
נתוני Instagram שלנו נשלפו מהחיבור הקנוני. המדגם עדיין קטן, ולא קודמה ממנו מסקנת ביצועים חדשה.
פריט
מצב
המשך
מיקום תפר
לא יושם
בחירת 3MF ופרופיל; השוואת סלייס
גובה שכבה
לא יושם
אותו דגם; בדיקת תאימות ותצוגה
סמני צמחים
חסום לקידום
אימות מקור, רישיון והדפסה
מקורות וטריות
נבדק היום, לא הושלם בזמן הבוקר
המחקר הזה בוצע כריצת השלמה ב־15.9.2026, אחרי חיתוך 07:00. הוא אינו הוכחה שהריצה הלילית סיימה בזמן.
תיעוד Prusa הוא ידע קיים שנבדק כעת; תאריך הפרסום המקורי לא אומת ולכן אין טענה שהשיטות הושקו השבוע. ממצאים חיצוניים אינם נתוני המכירות או ביצועי ההדפסה של Velvet Factory.
ההקשר העסקי הוצלב עם Jobs ו־Books: העבודות הרשומות סופקו, והגבייה הפתוחה היא 4,790 ש״ח. לכן ההמלצות נשארות בדיקות מצומצמות ולא ייצור מלאי חדש.
Velvet Factory · מחקר 15.9.2026 · מקורות נבדקו היום; אין שינוי ייצור

## Evidence and limitations

- Primary Prusa documentation was read on this date; original publication dates unavailable. These are existing methods, not newly released features.
- No slicer, production profile, SKU, price or physical print was changed.
- Candidate screening: https://cults3d.com/en/3d-model/home/herb-garden-markers-8-plant-labels-flat-print-cc0 ; attributed original https://www.thingiverse.com/thing:7387328 could not be loaded. License and physical-print status were not independently validated, so no SKU promotion.
- Best Skills lastPass 2026-09-14: 48-hour review not due; OpenPost daily upstream watch not duplicated.
- Prior research remains historical: 2026-09-14-orchestra.md.
