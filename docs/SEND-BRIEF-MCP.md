# שליחת בריף דרך Gmail MCP — פיצול ל־3 קריאות

GrokBot Gmail MCP **לא מצליח** להעביר ~98KB `htmlBody` + JPEG inline ב־**קריאת כלי אחת**.  
סמני `LOAD_FROM_FILE` דולפים לגוף המייל — **אסור** לשים אותם ב־`htmlBody` / `content`.

אין ₪ מומצא. אין דיוור המוני. בריף משרד אל `nocturney@gmail.com` בלבד.

## מסלול מועדף על הראנר — CLI (קובץ, לא ארגומנט MCP)

כשיש `GOOGLE_TOKEN` או ADC על הראנר:

```bash
PYTHONPATH=packages python3 -m vfops.gmail_brief_send \
  --html PATH --images DIR --to EMAIL --subject TEXT
```

- קורא HTML + תמונות מהדיסק (אין גבול ארגומנט MCP)
- בונה MIME `multipart/related` — `filename` = Content-ID (`cid:g001.jpg` ↔ `g001.jpg`)
- שולח **הודעה אחת** ב־Gmail API
- מדפיס את מזהה ההודעה
- בלי טוקן: מדפיס `no token` ויוצא `2`

מודול: `packages/vfops/gmail_brief_send.py`.  
חוזה ויזואלי: `packages/vfbriefux/MAIL.md`.

## עקיפת MCP — 3 צעדים (כשאין CLI / יש MCP בלבד)

אל תקראו `send_message` עם `htmlBody` **וגם** `attachments` באותה קריאה.  
אל תדביקו `LOAD_FROM_FILE` בשום שדה.

### 1) `create_draft` — HTML בלבד

- `to`: `["nocturney@gmail.com"]`
- `subject`: נושא הבריף
- `htmlBody`: תוכן הקובץ ש־`render_mail.py` יצר (תצוגה 3)
- `body`: טקסט חלופי קצר (בלי `LOAD_FROM_FILE`)
- **בלי** `attachments`

שמרו את `id` של הטיוטה (`draftId`).

### 2) `update_draft` — מצורפים בלבד

- `draftId`: מזהה הצעד הקודם
- `attachments`: כריכות inline בלבד
  - `content`: base64 של הקובץ
  - `filename`: ה־cid כמו ב־HTML (למשל `g001.jpg`)
  - `inline`: `true`
  - `mimeType`: `image/jpeg`
- **אל תעבירו** `htmlBody` / `body` / `subject` / `to` — מיזוג: שדה ריק מוחק HTML
- אזהרה: מצורפים **לא** מתמזגים; רשימה ריקה מוחקת מצורפים קיימים. העבירו את **כל** הכריכות כאן

### 3) `send_message` — לפי טיוטה

- `draftId`: אותו מזהה
- **בלי** `htmlBody` / `attachments` / `to` / `subject` — הטיוטה נשלחת כמו שהיא

אחרי שליחה: רושמים את מזהה ההודעה. `#נשלח-מ-HQ`. לא טוענים שעלה לפיד.

## מתי מה

| מצב | מה עושים |
|---|---|
| יש `GOOGLE_TOKEN` / ADC | CLI למעלה |
| יש Gmail MCP, HTML+JPEG גדול מדי לקריאה אחת | 3 הצעדים |
| MCP down | Drive `create_file` + ממשיכים · לא ממציאים פנייה |
| אין טוקן על הראנר | CLI יוצא `2` · לא שולחים מה־VM |

`LOAD_FROM_FILE` אינו פתרון. הוא דולף.
