# vfcanva workflow

## VF_PUBLICATION_ROUTE_V1 - current publication scope

For Velvet Factory publication tasks, use `packages/vfom/PUBLICATION-PREP-EXECUTION.md` and the `publicationRoute` in `packages/vfom/VISUAL-STANDARD-ENFORCEMENT.json`. Canva/vfcanva are forbidden in this scope; provider notes labelled LEGACY below are not executable routes for VF. Other businesses and non-publication uses are unchanged.
Run `scripts/vf_publication_evidence.py --phase production` before production and `--phase delivery` before review delivery, with the exact manifest/content ID. A file-path or static wiring pass is not creative approval. Preserve source pixels, purposeful editorial richness and independent source/reference/copy/brand/final review evidence.

> LEGACY / provenance only for VF publication; not a provider route: Agent SOP. Follow `.cursor/skills/vf-canva-instagram/SKILL.md` for the live Canva calls.

## 0. Laws

- HQ sends Instagram via tools (`constitution/SEND.md`). No auto-DM. No boost.
- No invented ₪, Insights, brand hex, fonts, or floor scenes.
- CTA is Instagram message (`PUBLIC_CURRENT_CTA` — שלחו לנו הודעה כאן באינסטגרם) · איסוף שדרות. Never WhatsApp / `050-2517000` on public frames. Never auto-DM / bare «שלחו DM».
- Hebrew, spoken voice. Caption comes from `vfcopy` when that pack has a draft.

## 1. Ticket

> LEGACY / provenance only for VF publication; not a provider route: Copy [`jobs/TEMPLATE.md`](jobs/TEMPLATE.md). Required before a Canva call:

- Job / SKU / print name the user gave
- Format id from [`FORMATS.json`](FORMATS.json)
- Caption or `vfcopy` status (`חסר` if none)
- Proof source (Drive file the user named, or `חסר`)

If proof is missing, still design — mark the visual as **טיוטה בלי הוכחת רצפה**.

## 1b. Floor-proof prep (browser-local, optional)

> LEGACY / provenance only for VF publication; not a provider route: When the owner has a real floor/product file that needs light prep **before** Canva:

| Need | Open in browser |
|---|---|
| HEIC → JPG | https://footrue.com/tools/heic-to-jpg |
| Remove background | https://footrue.com/tools/background-remover |
| Compress / resize | https://footrue.com/tools/image-compress · `/tools/image-resize` |

