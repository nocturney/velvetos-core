# Canva — כלי תוכן לאינסטגרם

Canva is the live visual tool for **`@velvets_cloud`**.  
החבילה: [`packages/vfcanva/`](../packages/vfcanva/).  
ה־skill: [`.cursor/skills/vf-canva-instagram/SKILL.md`](../.cursor/skills/vf-canva-instagram/SKILL.md).  
מפת מכונה: [`.cursor/vf-canva.json`](../.cursor/vf-canva.json).

HQ עדיין **לא** שולח אינסטגרם. גרוק שולח.

## חיבור

פירוט ותקלות: [`packages/vfcanva/CONNECT.md`](../packages/vfcanva/CONNECT.md).

1. [`.cursor/mcp.json`](../.cursor/mcp.json) חייב להיות `{ "url": "https://mcp.canva.com/mcp" }` — **לא** `mcp-remote`.
2. אם מופיע `spawn git ENOENT`: Uninstall לתוסף המרקטפלייס, להישאר עם ה־URL בפרויקט. או להתקין Git ולהפעיל מחדש את Cursor.
3. צריך תוכנית Canva Pro / Teams / Business / Nonprofit. חינם נכשל.
4. בדיקה: `python3 scripts/check-vf-canva.py` → `OK vfcanva formats=5 skill+rule+mcp`.

בלי OAuth: `python3 packages/vfcanva/studio/render.py` או [`studio/index.html`](../packages/vfcanva/studio/index.html). לא להמציא URL.

אם מופיע `spawn git ENOENT`: **Uninstall** לתוסף המרקטפלייס. הפרויקט טוען Canva מ־`.cursor-plugin` + `.cursor/mcp.json` (`type: http`).

## מה מבקשים

| בקשה | מה קורה |
|---|---|
| פוסט / סטורי / קאבר ריל | Canva בגודל מ־`FORMATS.json`, קישור עריכה |
| אותה אמנות בעוד פורמט | `resize-design` (ברירת מחדל: מרובע + סטורי) |
| כרטיסי SKU מתבנית | `autofill` — דורש Canva Enterprise |
| האם זה על המותג | `brand-check` מול קיט אמיתי בלבד |

## צינור

```
vfcopy → vfcanva (Canva) → vfigos (סקירה/שיבוץ) → Grok Bot
```

CTA: וואטסאפ `050-2517000` / איסוף שדרות. לא «שלחו DM».
