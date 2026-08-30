# למה Canva לא מתחבר — ומה לעשות

בודק בסוכן הזה (2026-08-30): השרת `https://mcp.canva.com/mcp` חי (401 בלי טוקן — תקין).
החיבור נכשל ב־**OAuth בדפדפן שלך**, לא ברשת של HQ.

## 1. אל תתחבר מתוך הסוכן בענן

המכונה הזו אין לה דפדפן. `npx mcp-remote` (הגדרה ישנה) מנסה `localhost:8787` ונופל.

חיבור נכון: **Cursor Desktop** או **cursor.com**, לא ה־VM.

`.cursor/mcp.json` עכשיו הוא חיבור ישיר:

```json
{ "mcpServers": { "canva": { "url": "https://mcp.canva.com/mcp" } } }
```

Cursor משתמש ב־`https://www.cursor.com/agents/mcp/oauth/callback` (Web / Cloud Agent)
או `http://localhost:8787/callback` (Desktop).

## 2. צעדים (Desktop)

1. משוך את הענף הזה / פתח את הפרויקט אחרי העדכון.
2. **Customize → MCP** (או Settings → MCP Tools).
3. כבה והדלק את **canva**, או לחץ **Connect**.
4. בדפדפן: היכנס לחשבון Canva של הסטודיו ואשר.
5. חזור לשיחה וכתוב «מחובר».

אל תאשר חלון קופץ חסום. אל תתחבר לחשבון Canva אחר.

מדריך Canva: [AI Connector](https://www.canva.com/help/mcp-agent-setup/).

## 3. תוכנית Canva — חוסם נפוץ

Canva מתירה AI Connector רק ב:

- Canva Pro
- Canva Teams
- Canva Business
- Canva Nonprofit

**חשבון חינם נכשל בחיבור.** זה לא באג ב־HQ.

אם זה צוות: Admin → Controls and Permissions → Third-party integrations → Canva AI Connector חייב להיות דלוק.

## 4. בלי MCP — עדיין עובדים

פתח עיצוב בדפדפן (`packages/vfcanva/OPEN.md`) והדבק את קישור העריכה בשיחה.
`vfigos` מקבל את הקישור. HQ לא שולח.
