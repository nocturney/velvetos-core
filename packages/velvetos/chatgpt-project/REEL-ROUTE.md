# Velvet Factory — Reel / Video Route

Status: **Project source extension for Revision 6.6.10**
Base creative authority: **Revision 6.6.9 / VF-PROJECT-6.6.9-NATIVE-PRODUCT-EDIT-ROUTING**.
Scope: prepare a complete review-ready Reel/video package. This route never auto-publishes.

## 1. Product Truth stays absolute

Product pixels come from verified real photos/video or from a deterministic render of the real print file. A generative video model never renders, replaces, repairs, re-angles or stylizes the product. A generative model never renders Hebrew text.

For photographed products, preserve the 6.6.9 Native Product Edit law: NATIVE_PRODUCT_EDIT may change scene, lighting, composition, depth of field, crop and placement around the real product; Identity Gate and Creative Gate remain separate. SOURCE_COMPOSITE remains the bounded fallback. Reel work does not weaken either gate.

For a 3D turntable, the real print file is the geometry source. The render illustrates that file; it does not prove a photographed physical event, print success, material, dimensions, durability or customer use unless separate evidence supports the claim.
## 2. Supported Reel types

### A. Animated rich still — `ANIMATED_RICH_STILL`
Use a text-free, source-faithful rich still master. Motion grammar:
1. slow camera push on the real hero;
2. HEADLINE_REVEAL;
3. ACCENT_RULE_WIPE;
4. CHIP_SEQUENCE;
5. INSET_POP when a verified inset adds information;
6. at least one verified real-motion beat;
7. deterministic end card.

A Ken Burns move on one still by itself is **not** a Reel.

### B. Printer-to-shelf — `PRINTER_TO_SHELF`
Start with a verified printer timelapse/process clip, cut to useful beats, and finish on the styled still/cover. The printer clip proves only what is actually visible.

### C. 3D turntable beat — `REAL_PRINT_FILE_TURNTABLE`
Use Blender with the real print file, warm-interior lighting and colour matched to verified photos of the printed product when available. Render a loopable 6–8 second 9:16 beat and return it to the same HyperFrames/QA pipeline.

### D. Rich-style v2 — `RICH_STYLE_V2`
Upgrade an existing ready package without changing its truth claims: current rich cover/hook, editorial motion, verified detail treatment, current audio gate and current end card. Preserve old receipts as history and create new exact-final receipts for v2.
## 3. Inputs and source locations

Resolve before production:
- product truth and still route: `packages/velvetos/chatgpt-project/` plus the active Project 6.6.9 bundle;
- real media: `packages/vfmedia/catalog.json`, Media Vault refs, or exact current-task source files;
- current visual language: `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `VISUAL-DNA.json`, `HYPERFRAMES-FRAME.md`;
- brand assets: `packages/vfbrand/brand-tokens.json`;
- video/edit policy: `VIDEO-TOOLCHAIN.md/.json`, `MOTION-PRESETS.md`, `HYPERFRAMES-BACKEND.md/.json`, `packages/vfgrowth/EDIT-GATE.md`, `packages/vfgrowth/PREFLIGHT.md`;
- reel candidates: `scripts/vf_reel_candidates.py`;
- existing packages: `packages/vfom/jobs/VF-R00x/`;
- render host: `packages/vfmcp/RENDER-HOSTS.json`.

Missing media or a missing print file is a needed input, never permission to fabricate it.
## 4. Text-free master and layer separation

A still-driven Reel starts from a **text-free master**. Keep the composition separable into:
- `product_layer`: real product pixels, or deterministic pixels from the real print file for a turntable;
- `background_plate`: scene pixels around the product;
- `editorial_overlay`: deterministic Hebrew, accent rule, chips, inset frame, CTA and logo;
- `audio`: source sound / verified music / authored SFX under office policy.

For Native edits, the candidate guard protects final overlays from touching product pixels; it is not segmentation proof and does not prove identity. Inset provenance remains `SAME_FRAME_CROP` or `ALTERNATE_VERIFIED_SOURCE`. Never synthesize a missing view.

## 5. Per-reel variables

Every template reads one JSON variables file. It may contain only verified strings/facts and explicit file refs: job id, reel type, headline, subhead, up to three chips, up to three insets, accent source/value, hero/text-free master, real-motion refs, optional turntable input, logo ref, CTA, audio strategy and output paths.

Hebrew is explicit RTL. Headline/subhead/chip limits come from the owner-approved rich editorial standard. Do not invent material, size, print duration, quality, stock, price, durability or suitability.
## 6. Motion vocabulary

The canonical editorial presets are:
- `HEADLINE_REVEAL`
- `ACCENT_RULE_WIPE`
- `CHIP_SEQUENCE`
- `INSET_POP`

They coexist with the existing:
- `VELVET_HARD_CUT`
- `VELVET_MACRO_PUNCH`
- `VELVET_MATERIAL_LABEL`
- `VELVET_FINAL_STAMP`

Motion supports hierarchy, evidence or pacing. Decorative motion that does not improve the story is removed.

## 7. Audio is mandatory creative work

Every Reel/video Story needs a documented audio strategy and exact-final Audio Gate. Follow `packages/vfom/FOUNDRY.json#audioPolicy`, `packages/vfom/VISUAL-OS.md`, and `packages/vfresearch/MUSIC.md`.

