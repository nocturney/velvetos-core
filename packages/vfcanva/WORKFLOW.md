# vfcanva workflow

Agent SOP. Follow `.cursor/skills/vf-canva-instagram/SKILL.md` for the live Canva calls.

## 0. Laws

- HQ sends Instagram via tools (`constitution/SEND.md`). No auto-DM. No boost.
- No invented ₪, Insights, brand hex, fonts, or floor scenes.
- CTA is WhatsApp `050-2517000` / איסוף שדרות. Never «שלחו DM».
- Hebrew, spoken voice. Caption comes from `vfcopy` when that pack has a draft.

## 1. Ticket

Copy [`jobs/TEMPLATE.md`](jobs/TEMPLATE.md). Required before a Canva call:

- Job / SKU / print name the user gave
- Format id from [`FORMATS.json`](FORMATS.json)
- Caption or `vfcopy` status (`חסר` if none)
- Proof source (Drive file the user named, or `חסר`)

If proof is missing, still design — mark the visual as **טיוטה בלי הוכחת רצפה**.

## 1b. Floor-proof prep (browser-local, optional)

When the owner has a real floor/product file that needs light prep **before** Canva:

| Need | Open in browser |
|---|---|
| HEIC → JPG | https://footrue.com/tools/heic-to-jpg |
| Remove background | https://footrue.com/tools/background-remover |
| Compress / resize | https://footrue.com/tools/image-compress · `/tools/image-resize` |

Source: [footrue.com](https://footrue.com/) (registered in `vfresearch/LINKS.json`). Human runs these locally; HQ does not upload customer files to cloud utilities from this agent. Not a Canva or brand-kit substitute. See `vfcovers/hq/PLAYBOOK.md` and `packages/vfresearch/sources/2026-09-05-footrue.md`.

## 2. Canva gate

1. Discover the `Canva` MCP namespace.
2. If status is `needsAuth` / empty tools: stop creating. Write `Canva לא מחובר` and the Connect path (Settings → MCP Tools → canva).
3. Do not paste fake `canva.com/design/…` URLs.

## 3. Make the design

Pick one path:

| Ask | Path | Official skill |
|---|---|---|
| New post / story / cover from a brief | create or search a starting design, then edit | `canva-edit-design` |
| Same art in more IG sizes | `resize-design` with `FORMATS.json` `design_type` | `canva-resize-for-social-media` (IG only unless asked) |
| Many SKUs / one template | brand template + autofill | `canva-bulk-create` (Enterprise) |
| «האם זה על המותג» | read-only brand check | `canva-brand-check` |
| Critique | read-only feedback | `canva-design-feedback` |

Instagram sizes on this desk (do not substitute):

- Feed square **1080×1080**
- Feed portrait **1080×1350**
- Story / reel cover **1080×1920**

Default resize set for `@velvets_cloud`: square + story. Add portrait or carousel only when the brief asks.

## 4. Hand off

Return, in Hebrew:

1. Format + pixels
2. Canva **edit** URL (from the tool, not constructed)
3. What is still `חסר` (proof, brand kit, caption)
4. Next seat: `vfigos` review / schedule — not send

Do not move a booked `vfigos` slot.
