# Velvet Factory — Reel / Video Route

Status: **Project source extension for Revision 6.6.11**
Base creative authority: **Revision 6.6.9 / VF-PROJECT-6.6.9-NATIVE-PRODUCT-EDIT-ROUTING**.
Previous Reel extension: **6.6.10**.
Canonical production route for "תכין ריל/וידאו ל<מוצר>": **Adobe Photoshop + After Effects on Chris**.
This route prepares an OWNER REVIEW candidate and never auto-publishes.

Policy bindings: `policy_id: project.request.preflight` governs request/tool preflight; `policy_id: cost.recurring.new` keeps the route on existing/zero-new-recurring-cost capability unless separately approved; `policy_id: instagram.publish` remains a separate publication gate and is never authorized by Reel preparation.

## 1. Product Truth is absolute

Product pixels come only from verified real photos/video or a deterministic render of the real print file. Generative video models never render, replace, repair, re-angle or stylize the product and never render Hebrew text.

For photographed products, preserve silhouette, proportions, parts/openings, surface identity, base colour/finish and critical details. Retouch may affect only environment, light/shadow integration, composition, depth of field, crop and placement. A missing product view is a missing input, not permission to synthesize it.

For a 3D turntable, the real print file is the geometry source. The render illustrates that file only; it does not prove a photographed event, material, dimensions, durability or print success.

## 2. Trigger and fixed workflow

The canonical Hebrew trigger is:

`תכין ריל/וידאו ל<מוצר>`

On that request:

1. Find the product's published rich still and use it as the primary visual reference.
2. Read its on-image copy as the overlay-copy source unless Christian explicitly supplies replacement copy.
3. Ask for original product photos: **front, 3/4, side, back, close-up**. A short phone video is optional.
4. Produce one text-free 1080x1920 scene per verified angle, matching the published still's room, light, retouch and colour grade.
5. Produce an identical **EMPTY plate** for each scene: same camera/frame/environment/light with the product absent.
6. Build the deterministic job package under `packages/vfom/jobs/VF-R0xx/`.
7. Run one Chris command: `py -3.14 scripts\vf_ae_reel.py --job packages\vfom\jobs\VF-R0xx`.
8. Run Reel QA against the published reference and hand the rendered candidate to Christian for review.

Do not stop at a storyboard or raw source when the required inputs exist. If required angles/scenes are missing, fail closed with exact `neededInputs`.

## 3. Exact scene-generation prompt template

Use only the current-task real product photo as the identity source. References are visual guidance, not product inputs.

> Create a vertical 1080x1920 text-free editorial scene for Velvet Factory using the supplied real product photo as the sole physical identity source. Preserve the product exactly: silhouette, proportions, openings/parts, eyes/horns/base/tail where present, surface identity, base colour/finish and every critical detail. Do not redraw, replace, repair, add parts, remove parts, invent a new angle or change geometry. Match the published rich-still reference only for room/environment, warm side/window light, surface, depth, colour grade, composition hierarchy and retouch vocabulary. The product must remain large and dominant, naturally grounded with believable contact shadow, with useful negative space for later Hebrew typography. No text, icons, cards, logo, watermark or claims. Retouch may change only lighting, shadow integration, background/environment, crop, depth of field and placement. Output 1080x1920.

For the paired empty plate:

> From the approved scene, create the identical EMPTY plate: same 1080x1920 frame, camera height/angle, crop, room, surface, props, light direction/intensity, depth of field and colour grade, but remove only the product and its contact shadow. Do not change any other composition element. No product, text, icons, cards, logo or watermark.

A scene pair is valid only when the plate and product scene are frame-compatible. Do not use a style reference or logo file as a Native identity input.

## 4. Job package contract

Every job lives at `packages/vfom/jobs/VF-R0xx/` and contains at minimum:

- `variables.json` — headline lines, subhead, accent, icon labels, detail labels, CTA and explicit font/logo refs;
- `storyboard.json` — 12–15 second beat timing and scene order;
- `manifest.json` — source/scene/plate refs plus SHA-256 bindings;
- `prep-status.json` — `needs_input` or `needs_review`, never publish authorization.

Canonical schema: `packages/vfom/adobe/REEL-JOB.schema.json`.

If a source has not arrived, its path/hash stays an explicit empty string and the missing item appears in `neededInputs`. Never invent a SHA-256. `publicationAuthorized` is always false in this route.

Brand refs come from `packages/vfbrand/brand-tokens.json`:
- Rubik 700: Hebrew headline;
- Rubik 600: Hebrew subhead/labels;
- Cinzel: Latin display/text only;
- exact overlay logo: `packages/vfbrand/assets/logo/velvet-factory-logo-gold-full-lockup-traced.svg`;
- CTA: `reel.endCardCta`.

## 5. Photoshop isolation

Canonical script: `packages/vfom/adobe/photoshop-product-layer.jsx`.

For each scene:
1. open the scene PNG;
2. run Photoshop **Select Subject**;
3. refine the selection edge deterministically with small smooth/feather operations;
4. clear the non-product area on a duplicate pixel layer;
5. export a full-canvas product-layer PNG with alpha.

No Firefly and no Generative Fill. Content-Aware Fill is not used automatically; if Christian explicitly requests a tiny manual edge-gap repair, it may be used only outside the verified product geometry.

The resulting product-layer retains the scene's exact registration so After Effects can place it over the paired EMPTY plate without a position guess.

## 6. After Effects build

Canonical script: `packages/vfom/adobe/build-reel.jsx`.