> LEGACY / provenance only for VF publication; not a provider route: Source: [footrue.com](https://footrue.com/) (registered in `vfresearch/LINKS.json`). Human runs these locally; HQ does not upload customer files to cloud utilities from this agent. Not a Canva or brand-kit substitute. See `vfcovers/hq/PLAYBOOK.md` and `packages/vfresearch/sources/2026-09-05-footrue.md`.

> LEGACY / provenance only for VF publication; not a provider route: ## 2. Canva gate

> LEGACY / provenance only for VF publication; not a provider route: 1. Discover the `Canva` MCP namespace.
> LEGACY / provenance only for VF publication; not a provider route: 2. If status is `needsAuth` / empty tools: stop creating. Write `Canva לא מחובר` and the Connect path (Settings → MCP Tools → canva).
> LEGACY / provenance only for VF publication; not a provider route: 3. Do not paste fake `canva.com/design/…` URLs.

## 3. Make the design

Pick one path:

| Ask | Path | Official skill |
|---|---|---|
> LEGACY / provenance only for VF publication; not a provider route: | New post / story / cover from a brief | create or search a starting design, then edit | `canva-edit-design` |
> LEGACY / provenance only for VF publication; not a provider route: | Same art in more IG sizes | `resize-design` with `FORMATS.json` `design_type` | `canva-resize-for-social-media` (IG only unless asked) |
> LEGACY / provenance only for VF publication; not a provider route: | Many SKUs / one template | brand template + autofill | `canva-bulk-create` (Enterprise) |
> LEGACY / provenance only for VF publication; not a provider route: | «האם זה על המותג» | read-only brand check | `canva-brand-check` |
> LEGACY / provenance only for VF publication; not a provider route: | Critique | read-only feedback | `canva-design-feedback` |

Instagram sizes on this desk (do not substitute):

- Feed square **1080×1080**
- Feed portrait **1080×1350**
- Story / reel cover **1080×1920**

Default resize set for `@velvets_cloud`: square + story. Add portrait or carousel only when the brief asks.

## 4. Hand off

Return, in Hebrew:

1. Format + pixels
> LEGACY / provenance only for VF publication; not a provider route: 2. Canva **edit** URL (from the tool, not constructed)
3. What is still `חסר` (proof, brand kit, caption)
4. Next seat: `vfigos` review / schedule — not send

Do not move a booked `vfigos` slot.

## Velvet Factory Visual Standard Gate — mandatory (`VF_VISUAL_STANDARD_GATE`)

> LEGACY / provenance only for VF publication; not a provider route: Before any Velvet Factory concept, image selection/edit, Canva operation, cover, carousel, Story still, Reel cover, feed/grid plan, render or publish handoff, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`. Verify Canva asset `MAHVL7PKpvE` and artifact SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897`. Record a PASS binding in the job/manifest/preflight before creative work continues.

> LEGACY / provenance only for VF publication; not a provider route: This gate is **fail-closed**: if the standard is unavailable, mismatched or unverified, stop the creative branch as `visual_standard_unavailable`; never fall back to a generic 3D-print, stock, template, Canva-default or model-default aesthetic. Real source product media remains Product Truth and outranks style; preserve product identity/geometry/material/color and apply the approved reference to composition, surroundings, light, crop, typography and finish.

## Publication-prep execution gate

For Velvet Factory requests that mean prepare/treat/edit content for a potential publication, `packages/vfom/PUBLICATION-PREP-EXECUTION.md` is mandatory. This is an execution task: when usable images and an editing capability exist, selection/caption/planning alone is incomplete. Produce at least one real edited visual artifact, preserve Product Truth, run exact-final visual QA, and only then package copy for owner review. If visual execution is unavailable, fail closed as `visual_execution_unavailable`; never claim ready from raw photos plus copy. Resolve public CTA from current authority; never hardcode the business WhatsApp number into public content from memory.

## Brand asset + public CTA lock

`packages/vfom/BRAND-ASSET-LOCK.md` is mandatory for Velvet Factory public creative. Never ask a generative image model to invent/render a Velvet Factory logo, wordmark or logo-like brand lockup. If an exact owner-approved logo asset is not available to the job, use no logo. If it is available, composite that exact asset deterministically after generation/editing. Base generative prompts must explicitly say `NO LOGO · NO WORDMARK · NO PHONE NUMBER · NO WHATSAPP · NO CONTACT BAR`. Public CTA must resolve from `constitution/PUBLIC_CTA.md`; `050-2517000` is forbidden in public creative/caption unless the owner explicitly requests that exact public use in the current task.

## Creative transformation lock

For Velvet Factory publication-prep, `packages/vfom/CREATIVE-TRANSFORMATION-LOCK.md` is mandatory. Preserve the real product, but do not pass through raw/source photos as the finished creative. At least one review visual — normally the hero/first slide — must show a meaningful approved Velvet treatment around the source-locked product. Default to editing the real source image, not recreating the product from text. Multiple photos do not imply a carousel; if carousel is chosen, slide 1 must be a fully treated hero. `raw_passthrough=true`, an essentially untouched source carousel, or crop/exposure-only work presented as publication-grade is FAIL. Generative edits must explicitly contain NO LOGO, NO WORDMARK, NO PHONE NUMBER, NO WHATSAPP, NO CONTACT BAR, NO GENERATED HEBREW TEXT.

