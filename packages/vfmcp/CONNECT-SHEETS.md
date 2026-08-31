# איך מחברים Google Sheets MCP

לא ב־`.cursor/mcp.json` של הריפו — צריך קובץ מפתח שירות. שמים ב־**`~/.cursor/mcp.json`** (גלובלי למשתמש), לא בפרויקט: קובץ הפרויקט מנצח ומרוקן env אם נדביק stub.

חבילה: [`mcp-gsheets`](https://github.com/freema/mcp-gsheets) (`npx -y mcp-gsheets@latest`).

גיבוי בלי מפתח (כבר בליבה): `python3 scripts/vf_office.py jobs` + Drive `exportMimeType=text/csv`. בלי ID: **חסר גיליון**. לא ממציאים ₪.

## Desktop

1. ב-Google Cloud: service account + Sheets API. הורד JSON **מחוץ לגיט** (למשל `~/.config/velvetos/gsheets.json`).
2. שתף את ארבעת הגיליונות ב־[VF HQ · משרד](https://drive.google.com/drive/folders/1dFvQBlwzoefZ7OZKHDbMAFjuJ_9kXw8e) עם אימייל ה־service account (עורך).
3. הדבק ל־`~/.cursor/mcp.json` (מזג, אל תמחק Canva):

```json
"mcp-gsheets": {
  "command": "npx",
  "args": ["-y", "mcp-gsheets@latest"],
  "env": {
    "GOOGLE_PROJECT_ID": "your-project-id",
    "GOOGLE_APPLICATION_CREDENTIALS": "/absolute/path/to/gsheets.json"
  }
}
```

4. Reload Window. אל תעתיק את ה-JSON לריפו.

IDs חיים: `office/ledger/bindings.json`. דוגמה מלאה: [`mcp.desktop.example.json`](mcp.desktop.example.json).

## Cloud Agent

אין service account בענן הזה. נשארים עם Drive + CSV עד שTeam MCP / סוד סביבה יוגדר **מחוץ לגיט**.

## VF

`mcpBind.mcp-gsheets.enabled: true` — כתיבת תא אחרי Connect. בלי Connect: `vf_office.py`. X ₪ אם חסר סכום מאומת.
