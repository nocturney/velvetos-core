# ניתוב חומר → מיטה

מושב: **ייצור** (`@studio-producer`). לא Print מ־HQ. לא פק חדש.

CLI: `python3 scripts/vfprod.py route --material PETG --strength outdoor`  
צי: `FLEET.json` (ארבע מיטות למילוי מהרצפה).  
Edge אחרי רכישה: [`WATCHTOWER.md`](WATCHTOWER.md) מריץ תור על ה־LAN — HQ רק ממליץ.

## מה מותר

1. לקרוא סוג חומר (PLA / PETG / ABS / ASA / Nylon / PEBA) + חוזק נדרש.
2. להמליץ **מיטה מועדפת** מתוך הארבע, עם נימוק קצר.
3. לחסום הדפסת לילה אם גרמי הסלייס גדולים מיתרת הגליל המאומתת (`vfprod.py remaining`).

## מה אסור

- לדחוף G-code / Start / Pause מ־Cloud או מ־Core.
- לנחש דגם מדפסת, סטטוס מיטה, או יתרת גרם.
- להמציא ₪ או שעת סיום.
- לחבר Elegoo / Snapmaker ל־Watchtower בלי אימות פרוטוקול (7.9: לא ברשימת הדף).

## טבלת המלצה (רצפה מאשרת)

| חומר | חוזק טיפוסי | מיטה מועדפת | למה |
|---|---|---|---|
| PLA | כללי | כל מיטה פנויה | קל; אדם בוחר |
| PETG | עמיד / יומיומי | Bambu A/B, אחר כך Elegoo | חום בינוני |
| ABS | חום | Bambu סגורה | ריח + enclosure |
| ASA | חוץ / UV | Bambu סגורה + פילטר | לא בלי סינון |
| Nylon | הנדסי / חום | Bambu סגורה | יבש + טמפ גבוהה |
| PEBA | גמיש / מכה | Bambu נתיב TPU; Snapmaker רק אם הרצפה אישרה | לא מנחשים נתיב גמיש |

חוזק `outdoor` → ASA. `flex` → PEBA. `engineering` → Nylon. אחרת PETG/PLA לפי הקלט.

פלט תמיד כולל `hq_prints: false`. אדם על המיטה לוחץ Print.

## G-code

המשרד **ממליץ נתיב קובץ** שכבר על הדיסק (`slicePath` ב־`vfsku`). לא יוצרים ולא שולחים G-code מכאן.
