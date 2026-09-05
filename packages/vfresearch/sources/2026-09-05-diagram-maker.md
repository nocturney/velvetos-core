# Diagram Maker → vfbriefux · 2026-09-05

מושב: `@ux-architect` + `@studio-operations` · Asia/Jerusalem  
מקור מבוקש: https://mcpmarket.com/tools/skills/diagram-maker-visualizer  
Failover: «אין גוף» מ־mcpmarket (Vercel checkpoint) → [agentskill.sh/@openclaw/diagram-maker](https://agentskill.sh/@openclaw/diagram-maker) + `github.com/openclaw/openclaw/skills/diagram-maker` (`contentSha` 6195e03).

## מה הוטמע

| קובץ | תפקיד |
|---|---|
| `packages/vfbriefux/hq/DIAGRAM-MAKER.md` | מפת skill → מחולל בריפים |
| `packages/vfbriefux/hq/diagram-svg-template.html` | מעטפת SVG עם טוקני DESIGN.md |
| `packages/vfbriefux/hq/references/excalidraw-patterns.md` | דפוסי Excalidraw (אופציונלי מקומי) |
| `packages/vfbriefux/render_mail.py --diagram` | `pipeline` / `slots` לוויינים |

## חוקים שנשמרו

- לא פק חדש
- לא `npx` / OpenClaw על Cloud Agent
- מייל חי = תצוגה 3 טבלאות; דיאגרמה = לוויין בלבד
- בלי ₪ / Insights מומצאים בתוויות

## בדיקה

```bash
python3 packages/vfbriefux/render_mail.py --check
python3 packages/vfbriefux/render_mail.py --diagram pipeline -o /tmp/vf-pipeline.html
```