Canonical orchestrator: `scripts/vf_ae_reel.py`.

Build:
- 1080x1920 portrait;
- 30fps;
- 12–15 seconds;
- paired plate/product layers at different Z values for 2.5D separation;
- slow dolly push-in and gentle parallax;
- camera depth of field plus rack focus;
- soft sunlight sweep over the scene;
- optional subtle dust with built-in **CC Particle World** only;
- restrained cuts/crossfades between verified angle scenes;
- no third-party plugins.

Typography is deterministic:
- explicit Hebrew RTL;
- Rubik 700/600 from committed font assets;
- Cinzel for Latin only;
- line-by-line masked reveal;
- thin accent-rule wipe;
- no bouncy pop-up cards.

Instagram safety:
- no text inside the top 150px;
- no text inside the bottom 20% of the frame;
- reserve the right-edge button strip;
- overlays never cross the protected product silhouette.

The end card uses the exact gold SVG logo and token CTA. The logo is resized only; it is never redrawn or recoloured.

## 7. Audio

Every final Reel has a documented `audioStrategy`: source, music, SFX, source+music, source+SFX, or explicit intentional silence. Never invent a track name or rights status. Audio remains exact-final QA work.

## 8. Render host and one-command route

Chris host:
- repo: `D:\Velvet\Repos\velvetos-core`;
- VelvetOS runtime/artifacts: `D:\Velvet\Runtime\VelvetOS\`;
- Photoshop 2026 expected: v27.7 under Program Files;
- After Effects 2026 expected: v26.3 under Program Files;
- `aerender.exe`: After Effects Support Files;
- ffmpeg/ffprobe: `D:\Velvet\Tools\Shared\ffmpeg\current\bin`.

Everything controlled by VelvetOS during the render is written under `D:\Velvet\Runtime\VelvetOS\`. Adobe may use its normal installed-app/profile state, but the pipeline does not create VelvetOS artifacts on C:.

From the repo root:

```bat
py -3.14 scripts\vf_ae_reel.py --job packages\vfom\jobs\VF-R0xx
```

The orchestrator validates the job, verifies source hashes, registers the committed fonts for the Windows session, runs Photoshop, runs the AE build, calls `aerender`, transcodes with ffmpeg when needed, verifies 1080x1920/30fps with ffprobe, and writes a receipt with hashes.

The first owl package remains `needs_input`; its structural check is:

```bat
py -3.14 scripts\vf_ae_reel.py --job packages\vfom\jobs\VF-R006 --validate-only
```

## 9. Supported Reel types

The Adobe route is canonical, while these semantic types remain valid:
- `ANIMATED_RICH_STILL`
- `PRINTER_TO_SHELF`
- `REAL_PRINT_FILE_TURNTABLE`
- `RICH_STYLE_V2`

`REAL_PRINT_FILE_TURNTABLE` may call `scripts/vf_turntable.py` and feed its deterministic MP4 into AE as an optional additional layer. The print file remains the only turntable geometry source.

HyperFrames remains a compatibility/deterministic backend and its five templates remain tracked:
`hook-card.html`, `chips.html`, `detail-inset.html`, `end-card.html`, `rich-still-reel.html`.

The eight historical motion IDs stay documented:
`HEADLINE_REVEAL`, `ACCENT_RULE_WIPE`, `CHIP_SEQUENCE`, `INSET_POP`,
`VELVET_HARD_CUT`, `VELVET_MACRO_PUNCH`, `VELVET_MATERIAL_LABEL`, `VELVET_FINAL_STAMP`.

## 10. HyperFrames regression contract

PR #422 regressions are explicitly guarded:
- the `<html>` tag in all five templates must **not** have `dir="rtl"`;
- text containers keep `dir="rtl"`;
- `velvet-reel.js` resolves `packages/...` from repo root;
- brand tokens, logo and committed fonts never use `../` repo escapes;
- `velvet-reel.css` contains no `../../vfbrand` font rules.

## 11. QA order

Run on the exact artifact:
1. **PREFLIGHT** — sources, claims, copy and visual-standard binding;
2. **EDIT-GATE** — real edit delta, Product Truth, source/final evidence and audio strategy;
3. **visual-standard** — warm editorial scene, product dominance, hierarchy, RTL and mobile readability;
4. **reference match** — compare against the product's published rich still;
5. **exact-final inspection** — first 2s, cuts, midpoint(s), last 2s/end card, full-size cover and mobile/grid crop.

Technical checks include ffprobe 1080x1920/30fps, duration 12–15s and SHA-256 receipt bindings.

A render receipt is technical evidence only. It is not Identity PASS, Creative PASS, MASTER approval or publish authorization.

## 12. Handoff state

A complete handoff includes the job package, scene pairs, product-layer PNGs, AEP, rendered MP4, ffprobe result and receipt. Before owner review the state is `needs_review`. The first job stays `needs_input` until required scene pairs exist.

`ready_for_publish` remains a handoff state only. No Instagram publishing, scheduling, post edit or other live write occurs from this route.

## 13. Drift sensors

`packages/vfom/REEL-ROUTE-CONTRACT.json` binds this document, Project revision, legacy template inventory and the Adobe schema/JSX/Python implementation.

`scripts/check-reel-route-sync.py` fails when Project/route/Adobe bindings drift.
`scripts/check-reel-templates.py` statically checks HyperFrames path/RTL regressions, Adobe JSX wiring, font/logo/CTA bindings, the job schema and VF-R006 copy.

CI performs static/schema checks only and never launches Adobe or renders production video.
