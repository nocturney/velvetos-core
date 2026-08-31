# גיליון סטודיו · יומן עבודות

מושב: **תפעול**. לא MCP Sheets נפרד. לא פק חדש.

Grok וג׳ימיני יודעים לערוך Google Sheets כמחבר. כאן אין שרת Sheets נפרד.

הגשר (31.8.2026, `bc-1764e30f`): CSV מקומי + ייצוא ל־Drive.

- קובץ חי: `office/ledger/live/jobs.csv` (נוצר ב־`python3 scripts/vf_office.py jobs add`).
- תבניות ריקות: `office/ledger/templates/` — בלי שורות ₪.
- ייצוא: `python3 scripts/vf_office.py jobs csv`
- Drive: `create_file` עם `contentMimeType=text/csv` (הופך לגיליון) או עדכון אחרי שנקב ID.
- IDs חיים: `office/ledger/bindings.json` (לא סוד). בלי קובץ / בלי ID: כותבים **חסר גיליון** וממשיכים.

## מתי יש ID (נזרע 31.8.2026)

תיקייה: [VF HQ · משרד](https://drive.google.com/drive/folders/1dFvQBlwzoefZ7OZKHDbMAFjuJ_9kXw8e) (`1dFvQBlwzoefZ7OZKHDbMAFjuJ_9kXw8e`).

| ספר | spreadsheetId | שם |
|---|---|---|
| יומן עבודות | `13jTA9FJLNWMEc2zEpdmXL5kNWYYguQHXeOdOPpDNgao` | VF HQ · jobs |
| מק״ט | `1eHfokYC0T4JZT2hvxnVy_CWThIEMrBwrhVUMuQqYnGE` | VF HQ · sku |
| הצעות | `13-kaFD8OpQ0ozMB0UuBNnpfYsvQZ1NVBWg05WrmIn1w` | VF HQ · quotes |
| ספר | `11eRkRT78Nzacef8PmPCk0xqtPXy0uw9ivu747bw0FIs` | VF HQ · books |

1. `search_files` לפי השם למעלה (לא סריקת תיקיות אישיות).
2. `download_file_content` עם `exportMimeType=text/csv` — שורות לספר / מק״ט / תור.
3. או `read_file_content` אם צריך תקציר ולא טבלה.
4. כתיבה לגיליון: מעדכנים את ה־CSV המקומי ואז `create_file` / ייצוא. Drive MCP לא עורך תא בודד.

בלי ID / בלי שם: כותבים «חסר גיליון» וממשיכים מ־Gmail תווית חשבונות או מהמשתמש הדביק. לא ממציאים שורות. לא ממציאים ₪. X ₪ אם חסר סכום מאומת.

## מה דולג

| הצעה | למה |
|---|---|
| לחבר MCP Sheets בלי ID | אין צורך — CSV + Drive מספיקים עד שכריסטיאן ירצה עריכת תאים |
| לפתוח גיליון Fitbit / איקאה / רפואי | אישי. לא הסטודיו |
| למלא מחיר ביומן | רק סכום מראש צוות. אחרת ריק / X ₪ |
