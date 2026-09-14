---
name: vf-canva-instagram
description: Create, resize, brand-check, or hand off Velvet Factory Instagram visuals in Canva for @velvets_cloud. Use when the user asks for Instagram content, a post, story, reel cover, carousel, Canva design, or חבילת תוכן ויזואלית.
---

# Canva → Instagram (`@velvets_cloud`)

Live visual tool for the Instagram page. Pack: `packages/vfcanva/`.
After a design exists, hand the edit URL to `vfigos` for review / schedule / **send via tools** (`packages/vfigos/SEND.md`, `constitution/SEND.md`). No auto-DM. No boost.

## Laws

- Hebrew, spoken voice (`vfcopy/VOICE.md` + `VOICE-CHART.md`). CTA is WhatsApp `050-2517000` / איסוף שדרות. Never «שלחו DM».
- Do not invent ₪, Insights, brand hex/fonts, or a floor scene. Write `חסר` / `Can't verify`.
- Do not construct Canva URLs. Use the `edit_url` the MCP returns.
- Before handoff to schedule: `vfgrowth/PREFLIGHT.md` + `CONTENT-RUBRIC.md` (scores + visual evidence + digest). Structure-only checks are not a design pass.
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

## Velvet Factory Visual Standard Gate — mandatory (`VF_VISUAL_STANDARD_GATE`)

Before any Velvet Factory concept, image selection/edit, Canva operation, cover, carousel, Story still, Reel cover, feed/grid plan, render or publish handoff, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`. Verify Canva asset `MAHVL7PKpvE` and artifact SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897`. Record a PASS binding in the job/manifest/preflight before creative work continues.

This gate is **fail-closed**: if the standard is unavailable, mismatched or unverified, stop the creative branch as `visual_standard_unavailable`; never fall back to a generic 3D-print, stock, template, Canva-default or model-default aesthetic. Real source product media remains Product Truth and outranks style; preserve product identity/geometry/material/color and apply the approved reference to composition, surroundings, light, crop, typography and finish.

### Visual-standard evidence contract

A Velvet Factory creative job cannot advance to design handoff, quality_checked, authorized_for_tool_publish, export or publish unless the same job records all of: `visual_standard_gate=PASS`, `visual_standard_canva_asset_id=MAHVL7PKpvE`, `visual_standard_artifact_sha256=df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897`, concrete `product_truth_source_refs`, and the exact-final artifact digest. Missing or mismatched evidence is `visual_standard_unavailable` and blocks the branch.

## Publication-prep execution gate

For Velvet Factory requests that mean prepare/treat/edit content for a potential publication, `packages/vfom/PUBLICATION-PREP-EXECUTION.md` is mandatory. This is an execution task: when usable images and an editing capability exist, selection/caption/planning alone is incomplete. Produce at least one real edited visual artifact, preserve Product Truth, run exact-final visual QA, and only then package copy for owner review. If visual execution is unavailable, fail closed as `visual_execution_unavailable`; never claim ready from raw photos plus copy. Resolve public CTA from current authority; never hardcode the business WhatsApp number into public content from memory.

## Brand asset + public CTA lock

`packages/vfom/BRAND-ASSET-LOCK.md` is mandatory for Velvet Factory public creative. Never ask a generative image model to invent/render a Velvet Factory logo, wordmark or logo-like brand lockup. If an exact owner-approved logo asset is not available to the job, use no logo. If it is available, composite that exact asset deterministically after generation/editing. Base generative prompts must explicitly say `NO LOGO · NO WORDMARK · NO PHONE NUMBER · NO WHATSAPP · NO CONTACT BAR`. Public CTA must resolve from `constitution/PUBLIC_CTA.md`; `050-2517000` is forbidden in public creative/caption unless the owner explicitly requests that exact public use in the current task.

## Creative transformation lock

For Velvet Factory publication-prep, `packages/vfom/CREATIVE-TRANSFORMATION-LOCK.md` is mandatory. Preserve the real product, but do not pass through raw/source photos as the finished creative. At least one review visual — normally the hero/first slide — must show a meaningful approved Velvet treatment around the source-locked product. Default to editing the real source image, not recreating the product from text. Multiple photos do not imply a carousel; if carousel is chosen, slide 1 must be a fully treated hero. `raw_passthrough=true`, an essentially untouched source carousel, or crop/exposure-only work presented as publication-grade is FAIL. Generative edits must explicitly contain NO LOGO, NO WORDMARK, NO PHONE NUMBER, NO WHATSAPP, NO CONTACT BAR, NO GENERATED HEBREW TEXT.

