# איך מחברים את 3D AI Studio ל-Cursor

מנוי בתשלום ב-[www.3daistudio.com](https://www.3daistudio.com).  
פלייבוק: [`3DAISTUDIO.md`](3DAISTUDIO.md).  
אין מפתח API בגיט. OAuth בלבד.

## שני ממשקים — Desktop ≠ Cloud

| ממשק | מאיפה MCP נטען | OAuth |
|---|---|---|
| **Cursor Desktop** (Agent מקומי) | `.cursor/mcp.json` בפרויקט + Customize → MCPs | Connect ב-IDE |
| **Cloud Agent** (`cursor.com/agents`) | **Dashboard → Integrations & MCP** (Team MCP) | Connect בדף Agents |

**חיבור Desktop לא מעביר אוטומטית ל-Cloud.** Canva עובד בענן כי נרשם ב-Team MCP — 3DAI צריך אותו תהליך.

שם השרת בכל מקום: **`threedaistudio`** (לא `3daistudio` — Cursor לא מציג מפתחות שמתחילים בספרה).

---

## A) Desktop (כבר עובד אצלך)

[`/.cursor/mcp.json`](../../.cursor/mcp.json):

```json
"threedaistudio": {
  "url": "https://mcp.3daistudio.com/mcp"
}
```

קישור מהיר:  
[cursor://anysphere.cursor-deeplink/mcp/install?name=threedaistudio&config=eyJ1cmwiOiJodHRwczovL21jcC4zZGFpc3R1ZGlvLmNvbS9tY3AifQ==](cursor://anysphere.cursor-deeplink/mcp/install?name=threedaistudio&config=eyJ1cmwiOiJodHRwczovL21jcC4zZGFpc3R1ZGlvLmNvbS9tY3AifQ==)

---

## B) Cloud Agent — שלבים

### 1. אדמין: Team MCP (פעם אחת לצוות)

1. [cursor.com/dashboard](https://cursor.com/dashboard) → **Cloud Agents** → **Integrations & MCP**  
   (או Team Settings → MCP Configuration)
2. **Add MCP server** → **HTTP**
3. מלא:
   - **Name:** `threedaistudio`
   - **URL:** `https://mcp.3daistudio.com/mcp`
4. שמור.
5. (אופציונלי) **Add to Team Marketplace** — כדי שגם IDE יראה את אותו שרת מהדשבורד.

Canva הוגדר כך — 3DAI באותו מסלול.

### 2. כל משתמש: OAuth לענן (נפרד מ-Desktop)

1. פתח [cursor.com/agents](https://cursor.com/agents)
2. לפני / בזמן ריצה: תפריט **MCP** (dropdown)
3. הפעל **`threedaistudio`**
4. **Connect** → Login ל-3D AI Studio → Allow  
   (redirect: `https://www.cursor.com/agents/mcp/oauth/callback`)

### 3. אימות

הרץ Cloud Agent עם: «בדוק יתרת קרדיטים ב-3D AI Studio» או «ייצא מודל ל-STL» (אחרי אישור קונספט).

אם OAuth נכשל — בדashboard events יופיע `mcp_auth_error`.

### 4. רשת (אם egress מוגבל)

ודא ש-`mcp.3daistudio.com` ברשימת ה-allowlist של הסביבה.  
סביבת HQ הנוכחית: egress פתוח.

---

## גיבוי: דרך האתר

1. Login ב-[3daistudio.com](https://www.3daistudio.com)
2. Settings → **AI Assistants (MCP)** → Cursor → Allow
3. חזור ל-Cursor (Desktop או Agents) → Connect

---

## מה לא לעשות

| חיפוש | למה |
|---|---|
| רק `.cursor/mcp.json` ל-Cloud | הקובץ לא מגיע ל-VM של Cloud Agent |
| API key ב-git / ב-Team MCP | OAuth בלבד |
| Desktop Connect = Cloud מוכן | OAuth נפרד לכל ממשק |
| Flow → Bob | עוזר קנבס, לא MCP |
| הדפסה / ₪ מ-HQ | רצפה + אדם |

## Failover

MCP אפור → אתר + Drive. אין מפתח / ₪ מומצאים.

## אחרי Connect ירוק

«3DAI מחובר ב-Desktop» / «3DAI מחובר ב-Cloud» · `@studio-producer` · `3DAISTUDIO.md`.
