# למה Canva לא מתחבר — ומה לעשות

בודק בסוכן הזה (2026-08-30): השרת `https://mcp.canva.com/mcp` חי (401 בלי טוקן — תקין).

## 0. השגיאה במסך: `Error loading plugin` / `spawn git ENOENT`

זה **לא** כשל OAuth של Canva. Cursor מנסה להריץ `git` כדי לטעון את תוסף Canva מהמרקטפלייס, ו־Git לא נמצא ב־PATH של המחשב.

הכלים (`canva-edit-design` וכו') מופיעים ברשימה, אבל התוסף לא נטען — לכן אין Connect אמיתי.

**תיקון מועדף (בלי Git):**

1. באותו מסך: **Uninstall** על תוסף Canva מהמרקטפלייס.
2. ודא שבפרויקט יש [`.cursor/mcp.json`](../../.cursor/mcp.json) עם URL בלבד (בלי `npx` / `git`):

```json
{ "mcpServers": { "canva": { "url": "https://mcp.canva.com/mcp" } } }
```

3. Customize → MCP → רענון. אמור להופיע `canva` כשרת מרוחק.
4. **Connect** בדפדפן, כניסה לחשבון Canva, אישור.

**אם רוצים להשאיר את התוסף מהמרקטפלייס:**

1. התקן [Git](https://git-scm.com/downloads) וסמן Add to PATH.
2. סגור לגמרי את Cursor ופתח שוב.
3. בטרמינל מחוץ ל־Cursor: `git --version` חייב להצליח.
4. חזור למסך Canva — הבאנר הכתום אמור להיעלם, ואז Connect.

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
