# וואטסאפ · טיוטה לאדם

מושב: **סטודיו**. לא MCP וואטסאפ. לא שליחה מ־HQ.

הלקוח מגיע ל־**050-2517000**. אדם שולח. HQ כותב טיוטה + קישור `wa.me` ללחיצה.

```
python3 scripts/vf_office.py jobs add --channel WhatsApp --what "מעמד" --qty 1 --material PLA --phone 0501234567
python3 scripts/vf_office.py convert draft VF-YYYYMMDD-001
python3 scripts/vf_office.py convert draft VF-YYYYMMDD-001 --stage ממתין לסכום
```

הפלט JSON:

- `send=false` תמיד
- `text` — להדבקה במקלדת
- `wa_me` — רק אם יש טלפון לקוח (נפתח אצל האדם במכשיר)
- `studio_phone`: `050-2517000`

אין טיוטת **הצעה** בלי סכום מראש צוות. בלי סכום: `--stage ממתין לסכום`.  
כרטיס השדות: `CARD.md`. נתיב: `PATH.md`. כיתוב דלפק: `vfcopy/DESK.md`.

אסור: WhatsApp Business MCP, Infobip, ManyChat, אוטו־DM, ₪ מומצא.
