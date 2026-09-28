# Velvet Factory — Reel / Video Route

Status: **CURRENT · ChatGPT Project execution route**
Scope: prepare a review-ready Reel/video package; never auto-publish.

## 1. Non-negotiable truth boundary

A Reel is an execution task, not a caption or storyboard task. The physical product must come from verified real pixels or the real print file. Never ask a generative video model to render, redraw or repair the product, and never ask a generative model to render Hebrew text. Synthetic media may only supply non-proof atmosphere/support around source-locked product media.

Read first: `PRODUCT-TRUTH-GUIDE-v1.txt`, `packages/vfom/CREATIVE-TRANSFORMATION-LOCK.md`, `packages/vfom/LOCK.md`, the current Visual Standard/VISUAL-DNA/HyperFrames frame contract, video-toolchain docs, Edit Gate and Preflight.

## 2. Supported reel types

**A. Animated rich still.** Start from a text-free, source-faithful rich still master. Motion sequence: slow camera push on the real hero, headline reveal, accent-rule wipe, chips in sequence, detail inset pop, then at least one verified real-motion beat, and the end card. A Ken Burns move on one still by itself is not a Reel.

**B. Printer-to-shelf.** Use a verified printer timelapse/process clip, edit to the useful beats, and end on the styled text-free still / rich cover. The timelapse proves only what the source actually shows.

**C. 3D turntable beat.** Render the real print file in Blender. Match the material colour to the printed product using verified product evidence. Use a warm interior and a loopable 6–8s turntable as one beat; a render is an illustration of the real print file, not proof of a photographed physical event.

**D. Rich-style v2.** Upgrade an existing ready package without changing its source claims: new rich hook/cover, editorial motion, verified insets/real-motion beats, current audio gate and end card. Preserve old receipts as history; v2 gets new exact-final receipts.
## 3. Inputs and source locations

Resolve inputs before rendering:
- real photos/video: `packages/vfmedia/catalog.json`, Media Vault refs, or exact current-task files;
- still route / source truth: `packages/velvetos/chatgpt-project/` and `PRODUCT-TRUTH-GUIDE-v1.txt`;
- current visual rules: `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `VISUAL-DNA.json`, `HYPERFRAMES-FRAME.md`;
- brand tokens: `packages/vfbrand/brand-tokens.json`;
- render host: `packages/vfmcp/RENDER-HOSTS.json`;
- existing reel packages: `packages/vfom/jobs/VF-R00x/`;
- printer/edit tools: `scripts/vf_video_edit.py`, `scripts/vf_hyperframes.py`, `scripts/vf_3d.py`, `scripts/vf_turntable.py` when present.

Missing media is a needed input, never permission to fabricate it. A current photo/video must remain identifiable by asset/source ref and digest through the package.

## 4. Text-free masters and layer separation

Create or locate a **text-free master** before motion graphics. The master may contain the real source product plus the approved scene/retouch, but no final Hebrew, logo, CTA, phone, WhatsApp or generated lettering.

For still-driven reels, keep explicit layers:
1. `product_layer`: only real source pixels, or the deterministic render of the real print file for a turntable beat;
2. `background_plate`: scene pixels around the product, with no synthetic replacement product;
3. `editorial_overlay`: deterministic Hebrew, accent rule, chips, inset frame, CTA and exact logo;
4. `audio`: source sound / verified music / authored SFX according to office policy.

A product cutout/guard is an overlay-protection mechanism, not evidence that identity is correct. Product Truth review still compares the exact product source.
## 5. Per-reel variables

Each reel uses one JSON variables file. It carries only verified copy/facts and file refs: job id, reel type, headline, subhead, up to three chips, up to three detail insets, accent selection/source, hero/text-free-master ref, real-motion refs, optional turntable input, CTA, logo ref, audio strategy and output paths.

Hebrew is explicit RTL. Headline/subhead/chip limits come from the owner-approved rich editorial standard. Do not invent a missing chip, specification, price, stock state, material, size, durability or suitability claim.

The variable file is data, not an authority. Product Truth, Visible Text, public CTA, rights/claim gates and the Creative Manifest remain authoritative.

## 6. Motion grammar

Use the narrow Velvet vocabulary:
- `HEADLINE_REVEAL`;
- `ACCENT_RULE_WIPE`;
- `CHIP_SEQUENCE`;
- `INSET_POP`;
- `VELVET_HARD_CUT`;
- `VELVET_MACRO_PUNCH`;
- `VELVET_MATERIAL_LABEL`;
- `VELVET_FINAL_STAMP`.

Effects serve hierarchy/proof. Do not add decorative motion merely to make a still move. Hook and end card may carry deterministic text; real footage beats may remain NO_TEXT when stronger.

## 7. Audio

Every Reel/video Story needs a documented audio strategy and exact-final Audio Gate. Follow `packages/vfom/FOUNDRY.json#audioPolicy`, `packages/vfom/VISUAL-OS.md`, and `packages/vfresearch/MUSIC.md`.

