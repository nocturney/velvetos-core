# איך מחזירים את Canva לרשימה

מחקנו את **התוסף מהחנות**. זה נכון. עכשיו מוסיפים את Canva כשרת רחוק (רק קישור), לא מהחנות.

אל תחפש «Canva» במרקטפלייס. אל תלחץ Install Plugin.

## הכי קל: לחץ על הקישור

1. במחשב שבו מותקן Cursor, לחץ:
   [הוסף Canva ל-Cursor](cursor://anysphere.cursor-deeplink/mcp/install?name=canva&config=eyJ1cmwiOiJodHRwczovL21jcC5jYW52YS5jb20vbWNwIiwidHlwZSI6Imh0dHAifQ==)
2. Cursor ישאל אם להתקין שרת MCP בשם `canva`. אשר.
3. ייפתח דפדפן — היכנס לחשבון Canva ולחץ Allow.
4. חזור ל-Cursor. ברשימת MCP אמור להופיע `canva` (ירוק / Connect).

אם הקישור לא נפתח, העתק לכתובת בדפדפן במחשב:

`cursor://anysphere.cursor-deeplink/mcp/install?name=canva&config=eyJ1cmwiOiJodHRwczovL21jcC5jYW52YS5jb20vbWNwIiwidHlwZSI6Imh0dHAifQ==`

זה עובד רק ב-Cursor Desktop על המחשב שלך. לא בתוך הצ'אט של הסוכן בענן.

## בלי קישור: הוספה ידנית (Windows)

1. ב-Cursor לחץ `Ctrl + Shift + P`.
2. הקלד: `View: Open MCP Settings` ולחץ Enter.
3. לחץ **Add Custom MCP** / **New MCP Server**.
4. נפתח קובץ `mcp.json`. מחק הכל והדבק בדיוק:

```json
{
  "mcpServers": {
    "canva": {
      "type": "http",
      "url": "https://mcp.canva.com/mcp"
    }
  }
}
```

5. שמור (`Ctrl + S`).
6. ברשימת MCP יופיע `canva`. לחץ **Connect** / התחבר.
7. בדפדפן אשר את Canva.

## מה לא לעשות

- לא Install מחדש של תוסף Canva מהחנות (`spawn git ENOENT` יחזור).
- לא לחפש Canva תחת Plugins.
- לא לחכות שיופיע לבד אחרי Uninstall — צריך להוסיף אותו כ-MCP.

## אחרי שהחיבור חי

**לא בצ'אט הזה, ולא בשום צ'אט שכתוב בו «Setting up environment».**  
זה Cloud Agent — Canva מהמחשב לא מגיע לשם. Gmail כן, Canva לא.

### איפה לבדוק שהעיצוב באמת נפתח

1. ב-Cursor **על המחשב** (חלון העורך, לא האתר cursor.com/agents).
2. צ'אט חדש: `Ctrl + L`.
3. ליד השליחה בחר **Agent** — לא Cloud, לא Background.
4. כתוב: `הצג את העיצוב האחרון שלי ב-Canva`.

אם חוזר שם עיצוב + קישור — החיבור עובד.  
אם שוב «Setting up environment» — זה עדיין ענן. תבטל ותפתח Agent מקומי.
