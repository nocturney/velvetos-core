# וואטסאפ · טיוטה לאדם

מושב: **סטודיו**. שליחה לאדם. MCP בליבה = חיפוש/טיוטה בלבד.
Human-visible text authority: `constitution/VISIBLE_TEXT.md`, mode `customer-message`.

הלקוח מגיע ל־**050-2517000**. אדם שולח. HQ יכול להכין טיוטה + קישור `wa.me` ללחיצה, אבל **הטקסט אינו מוכן להדבקה לפני Visible Text Gate**.

Core מתקין WhatsApp MCP לחיפוש/טיוטה על Desktop: `packages/vfmcp/CONNECT-WHATSAPP.md`. VF `mcpBind.whatsapp.send=false`. בלי Connect / בענן:

```
python3 scripts/vf_office.py jobs add --channel WhatsApp --what "מעמד" --qty 1 --material PLA --phone 0501234567
python3 scripts/vf_office.py convert draft VF-YYYYMMDD-001
python3 scripts/vf_office.py convert draft VF-YYYYMMDD-001 --stage ממתין לסכום
```

הפלט JSON של `vf_office.py` הוא **raw/template draft** עד שעבר את השער:

- `send=false` תמיד
- `text` — candidate בלבד; להעביר דרך `customer-message` Visible Text Gate לפני הצגה כ״מוכן להדבקה״
- `wa_me` — רק אם יש טלפון לקוח; אם הטקסט השתנה אחרי השער יש לבנות מחדש את הקישור מהטקסט המאושר
- `studio_phone`: `050-2517000`

## Visible Text Gate ל־WhatsApp

לפני שהמשרד מציג טיוטה כגוף שהאדם יכול לשלוח:

1. לקרוא את כרטיס/שרשור הלקוח והשלב האמיתי.
2. `vfconvert` מספק חסרים והקשר; `vfsales` אם זו הצעה/מכירה; `vfcost` לכל ₪; `vlicense` רק כשישים.
3. `packages/vfcopy/hq/reader-first-he.md` — לענות למה שהלקוח צריך עכשיו, לא לפתוח בטקסט שירות גנרי.
4. `.cursor/skills/vf-hebrew-copy/SKILL.md` mode `customer-message`.
5. `packages/vfcopy/hq/ai-tells-he.md` + **surface-aware lint** על הטקסט הסופי.
6. factual/constraint pass: מחיר/מועד/סטטוס/איסוף רק אם אומתו.
7. רק אז `visible_text_gate: PASS` והגוף יכול להימסר לאדם להדבקה/שליחה.

מספר WhatsApp בתוך **שיחה פרטית** אינו נפסל רק מפני שהוא אסור כ־CTA ציבורי. `PUBLIC_CURRENT_CTA` חל על public/social ולא על customer-message פרטי.

אין טיוטת **הצעה** בלי סכום מראש צוות. בלי סכום: `--stage ממתין לסכום`.  
כרטיס השדות: `CARD.md`. נתיב: `PATH.md`. כיתוב/קול: `vfcopy` + Visible Text Gate.

אסור: שליחה מ־HQ ב־WhatsApp, `visible_text_gate: PASS` ידני בלי הרצה, Infobip/ManyChat על VF, אוטו־DM, ₪ מומצא.
