---
name: vf-canva-instagram
description: Create, resize, brand-check, or hand off Velvet Factory Instagram visuals in Canva for @velvets_cloud. Use when the user asks for Instagram content, a post, story, reel cover, carousel, Canva design, or חבילת תוכן ויזואלית.
---

# Canva → Instagram (`@velvets_cloud`)

Live visual tool for the Instagram page. Pack: `packages/vfcanva/`.
After a design exists, hand the edit URL to `vfigos` for review / schedule / **send via tools** (`packages/vfigos/SEND.md`, `constitution/SEND.md`). No auto-DM. No boost.

## Laws

- Hebrew, spoken voice. CTA is WhatsApp `050-2517000` / איסוף שדרות. Never «שלחו DM».
- Do not invent ₪, Insights, brand hex/fonts, or a floor scene. Write `חסר` / `Can't verify`.
- Do not construct Canva URLs. Use the `edit_url` the MCP returns.
- Superdesign is fallback only when Canva MCP is down. Prefer `packages/vfcanva/studio/render.py` for a real PNG this HQ can produce without OAuth.

## Step 1 — Ticket

Fill `packages/vfcanva/jobs/TEMPLATE.md` in the reply (do not invent a job name). Need:

1. Job / SKU / print the user named
2. Format id from `packages/vfcanva/FORMATS.json`
3. Caption from `vfcopy`, or `חסר`
4. Proof the user named, or `חסר`

Default format: `ig_feed_square` (1080×1080). Story / reel cover = 1080×1920. Portrait = 1080×1350.

## Step 2 — Canva MCP gate

Inspect the `Canva` MCP namespace (tools + auth status).

- **`needsAuth` or no tools:** do not fake a design. Point to `packages/vfcanva/CONNECT.md`. Usual causes: **`spawn git ENOENT`** (marketplace plugin — Uninstall it, keep project `url` MCP), connecting from the cloud VM, Canva **Free**, or a team admin who disabled third-party integrations. Fallback: `packages/vfcanva/OPEN.md`.
- **Tools present:** continue. Use exact tool names from the live schema (discover before each call).

Official Canva skills (read the matching file before mutating a design):

- Edit / create on an existing design → `canva-edit-design` (transaction → operate → commit only after approval)
- Resize → `canva-resize-for-social-media` using the `design_type` objects in `FORMATS.json`
- Bulk SKU cards → `canva-bulk-create` (Enterprise autofill)
- On-brand? → `canva-brand-check` (never invent a kit)
- Critique → `canva-design-feedback`

## Step 3 — Make or reuse

1. If the user gave a design id (`D…`) or `canva.com/design/…` / `canva.link/…`, resolve that id. Do not search.
2. Else `search-designs` with the job name the user gave. If several match, list titles and wait.
3. New work: start from a searched studio design or a brand template. Prefer a real Velvet Factory / `@velvets_cloud` design over a blank generic.
4. Sizes must match `FORMATS.json`. For a content pack, resize in parallel to **square + story** unless the user named other formats. Story and reel cover share 1080×1920 — say so.
5. Keep hook text out of story chrome (`safeZone` in `FORMATS.json`).

## Step 4 — Copy on the art

On-film text is short Hebrew. Caption stays with `vfcopy` / `vfigos`, not stuffed into the image.

Allowed on the frame: hook, job name the user gave, WhatsApp / איסוף שדרות.
Forbidden on the frame: invented ₪, fake Insights, «שלחו DM», copied Israeli brand marks.

## Step 5 — Hand off

Reply with:

```
פורמט: <id> <width>×<height>
Canva: <edit_url>
חסר: <proof / brand kit / caption / none>
הבא: vfigos — סקירה ושיבוץ בלבד. גרוק שולח.
```

Do not move a booked `vfigos` slot. Do not export-and-post from HQ.
