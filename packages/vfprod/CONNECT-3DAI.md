# איך מחברים את 3D AI Studio ל-Cursor

מנוי בתשלום ב-[www.3daistudio.com](https://www.3daistudio.com).  
פלייבוק: [`3DAISTUDIO.md`](3DAISTUDIO.md).  
אין מפתח API בגיט. OAuth בלבד.

המתג **לא** ב-Marketplace / Plugins. שם השרת בכל מקום: **`threedaistudio`** (לא `3daistudio` — Cursor מדלג על מפתח שמתחיל בספרה).

## שני ממשקים — Desktop ≠ Cloud

| ממשק | מאיפה MCP נטען | OAuth |
|---|---|---|
| **Cursor Desktop** (Agent מקומי) | `.cursor/mcp.json` בפרויקט + Customize → MCPs | Connect ב-IDE |
| **Cloud Agent** (`cursor.com/agents`) | **Dashboard → Integrations & MCP** (Team MCP) | Connect בדף Agents |

**חיבור Desktop לא מעביר אוטומטית ל-Cloud.** Canva עובד בענן כי נרשם ב-Team MCP — 3DAI צריך אותו תהליך.

---

## A) Desktop

### הכי קל: לחץ על הקישור

1. במחשב שבו מותקן Cursor, לחץ:
   [הוסף 3D AI Studio ל-Cursor](cursor://anysphere.cursor-deeplink/mcp/install?name=threedaistudio&config=eyJ1cmwiOiJodHRwczovL21jcC4zZGFpc3R1ZGlvLmNvbS9tY3AifQ==)
2. Cursor ישאל אם להתקין שרת MCP בשם `threedaistudio`. אשר.
3. בדפדפן — Login ל-3D AI Studio → Allow.
4. ברשימת MCP אמור להופיע `threedaistudio` (Connect / ירוק).

אם הקישור לא נפתח, העתק לכתובת בדפדפן:

`cursor://anysphere.cursor-deeplink/mcp/install?name=threedaistudio&config=eyJ1cmwiOiJodHRwczovL21jcC4zZGFpc3R1ZGlvLmNvbS9tY3AifQ==`

**הערה:** ב-Cursor 3.15.6 deeplink עלול לא לעבוד — עדכן ל-3.15.12+ או הוסף ידנית למטה.

### מהפרויקט (אחרי pull)

הריפו מגדיר ב-[`.cursor/mcp.json`](../../.cursor/mcp.json):

```json
"threedaistudio": {
  "url": "https://mcp.3daistudio.com/mcp"
}
```

1. פתח את **שורש הריפו** `velvet-factory-headquarters-os` ב-Cursor (לא תת-תיקייה).
2. `Ctrl+Shift+P` → **Developer: Reload Window**.
3. Customize → **MCPs** — אמור להופיע `threedaistudio`.
4. Connect → Allow בדפדפן.

### בלי קישור: הוספה ידנית

1. `Ctrl+Shift+P` → `View: Open MCP Settings`.
2. הוסף ל-`mcp.json` (או הדבק את כל הקובץ):

```json
{
  "mcpServers": {
    "canva": {
      "type": "http",
      "url": "https://mcp.canva.com/mcp"
    },
    "threedaistudio": {
      "url": "https://mcp.3daistudio.com/mcp"
    }
  }
}
```

3. שמור → Reload Window → Connect על `threedaistudio`.

---

## B) Cloud Agent

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

אם OAuth נכשל — ב-dashboard events יופיע `mcp_auth_error`.

### 4. רשת (אם egress מוגבל)

ודא ש-`mcp.3daistudio.com` ברשימת ה-allowlist של הסביבה.
סביבת HQ הנוכחית: egress פתוח.

---

## גיבוי: דרך האתר

1. Login ב-[3daistudio.com](https://www.3daistudio.com)
2. Settings → **AI Assistants (MCP)** → Cursor → Allow
3. חזור ל-Cursor (Desktop או Agents) → Connect

מקור: [MCP](https://www.3daistudio.com/MCP) · v6.5 — «Available on all paid plans.»

אם הלשונית באתר חסרה אחרי Login + מנוי בתשלום: `support@3daistudio.com`.

## רואים רק Canva? / Cloud לא רואה 3DAI?

| סיבה | תיקון |
|---|---|
| רק `.cursor/mcp.json` ל-Cloud | הוסף Team MCP ב-Dashboard (סעיף B) |
| Desktop Connect = Cloud מוכן | OAuth נפרד לכל ממשק |
| לא עשית pull / Reload | `git pull` + Reload Window |
| שם ישן `3daistudio` | שנה ל-`threedaistudio` |
| Canva מ-global, פרויקט לא נטען | פתח שורש הריפו או deeplink |
| deeplink שבור (Cursor ישן) | עדכן Cursor או הוסף ידנית |
| Marketplace / Plugins | אין תוסף חנות. זה HTTP ב-`mcp.json` (Desktop) או Team MCP (Cloud) |
| API key ב-git / ב-Team MCP | OAuth בלבד |
| Flow → **Bob** | עוזר פנימי לקנבס, לא MCP ל-Cursor |
| הדפסה / ₪ מ-HQ | רצפה + אדם |

## Failover

MCP אפור / `needsAuth` → אתר + Drive. אין מפתח / ₪ מומצאים.

## אחרי Connect ירוק

«3DAI מחובר ב-Desktop» / «3DAI מחובר ב-Cloud» · `@studio-producer` · `3DAISTUDIO.md`.
