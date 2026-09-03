# איך מחברים WhatsApp MCP

טלפון הסטודיו הוא **אישי** `050-2517000`, לא WhatsApp Business API. לכן בליבת Core ל-VF: [lharries/whatsapp-mcp](https://github.com/lharries/whatsapp-mcp) על **המק** (גשר Go + QR).

שליחת לקוח ב-VF נשארת **אדם**. MCP = חיפוש שיחות + טיוטה. `send=false`. אין ManyChat / אוטו־DM.

גיבוי בלי MCP: `python3 scripts/vf_office.py convert draft` + `wa.me` ([`vfconvert/WHATSAPP.md`](../vfconvert/WHATSAPP.md)).

לא שמים את הגשר ב־`.cursor/mcp.json` של הריפו (נתיב מוחלט + סשן מקומי).

## Desktop (lharries)

1. מק: Go + `uv`. `git clone https://github.com/lharries/whatsapp-mcp.git` מחוץ לריפו הזה.
2. הרץ את הגשר לפי README שלהם → סרוק QR עם המכשיר של `050-2517000`.
3. הדבק ל־`~/.cursor/mcp.json`:

```json
"whatsapp": {
  "command": "uv",
  "args": [
    "--directory",
    "/ABS/PATH/whatsapp-mcp/whatsapp-mcp-server",
    "run",
    "main.py"
  ]
}
```

4. Reload. אסור לשלוח הצעה / הוכחה בלי לחיצת אדם.

## Infobip (רק מופע שכבר משלם Infobip)

HTTP: `https://mcp.infobip.com/whatsapp`. מפתח / OAuth **לא בגיט**. VF **לא** כורך Infobip — אין חשבון Infobip על המספר הזה. מופע אחר יכול להדליק ב־`mcpBind` ועדיין לשמור שער אדם אם החוקה שלו דורשת.

## Cloud Agent

אין גשר WhatsApp Web בענן. טיוטות: `vf_office.py`. אדם שולח מהטלפון.

## VF `mcpBind`

```
whatsapp.mode = search-and-draft
whatsapp.send = false
```
