> VF publication route: read `packages/vfom/PUBLICATION-PREP-EXECUTION.md`; require reference decomposition and exact-final reference_match_gate. Rejected directions are not repaired by repeating the same layout family.

# Velvet Factory — Creative Transformation Lock

Status: **MANDATORY · FAIL-CLOSED**

This lock exists to prevent a publication-prep task from collapsing into either extreme: a synthetic redesign that drifts from the real product, or a raw-photo carousel with no meaningful Velvet treatment.

## Core rule

For real-product publication prep, the product is source-locked but the presentation must be intentionally transformed. **Preserve the product; redesign the presentation.**

A crop, image ranking, simple ordering, filename selection, exposure tweak, or untouched/raw-photo carousel is not sufficient by itself. At least one owner-review visual — normally the hero/first slide — must show a meaningful, visible creative treatment consistent with the approved Velvet reference.

## Default execution method

Use the real uploaded photograph as the edit target. Do **not** recreate the product from a text description. Prefer image-edit/reference mode over text-to-image recreation.

Lock the product identity, silhouette, proportions, parts, openings, texture/material and verified color. Creative change belongs around the product: background/environment, lighting, shadow/depth, crop/perspective, negative space, atmosphere and editorial composition.

If generative editing cannot keep the product faithful, simplify the treatment or use deterministic compositing/retouching. Never solve fidelity by falling back to an untreated raw carousel and calling it finished.

## Owner correction — ordinary photo retouch does not violate Product Truth

For a verified real-product source, ordinary photographic corrections are allowed: brightness/exposure, mild contrast, white balance/color temperature, highlight/shadow balancing, light sharpening, gentle cleanup/noise reduction, crop/straighten and subtle subject-separation or lighting improvement.

These adjustments are source-grounded retouch, not product redesign, provided they do not materially change texture/material identity, elements/parts, geometry, silhouette, proportions, identifying details, surface pattern, protected eye/face details or the product's real color.

Do not fail Product Truth merely because such basic corrections were applied. Fail only when the product itself was materially altered or misrepresented.

This allowance is separate from the creative-delta requirement: a safe brightness/contrast/crop pass can preserve Product Truth while still being too weak to qualify as the finished Velvet publication treatment.

## Minimum creative delta

Before `ready for review`, require all of:

- `creative_delta_gate: PASS`
- `raw_passthrough: false`
- `source_edit_mode: SOURCE_IMAGE_EDIT` or a documented deterministic equivalent
- `hero_transformation_evidence: <final artifact ref + what visibly changed around the product>`
- `product_truth_gate: PASS`
- `brand_asset_gate: PASS`
- `public_cta_gate: PASS`

The hero must materially improve at least two presentation dimensions such as environment/background, lighting/depth, composition/perspective, subject separation, atmosphere or deterministic graphic hierarchy. Crop + exposure alone do not count unless the source was already at owner-reference quality and that exceptional decision is documented.

## Carousel rule

Multiple source photos do not imply a carousel. Choose the format that produces the strongest content. If a carousel is selected, slide 1 must be a fully treated hero at the approved quality bar. Secondary slides may be lighter real-photo treatments when they serve distinct roles such as macro, profile, rear/detail or proof, but a sequence of essentially raw originals is a FAIL.

Never use a carousel as an escape hatch when a compliant hero edit is difficult.
## Generation hygiene

Every generative edit prompt must explicitly say: preserve the exact real product; edit the scene around it; **NO LOGO, NO WORDMARK, NO PHONE NUMBER, NO WHATSAPP, NO CONTACT BAR, NO GENERATED HEBREW TEXT**. Branding and copy, when needed, are deterministic post-generation overlays from verified assets only.

## Hard failure examples

FAIL: raw photos merely resized into 1080x1350 slides; untouched source images presented as a finished carousel; product recreated from description instead of edited from source; synthetic product drift; generative text/logo/phone; a first slide that is only a crop of the source while claiming publication-grade treatment.

PASS: a source-faithful product preserved while the surrounding environment, light, depth and composition are deliberately brought to the approved Velvet premium/editorial standard, followed by exact-final QA.