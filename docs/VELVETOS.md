# VelvetOS

**VelvetOS** = מערכת ניהול עסק + עמודי סושיאל אוטונומיים על Cursor.  
המשרד החי הראשון הוא **Velvet Factory** (הדפסות תלת־ממד, שדרות) — נשאר ה־tenant הפעיל עד שראש צוות מחליף.

## למה

עברנו על הרבה סוכנים/מערכות; רובן נפסלו כי לא התאימו לסטודיו הספציפי. VelvetOS מפריד:

1. **Kernel** — חוקים, 5 מושבים, פקים, שליחה דרך כלים, רתמה  
2. **Tenant** — זהות, צינור בעברית, ערוצי IG (1..N), אספקה, נעילות אנכיות  

כך אפשר לנסות אנכיים אחרים **בלי לשבור** את השימוש הנוכחי.

## מבנה

| נתיב | תפקיד |
|---|---|
| `packages/velvetos/KERNEL.md` | מה המוצר |
| `packages/velvetos/ACTIVE.json` | מי פעיל |
| `packages/velvetos/tenants/*.json` | פרופילים |
| `packages/velvetos/tenants/_examples/` | טיוטות בלבד |
| `packages/velvetos/PIPELINE.md` | 5 שלבים קנוניים |
| `packages/velvetos/CHANNELS.md` | multi-IG |
| `scripts/velvetos.py` | active / list / show |
| `scripts/check-velvetos.py` | סנסור |

## תאימות VF

כל עוד `activeTenant = velvet-factory`:

- `constitution/STUDIO.md` ו־`.cursor/vf-desk.json` → `studio` הם המקור החי  
- צינור: פנייה → שיחה → הצעה → הדפסה → איסוף  
- IG: `@velvets_cloud`  
- CTA: וואטסאפ `050-2517000` / איסוף שדרות  

הסנסור נכשל אם פרופיל ה־tenant סותר את אלה.

## דוגמאות יעד (לא פעילים)

1. **nails-tattoos** — appointment + שני עמודי Instagram  
2. **psychiatrist-legal** — document fulfill + נעילות PHI / בלי ייעוץ קליני מ־HQ  

## הפעלה לעסק חדש

ראו `packages/velvetos/EMBED.md`. לא פק חדש לכל עסק. לא ACTIVE בלי ראש צוות.

## סנסורים

```bash
python3 scripts/check-velvetos.py
python3 scripts/check-all.py
```
