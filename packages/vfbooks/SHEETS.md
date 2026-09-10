# גיליון סטודיו · יומן עבודות

מושב: **תפעול**. לא MCP Sheets נפרד. לא פק חדש.

## סמכות קנונית (2026-09-10)

**Google Sheet `VF HQ · jobs` הוא ה-SoT.**
`office/ledger/live/jobs.csv` הוא **cache מקומי** בלבד (gitignore) — לא ספר שני.

הגשר:

1. קריאה: Drive MCP `download_file_content` + `exportMimeType=text/csv` **או** Drive API כשיש `GOOGLE_TOKEN` / credentials כמו vfmedia.
2. טעינה ל-cache: `python3 scripts/vf_office.py jobs pull --from-csv PATH`
3. צרכנים (Living Studio / World Model / Autonomy) קוראים את ה-cache אחרי pull.
4. כתיבה: עדכון cache (`jobs add` / `jobs stage`) → `jobs push` → העלאה לגיליון → `jobs pull --force` לאימות.
5. קונפליקט: cache מלוכלך + Sheet שונה → `status=conflict` בלי דריסה (אלא אם `--force`).

IDs חיים: `office/ledger/bindings.json` (לא סוד). בלי קובץ / בלי ID: כותבים **חסר גיליון** וממשיכים.

תאי גיליון (Desktop): `mcp-gsheets` ב־`~/.cursor/mcp.json` — `packages/vfmcp/CONNECT-SHEETS.md`. לא בפרויקט (מפתח שירות). Cloud: CSV + Drive מספיקים.

## מתי יש ID (נזרע 31.8.2026)

תיקייה: [VF HQ · משרד](https://drive.google.com/drive/folders/1dFvQBlwzoefZ7OZKHDbMAFjuJ_9kXw8e) (`1dFvQBlwzoefZ7OZKHDbMAFjuJ_9kXw8e`).

| ספר | spreadsheetId | שם |
|---|---|---|
| יומן עבודות | `13jTA9FJLNWMEc2zEpdmXL5kNWYYguQHXeOdOPpDNgao` | VF HQ · jobs |
| מק״ט | `1eHfokYC0T4JZT2hvxnVy_CWThIEMrBwrhVUMuQqYnGE` | VF HQ · sku |
| הצעות | `13-kaFD8OpQ0ozMB0UuBNnpfYsvQZ1NVBWg05WrmIn1w` | VF HQ · quotes |
| ספר | `11eRkRT78Nzacef8PmPCk0xqtPXy0uw9ivu747bw0FIs` | VF HQ · books |

1. `search_files` לפי השם למעלה (לא סריקת תיקיות אישיות).
2. `download_file_content` עם `exportMimeType=text/csv`.
3. `python3 scripts/vf_office.py jobs pull --from-csv …`
4. או `read_file_content` אם צריך תקציר ולא טבלה.

בלי ID / בלי שם: כותבים «חסר גיליון» וממשיכים מ־Gmail תווית חשבונות או מהמשתמש הדביק. לא ממציאים שורות. לא ממציאים ₪. X ₪ אם חסר סכום מאומת.

## מה דולג

| הצעה | למה |
|---|---|
| להכריז על CSV מקומי כ-SoT בזמן שהוא gitignored | נסגר — Sheet קנוני + adapter |
| לחבר MCP Sheets בלי ID | אין צורך — CSV export + Drive מספיקים |
| לפתוח גיליון Fitbit / איקאה / רפואי | אישי. לא הסטודיו |
| למלא מחיר ביומן | רק סכום מראש צוות. אחרת ריק / X ₪ |
