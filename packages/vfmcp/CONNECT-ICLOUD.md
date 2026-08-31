# איך מחברים iCloud Drive ל-Cursor (Mac בלבד)

Apple **לא** נותנת OAuth/HTTP MCP ל-iCloud Drive כמו Gmail או Canva.  
הגישה היא **MCP מקומי** על macOS — קריאה/כתיבה לתיקייה ש-iCloud Drive מסנכרן.

**Cloud Agent (Linux) לא רואה iCloud.** לעבודה מהענן: סנכרון ל-Google Drive — [`ICLOUD-DRIVE-SYNC.md`](ICLOUD-DRIVE-SYNC.md).

## שני ממשקים — Desktop ≠ Cloud

| ממשק | iCloud MCP | מה HQ רואה |
|---|---|---|
| **Cursor Desktop** (Mac, Agent מקומי) | כן — stdio MCP + Full Disk Access | קבצים ב-iCloud ישירות |
| **Cloud Agent** | **לא** — אין Apple על Linux | **Drive** אחרי סנכרון `Velvet Factory/` |

---

## A) Desktop — MCP מומלץ

### 1. התקנה (Node)

```bash
npm install -g icloud-drive-mcp-server
```

חלופות: [apple-ecosystem-mcp](https://github.com/abhinavag-svg/apple-ecosystem-mcp) (Mail/Calendar/iCloud), [apple-files-mcp](https://pypi.org/project/apple-files-mcp/) (קבצים + תגיות Finder).

### 2. הרשאות macOS

**System Settings → Privacy & Security → Full Disk Access** → הוסף **Cursor** (ולפעמים **Terminal** אם MCP רץ משם).

בלי זה: `list_folder` / `read_file` על placeholders של iCloud ייכשלו.

### 3. הוספה ל-Cursor

`Ctrl+Shift+P` → **View: Open MCP Settings** → הוסף ל-`mcp.json` (או מיזוג עם Canva / 3DAI מהריפו):

דוגמה מלאה: [`examples/mcp-icloud-desktop.json`](examples/mcp-icloud-desktop.json).

```json
{
  "mcpServers": {
    "canva": {
      "type": "http",
      "url": "https://mcp.canva.com/mcp"
    },
    "threedaistudio": {
      "url": "https://mcp.3daistudio.com/mcp"
    },
    "icloud": {
      "command": "icloud-drive-mcp-server",
      "env": {
        "ICLOUD_MCP_ROOT": "/Users/YOU/Library/Mobile Documents/com~apple~CloudDocs/Velvet Factory",
        "ICLOUD_MCP_WRITE": "false"
      }
    }
  }
}
```

החלף `YOU` בשם המשתמש.  
`ICLOUD_MCP_WRITE`: `false` = קריאה בלבד (מומלץ). `true` רק אם צריך `write_file` / `delete_file`.

### 4. Reload + אימות

1. **Developer: Reload Window**
2. צ'אט **Agent מקומי** (לא Cloud): «רשום את הקבצים בתיקיית Velvet Factory ב-iCloud»
3. אם קובץ בענן בלבד (placeholder `.icloud`) — MCP אמור לקרוא ל-`brctl download` אוטומטית

---

## B) תיקיית iCloud לסטודיו

צור (או השתמש ב):

`~/Library/Mobile Documents/com~apple~CloudDocs/Velvet Factory/`

| תת-תיקייה | שימוש |
|---|---|
| `floor/` | תמונות רצפה, timelapse |
| `stl/` | מודלים לפני/אחרי slicer |
| `jobs/` | קבצים לפי שם עבודה (כמו Drive) |
| `office/` | חשבונות, PDF — **לא** רפואי/משפטי/אישי |

אותם שמות תת-תיקיות מופיעים ב-[`ICLOUD-DRIVE-SYNC.md`](ICLOUD-DRIVE-SYNC.md) בצד Drive.

---

## Failover (Desktop)

| מצב | מעבירים ל־ |
|---|---|
| MCP אפור / אין Full Disk Access | פתח קובץ ידנית · העתק ל-Drive · צ'אט Cloud Agent |
| placeholder לא יורד | `brctl download` ידני על הנתיב · או סנכרון [`sync-icloud-to-drive.sh`](../../scripts/sync-icloud-to-drive.sh) |
| Cloud Agent צריך את הקובץ | **חובה** סנכרון Drive — MCP iCloud לא מגיע לענן |

---

## מה לא לעשות

- לא לשים MCP iCloud ב-Team MCP / Cloud Agent — לא יעבוד על Linux
- לא לפתוח תיקיות אישיות/רפואיות/משפטיות אלא אם הבעלים שם אותן במפורש
- לא `ICLOUD_MCP_WRITE=true` בלי צורך — מחיקה עוברת ל-Trash אבל עדיין סיכון
- לא סודות Apple ID / app-specific password בגיט

## אחרי Connect ירוק (Desktop)

«iCloud מחובר ב-Desktop» · חיפוש job ב-`jobs/` · Cloud: «חפש ב-Drive Velvet Factory/iCloud mirror».
