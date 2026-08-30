# vfcanva — Canva for `@velvets_cloud`

Velvet Factory Instagram visuals are made in **Canva**. This pack is the office
procedure. HQ still does **not** send, boost, or DM. Grok Bot sends.

| | |
|---|---|
| Account | `@velvets_cloud` |
| Seat | צמיחה (growth) |
| Live tool | Canva MCP (`https://mcp.canva.com/mcp`) |
| Skill | `.cursor/skills/vf-canva-instagram/SKILL.md` |
| Formats | [`FORMATS.json`](FORMATS.json) |
| Ticket | [`jobs/TEMPLATE.md`](jobs/TEMPLATE.md) |

## Pipeline

```
vfcopy (caption) → vfcanva (design + edit URL) → vfigos (review / schedule) → Grok Bot (send)
```

`vfcovers` and `vfgrowth` write the brief. If Canva MCP is down, render PNG
from [`studio/`](studio/) — do not wait on the marketplace plugin.

## Connect Canva

See [`CONNECT.md`](CONNECT.md). Short version: use Cursor Desktop, `url` not `mcp-remote`, and a Canva Pro/Teams/Business/Nonprofit account.

Until OAuth works, render locally:

```bash
python3 packages/vfcanva/studio/render.py --format ig_feed_square --hook "הדפסה בתלת־ממד · שדרות"
```

Or open [`studio/index.html`](studio/index.html) / [`OPEN.md`](OPEN.md). Do not invent Canva URLs.

## What this pack does

- Open or create a design in the right Instagram size
- Resize one design to post / story / reel cover
- Brand-check against a real Canva brand kit (never invent palette)
- Hand an edit URL to `vfigos` for review

## What it does not do

- Send, boost, auto-DM, or move a booked `vfigos` slot
- Invent ₪ prices, Insights, or floor scenes
- Copy Israeli brand files
- Write CTA as «שלחו DM» — WhatsApp `050-2517000` / איסוף שדרות only
