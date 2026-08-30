# Canva — כלי תוכן לאינסטגרם

Canva is the live visual tool for **`@velvets_cloud`**.  
החבילה: [`packages/vfcanva/`](../packages/vfcanva/).  
ה־skill: [`.cursor/skills/vf-canva-instagram/SKILL.md`](../.cursor/skills/vf-canva-instagram/SKILL.md).  
מפת מכונה: [`.cursor/vf-canva.json`](../.cursor/vf-canva.json).

HQ עדיין **לא** שולח אינסטגרם. גרוק שולח.

## חיבור

1. בקובץ הפרויקט רשום שרת MCP: [`.cursor/mcp.json`](../.cursor/mcp.json) → `https://mcp.canva.com/mcp`.
2. ב־Cursor: **Settings → MCP Tools → canva → Connect**, ואז כניסה לחשבון Canva.
3. בדיקה: `python3 scripts/check-vf-canva.py`  
   מצופה: `OK vfcanva formats=5 skill+rule+mcp`.

בלי OAuth אין יצירת עיצוב. לכתוב `Canva לא מחובר` — לא לקשר קישור מזויף.

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
