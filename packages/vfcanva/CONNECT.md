# חיבור Canva — מה שצריך כדי שזה יעבוד

השרת `https://mcp.canva.com/mcp` חי. הכשל אצלך הוא **טעינת תוסף המרקטפלייס**, לא הרשת.

## מה לעשות עכשיו (בסדר הזה)

1. במסך Canva עם הבאנר הכתום: **Uninstall**.  
   `spawn git ENOENT` = Cursor מחפש `git` כדי לעדכן את התוסף. בלי Git התוסף מת.
2. לפתוח את הריפו הזה (הענף של PR #6). הוא טוען Canva **מהפרויקט**:
   - [`.cursor-plugin/plugin.json`](../../.cursor-plugin/plugin.json)
   - [`.cursor/mcp.json`](../../.cursor/mcp.json) — `type: http`, בלי `npx`, בלי `git`
3. **Developer: Reload Window**.
4. Customize → MCP → `canva` (מהפרויקט) → **Connect** בדפדפן.

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

אל תתקין שוב את תוסף המרקטפלייס. אל תתחבר מתוך ה־VM של Cloud Agent.

## בינתיים — הסטודיו כבר מייצר פריימים

```bash
python3 packages/vfcanva/studio/render.py --format ig_feed_square --hook "הדפסה בתלת־ממד · שדרות"
python3 packages/vfcanva/studio/render.py --format ig_story --hook "הדפסה בתלת־ממד · שדרות" --name ig_story
```

שולחן: [`studio/index.html`](studio/index.html).  
יציאה: `packages/vfcanva/studio/out/*.png` (1080×1080 / 1080×1920).

## אם Connect עדיין נכשל אחרי Uninstall

- Canva AI Connector דורש Pro / Teams / Business / Nonprofit. חינם נכשל.
- צוות: Admin → Third-party integrations → Canva AI Connector דלוק.
- חלון קופץ חסום / חשבון Canva אחר.

מדריך Canva: https://www.canva.com/help/mcp-agent-setup/
