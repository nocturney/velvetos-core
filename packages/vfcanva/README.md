# vfcanva — Canva for `@velvets_cloud`

## VF_PUBLICATION_ROUTE_V1 - current publication scope

For Velvet Factory publication tasks, use `packages/vfom/PUBLICATION-PREP-EXECUTION.md` and the `publicationRoute` in `packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json`. Canva/vfcanva are forbidden in this scope; provider notes labelled LEGACY below are not executable routes for VF. Other businesses and non-publication uses are unchanged.
Run `scripts/vf_publication_evidence.py --phase production` before production and `--phase delivery` before review delivery, with the exact manifest/content ID. A file-path or static wiring pass is not creative approval. Preserve source pixels, purposeful editorial richness and independent source/reference/copy/brand/final review evidence.

> LEGACY / provenance only for VF publication; not a provider route: Velvet Factory Instagram visuals are made in **Canva**. This pack is the office
procedure. HQ still does **not** send, boost, or DM. Grok Bot sends.

| | |
|---|---|
| Account | `@velvets_cloud` |
| Seat | צמיחה (growth) |
> LEGACY / provenance only for VF publication; not a provider route: | Live tool | Canva MCP (`https://mcp.canva.com/mcp`) |
> LEGACY / provenance only for VF publication; not a provider route: | Skill | `.cursor/skills/vf-canva-instagram/SKILL.md` |
| Formats | [`FORMATS.json`](FORMATS.json) |
| Ticket | [`jobs/TEMPLATE.md`](jobs/TEMPLATE.md) |

## Pipeline

```
> LEGACY / provenance only for VF publication; not a provider route: vfcopy (caption) → vfcanva (design + edit URL) → vfigos (review / schedule) → Grok Bot (send)
```

> LEGACY / provenance only for VF publication; not a provider route: `vfcovers` and `vfgrowth` write the brief. If Canva MCP is down, render PNG
from [`studio/`](studio/) — do not wait on the marketplace plugin.

> LEGACY / provenance only for VF publication; not a provider route: ## Connect Canva

> LEGACY / provenance only for VF publication; not a provider route: See [`CONNECT.md`](CONNECT.md). Short version: use Cursor Desktop, `url` not `mcp-remote`, and a Canva Pro/Teams/Business/Nonprofit account.

Until OAuth works, render locally:

```bash
> LEGACY / provenance only for VF publication; not a provider route: python3 packages/vfcanva/studio/render.py --format ig_feed_square --hook "הדפסה בתלת־ממד · שדרות"
```

> LEGACY / provenance only for VF publication; not a provider route: Or open [`studio/index.html`](studio/index.html) / [`OPEN.md`](OPEN.md). Do not invent Canva URLs.

## What this pack does

- Open or create a design in the right Instagram size
- Resize one design to post / story / reel cover
> LEGACY / provenance only for VF publication; not a provider route: - Brand-check against a real Canva brand kit (never invent palette)
- Hand an edit URL to `vfigos` for review

## What it does not do

- Send, boost, auto-DM, or move a booked `vfigos` slot
- Invent ₪ prices, Insights, or floor scenes
- Copy Israeli brand files
- Write CTA as WhatsApp / `050-2517000` or bare «שלחו DM» — public CTA is Instagram message only (`PUBLIC_CURRENT_CTA`); auto-DM stays forbidden; BUSINESS_CONTACT_RECORD phone stays off-frame

## Velvet Factory Visual Standard Gate — mandatory (`VF_VISUAL_STANDARD_GATE`)

> LEGACY / provenance only for VF publication; not a provider route: Before any Velvet Factory concept, image selection/edit, Canva operation, cover, carousel, Story still, Reel cover, feed/grid plan, render or publish handoff, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`. Verify Canva asset `MAHVL7PKpvE` and artifact SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897`. Record a PASS binding in the job/manifest/preflight before creative work continues.

> LEGACY / provenance only for VF publication; not a provider route: This gate is **fail-closed**: if the standard is unavailable, mismatched or unverified, stop the creative branch as `visual_standard_unavailable`; never fall back to a generic 3D-print, stock, template, Canva-default or model-default aesthetic. Real source product media remains Product Truth and outranks style; preserve product identity/geometry/material/color and apply the approved reference to composition, surroundings, light, crop, typography and finish.