Use source, music, SFX, source+music, source+SFX, or explicitly justified intentional silence. Preserve useful real machine/handling/room sound when it strengthens proof. Do not invent a trending track name. A final Reel must not be near-silent unless intentional silence is documented and reviewed.
## 8. Cover, caption and hashtags

The Reel cover uses the same rich editorial language as the feed: dominant real product, heavy Hebrew headline, product-following accent rule, one-line subhead, and only verified chips/insets that earn their place. The cover must survive the feed-grid crop and phone preview.

Caption goes through `packages/vfcopy` and the exact public-social Visible Text gate. Public CTA resolves from current authority; the default end-card CTA is:
`לפרטים והזמנות — שלחו לנו הודעה כאן באינסטגרם`.

No public phone/WhatsApp/wa.me without exact current-task permission. Hashtags come from `packages/vfgrowth/data/hashtag-library.json` and current growth rules; public caption uses at most five.

## 9. QA order

Run on the exact current artifact, in this order:
1. **PREFLIGHT** — sources, claims, rights, copy state and visual-standard binding;
2. **EDIT-GATE** — real edit delta, Product Truth, source/final evidence and audio strategy;
3. **Visual-standard gate** — rich editorial scene/layout, RTL, product dominance, product-following accent and mobile readability;
4. **reference match** — compare exact cover/frames against the selected 6.6.9 S01–S07 reference(s), one primary and at most one support.

Then inspect first 2s, cut boundaries, representative midpoint(s), last 2s/end card, full-size cover and mobile/grid crop. A render receipt is technical evidence only; it is not creative approval and never a publish receipt.
## 10. Render commands on Chris / sderot-windows

Verified host path contract:
- repo: `D:\Velvet\Repos\velvetos-core`
- HyperFrames: `C:\Users\Chris\AppData\Roaming\npm\hyperframes.cmd`
- FFmpeg/ffprobe: `D:\Velvet\Tools\Shared\ffmpeg\current\bin`
- Blender: `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`

From `cmd.exe`:

```bat
set "PATH=C:\Users\Chris\AppData\Roaming\npm;D:\Velvet\Tools\Shared\ffmpeg\current\bin;%PATH%"
cd /d D:\Velvet\Repos\velvetos-core
py -3.14 scripts\vf_hyperframes.py doctor
py -3.14 scripts\vf_hyperframes.py plan packages\vfom\jobs\<JOB_ID>\render-request.json
py -3.14 scripts\vf_hyperframes.py run packages\vfom\jobs\<JOB_ID>\render-request.json
```

Batch variable-row render:

```bat
py -3.14 scripts\vf_hyperframes.py run packages\vfom\jobs\<JOB_ID>\render-request.json --batch packages\vfom\jobs\<JOB_ID>\render-batch.json
```

Turntable beat:

```bat
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --factory-startup --disable-autoexec -b -P scripts\vf_turntable.py -- --input "D:\Downloads\3D Prints\<REAL_PRINT_FILE>" --output "D:\Velvet\Artifacts\<JOB_ID>\turntable.mp4" --duration 7 --fps 30 --width 1080 --height 1920
```

The default `--color-mode embedded` preserves print-file material colours. When a verified photo of the printed item is the colour authority, use `--color-mode verified-hex --base-color-hex <#RRGGBB> --color-source <evidence ref>`; never guess a product colour.

Rendering runs on the authorized host; CI lints contracts/templates and never renders production video.
## 11. Handoff package

Mirror `packages/vfom/jobs/VF-R00x`. A review-ready Reel handoff contains:
- `content-contract.json`;
- `creative-manifest.json` with `format: reel` and `status: ready_for_publish`;
- per-reel variables;
- render request/batch request;
- exact cover and final video refs;
- caption/hashtag selection;
- audio/render/visible-text/package receipts with exact SHA-256 bindings;
- turntable receipt when used, including the real print-file input ref;
- explicit `needed_inputs` for anything Christian must provide.

`ready_for_publish` is a preparation state, not publication permission. Never call Instagram publishing, schedule a post, edit a live post or write any live channel from this route.

## 12. Route/template/preset drift sensor

`packages/vfom/REEL-ROUTE-CONTRACT.json` binds this route to:
`hook-card.html`, `chips.html`, `detail-inset.html`, `end-card.html`, `rich-still-reel.html`
and to the eight motion preset IDs above.

`scripts/check-reel-route-sync.py` fails when route names, templates and presets drift apart. PR2 flips the contract from pending to implemented when the templates/presets exist.

## 13. Completion

A Reel task is complete only with the reviewed rendered artifact (or a precise missing-input blocker), cover, caption/hashtags, receipts and handoff state. Do not stop at a storyboard, a raw timelapse, one animated still, an unrendered HTML composition or a turntable proposal.
