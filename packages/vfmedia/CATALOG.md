# קטלוג מדיה יחיד

מושב: **תפעול** (קליטה). Cursor מחזיק את הסכמה. GrokBot עובד על Drive MCP.  
לא מדף מק״ט (`vfsku`). לא ממציאים שמות מוצר ולא ₪.

**הקטלוג:** [`catalog.json`](catalog.json)  
**הסכמה:** [`catalog.schema.json`](catalog.schema.json)  
**התיקיות:** [`FOLDERS.json`](FOLDERS.json)  
**הנוהל:** [`docs/MEDIA-VAULT.md`](../../docs/MEDIA-VAULT.md)

אין קטלוג שני. שורת INSTA / Canva / מדף מק״ט אינה מחליפה את הקובץ הזה.

## שדות חובה לכל פריט

| שדה | מה רושמים | מה אסור |
|---|---|---|
| `sourceFile.id` + `sourceFile.url` | מזהה Drive + קישור צפייה של **המקור** | מזהה בדוי, «חסר» כאילו זה קובץ |
| `viewDescription` | מה שנראה בקובץ אחרי פתיחה | סצנת רצפה / מוצר מומצא |
| `uploadedAt` | תאריך העלאה מהקובץ או מההעלאה | תאריך משוער בלי מקור |
| `productLink` | קישור מוצר / עבודה **אם ידוע** | מק״ט חדש, שם מדף, ₪ |
| `status` | `inbox` / `source` / `in_progress` / `approved` | סטטוס מתיקייה בלי העברה |
| `assignee` | מושב או שם שקיבל את הקובץ | סוכן מומצא |
| `derivativeIds` | מזהי נגזרות (id+url) שכבר קיימות | רשימת עיצובים שלא נוצרו |
| `sourceLinks` | קישורי מקור שהמשתמש נקב | MakerWorld / טרנד מומצא |
| `versionApproval` | `none` / `pending` / `approved` / `rejected` + מי ומתי | להסיק אישור מתיקיית «מאושר לפרסום» |

`id` של שורה הוא מזהה קטלוג, **לא** מק״ט. אין שדה SKU. כשיש כרטיס מדף אמיתי — `productLink` מצביע אליו; לא יוצרים שם.

## Asset Truth — שדות אופציונליים אך סמנטיקה מחייבת

`truth` מרחיב את אותה שורת קטלוג; הוא **לא** קטלוג נוסף. אם השדה חסר, Visual Foundry מתייחס לנכס כ־`unverified` לצורכי טענה ציבורית.

- `truthLevel`: `verified_real` / `derived_real` / `illustrative_ai` / `synthetic` / `unverified`.
- `origin`: מקור ידוע בלבד (`studio_camera`, `studio_export`, `customer_media`, `canva`, `generated_ai`, `external_reference`, `unknown`).
- `rightsStatus`: `approved` / `restricted` / `unknown` / `not_applicable`.
- `usableFor`: שימושים מותרים כמו `hero`, `proof`, `reel`, `cover`, `reference_only`.
- `qualityScore`, `visualTags`, `project`, `object`, `material`, `evidenceRefs` — רק כאשר ידועים/נמדדו.

**חוק אמת:** `verified_real` מתאר את מקור הנכס, לא את תקפות כל טענה שאפשר לכתוב עליו. טענה עובדתית יוצאת החוצה רק דרך `packages/vfom/CONTENT-CONTRACT.schema.json` עם `truthClaims[].status=verified` וקישור ל־evidence אמיתי. `illustrative_ai` ו־`synthetic` לעולם אינם הוכחת מדידה/עומס/כשל/הצלחה פיזיים.

## סטטוס מול תיקייה

| `status` | תיקיית Drive | מי מעביר |
|---|---|---|
| `inbox` | `01 - נכנס` | מעלה |
| `source` | `02 - מקור` | **תפעול** אחרי קליטה |
| `in_progress` | `03 - בעבודה` | סטודיו / צמיחה |
| `approved` | `04 - מאושר לפרסום` | רק אחרי `versionApproval.state=approved` |

העלאה ≠ אישור. תיקיית מאושר לבד ≠ הוכחת אישור.

## איך מוסיפים שורה

1. הקובץ כבר ב־Drive (נכנס או מקור). יש `id` אמיתי.
2. תפעול ממלא תיאור לפי צפייה.
3. מוסיפים אובייקט ל־`items` לפי הסכמה. בלי מק״ט חדש. בלי ₪.
4. כאשר קיימת ראיה אמיתית, מוסיפים `truth` לפי הסכמה; אין להמציא metadata כדי "להעלות" נכס לרמת אמת גבוהה יותר.
5. `python3 scripts/vfmedia.py validate`

שורות בקטלוג חייבות `sourceFile.id` אמיתי מ־Drive. אין דמו. אין מק״ט משם קובץ. העלאה לנכנס ≠ אישור.
