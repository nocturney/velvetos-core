# diagram-maker — מפת בריף

מקור מבוקש: [mcpmarket · diagram-maker-visualizer](https://mcpmarket.com/tools/skills/diagram-maker-visualizer)  
גוף חי (failover — mcpmarket חומת Vercel): [openclaw/diagram-maker](https://github.com/openclaw/openclaw/tree/main/skills/diagram-maker) · [agentskill.sh/@openclaw/diagram-maker](https://agentskill.sh/@openclaw/diagram-maker)  
תוכן שנמשך ב־2026-09-05 מ־`agentskill.sh` API (`contentSha` 6195e03). **אין גוף** מ־mcpmarket עצמו.

## מתי

- HQ בונה **גרפיקת חבילת בריף** / wireframe / מפת צינור לצד `MAIL.html`.
- `@ux-architect` מסביר חריצים 01–07 או את הצינור פנייה→…→איסוף בלי פרוזה ארוכה.
- Superdesign / Mobbin חסומים → דיאגרמת SVG עצמאית במקום מסך מומצא.

**לא** מחליף את תצוגה 3 במייל. Gmail לא אמין ל־SVG מוטמע — המייל נשאר טבלאות (`MAIL.html` + `render_mail.py`). הדיאגרמה היא **לוויין**: קובץ HTML עצמאי או ארטיפקט ל־Drive.

## skill → מחולל בריפים

| מושג ב-diagram-maker | אצלנו |
|---|---|
| `clean-svg` | צינור הסטודיו · מחזור בריף · קונסולת פורטלים (פנימית) |
| `architecture-svg` | Core↔instances · כלי HQ · failover (רק כשמבקשים מפת מערכת) |
| `excalidraw` | סקיצה לעריכה מקומית — אופציונלי; לא על Cloud Agent בלי כלי |
| Routing (editable vs polished) | ברירת מחדל לבריף: **clean-svg** עם טוקני `DESIGN.md` |
| 5–9 אלמנטים | חריצי 01–07 או 5 שלבי צינור — לא דאשבורד צפוף |
| `references/svg-template.md` | `hq/diagram-svg-template.html` (כהה/זהב/קרם, RTL) |
| `references/excalidraw-patterns.md` | `hq/references/excalidraw-patterns.md` (עותק דפוסים) |
| Generate `./diagram.html` | `python3 packages/vfbriefux/render_mail.py --diagram pipeline -o …` |

## Routing לבריף

1. צינור / מחזור יומי / חריצים → `clean-svg` (ברירת מחדל).
2. מפת Core/מודולים / כלי MCP → `architecture-svg`.
3. סקיצה משותפת לעריכה → `excalidraw` (מקומי בלבד).
4. לא בטוחים → `clean-svg`. לא שואלים שאלה אם אפשר לבחור לבד.

## חוקי VF (על גבי ה־skill)

- צבעים סמנטיים מ־`DESIGN.md` — לא סגול/קשת/glow.
- תוויות בעברית למוצר; אנגלית OK ב־IDs טכניים.
- RTL ב־`dir` על המעטפת. חיצים נשארים LTR בתוך ה־SVG כשצריך כיוון זרימה שמאל→ימין לקריאות קוד; לצינור העסקי מעדיפים סדר ימין→שמאל או שורה אופקית עם תוויות עבריות.
- בלי ₪ / Insights מומצאים בתוויות. חסר מקור → «אין ספירה».
- CTA אם מופיע: WhatsApp `050-2517000` / איסוף שדרות — לא «שלחו DM».
- בלי התקנת `npx` / OpenClaw / MCP חדש על Cloud Agent. דפוסים בלבד.

## מחולל

```bash
# צינור קנוני (5 שלבים) — HTML עצמאי
python3 packages/vfbriefux/render_mail.py --diagram pipeline -o /tmp/vf-pipeline.html

# מחזור חריצי בריף 01–07
python3 packages/vfbriefux/render_mail.py --diagram slots -o /tmp/vf-brief-slots.html

# בדיקה
python3 packages/vfbriefux/render_mail.py --check
```

מייל חי נשאר:

```bash
python3 packages/vfbriefux/render_mail.py packages/vfops/hq/brief-YYYY-MM-DD.json -o /tmp/brief.html
```

## מה לא הוטמע

- התקנת skill / OpenClaw runtime / Excalidraw MCP על Cloud Agent
- החלפת `MAIL.html` ב־SVG
- דיאגרמות מחיר או Insights בלי מקור
- פק חדש `vfdiagram`

## סנסור

אחרי שינוי קטלוג/מפה: `python3 scripts/check-all.py`.  
`render_mail.py --check` מאמת גם את תבניות הדיאגרמה.