Allowed strategies are source, music, SFX, source+music, source+SFX, or documented intentional silence. Prefer useful real studio sound when it strengthens proof. Do not invent a trending track name. If live music research is unavailable, specify energy/role only or mark selection for Instagram according to the music playbook. The final Reel must not be near-silent unless intentional silence is explicitly justified and reviewed.
## 8. Cover, caption and hashtags

The cover is a real-product frame/still in the same rich editorial language: heavy Hebrew headline, product-following accent rule, one-line subhead, optional verified chips/insets, product still dominant. The cover must be readable in the feed-grid crop and phone preview.

Public caption goes through `packages/vfcopy` and the current public-social Visible Text gate. Use the Instagram-message CTA from current authority when a CTA is appropriate; never add public phone/WhatsApp from memory.

Hashtags come from `packages/vfgrowth/data/hashtag-library.json` / current growth rules. Public caption uses at most five hashtags and records the selected `hashtag_set_id` where the existing workflow requires it.

## 9. QA order

Run gates in this order on the exact current artifact:
1. **PREFLIGHT** — content/publication preflight, exact source refs, copy/fact/rights state and visual-standard binding;
2. **EDIT-GATE** — real edit delta, Product Truth, source/final evidence, audio strategy, no synthetic product;
3. **Visual-standard gate** — rich editorial scene/layout, RTL, product dominance, accent follows product, mobile readability;
4. **Reference match** — compare exact cover/frames to the current owner-approved visual references and reject generic/template-looking output.

Then inspect the exact final render: first 2s, cut boundaries, representative midpoint(s), last 2s/end card, full-size cover and mobile/grid crop. Verify audio stream/level, no text-product collisions, no invented facts, and product identity across every beat.

A technical render receipt is not a creative PASS and never a publish receipt.
## 10. Exact render commands — Chris / sderot-windows

Current verified host facts (2026-09-28): HyperFrames 0.8.81 at `C:\Users\Chris\AppData\Roaming\npm\hyperframes.cmd`; FFmpeg/ffprobe under `D:\Velvet\Tools\Shared\ffmpeg\current\bin`; Blender 5.2.2 LTS at `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`; repo checkout `D:\Velvet\Repos\velvetos-core`.

HyperFrames from `cmd.exe`:

```bat
set "PATH=C:\Users\Chris\AppData\Roaming\npm;D:\Velvet\Tools\Shared\ffmpeg\current\bin;%PATH%"
cd /d D:\Velvet\Repos\velvetos-core
py -3.14 scripts\vf_hyperframes.py doctor
py -3.14 scripts\vf_hyperframes.py plan packages\vfom\jobs\<JOB_ID>\render-request.json
py -3.14 scripts\vf_hyperframes.py run packages\vfom\jobs\<JOB_ID>\render-request.json
```

Batch rendering after the bridge supports it:

```bat
py -3.14 scripts\vf_hyperframes.py run --batch packages\vfom\jobs\<JOB_ID>\render-batch.json
```

Turntable beat:

```bat
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --factory-startup --disable-autoexec -b -P scripts\vf_turntable.py -- --input "D:\Downloads\3D Prints\<REAL_PRINT_FILE>" --output "D:\Velvet\Artifacts\<JOB_ID>\turntable.mp4" --duration 7 --fps 30 --width 1080 --height 1920
```

Rendering runs only on the authorized render host; CI lints contracts/templates and does not render video.
## 11. Handoff package

Mirror the evidence style of `packages/vfom/jobs/VF-R00x`. A publishable Reel handoff contains:
- `content-contract.json`;
- `creative-manifest.json` with `format: reel` and `status: ready_for_publish`;
- `variables.json` (or product-named variables file);
- `render-request.json` or `render-batch.json`;
- exact cover ref and final video ref;
- caption/copy ref and hashtag selection;
- audio/render/visible-text/package receipts and exact SHA-256 bindings;
- any turntable receipt identifying the real print-file input;
- unresolved/needed inputs explicitly listed rather than fabricated.

`ready_for_publish` means the review package passed its preparation gates. It is **not** authorization to publish. Never call Instagram publishing from this route, never schedule automatically, and never mutate a live post.

## 12. Route/template/preset drift sensor

`scripts/check-reel-route-sync.py` binds this route to the named motion vocabulary and template contract. Stable template files are `hook-card.html`, `chips.html`, `detail-inset.html`, `end-card.html` and `rich-still-reel.html`. PRs that change route names, template IDs or preset IDs must update the matching contract in the same change; CI fails closed on drift.

## 13. Completion rule

A Reel request is complete only when the review package has the rendered/verified artifact (or a precise missing-input blocker), cover, caption/hashtags, receipts and `ready_for_publish` state. Do not stop at a plan, a still, a raw timelapse, an unrendered HTML composition, or a turntable proposal.
