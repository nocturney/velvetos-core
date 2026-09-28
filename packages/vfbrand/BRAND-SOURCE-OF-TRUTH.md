# Velvet Factory · Brand Source of Truth

Status: **LOCKED** · 2026-09-13 · owner reconciliation 2026-09-28 (see `Owner reconciliation · 2026-09-28` below)

This document is the visual source of truth for public Velvet Factory creative. It overrides older ad-hoc orange/black/text-card directions when they conflict with the current identity.

## Authoritative identity (logo and brand mark)

- Master logo: **user-supplied `logo vector.svg`**.
- Visual reference supplied by owner: deep **navy** field with **warm gold / ivory** logo and typography. Since 2026-09-28 this navy/gold/ivory set is the **logo and brand-mark identity**, not the default feed background.
- Wordmark: `VELVET FACTORY` + `3D PRINTING STUDIO` as supplied in the master identity.
- The exact master logo must be placed as an asset. **Do not redraw, regenerate, reinterpret or approximate the VF mark.**
- Do not invent hex values from screenshots. When exact color is required, sample/use the master SVG or an owner-approved exported brand asset.

## Brand character

Elegant, premium, restrained, tactile and crafted. ~~Dark navy is the primary visual field; warm gold/ivory is the signature accent.~~ *(SUPERSEDED 2026-09-28 for feed creative: the feed field is a warm real-feeling interior and the accent follows the product; navy/gold/ivory stays on the logo and brand mark.)* Product photography should feel intentional and studio-led, not like a generic tech card or an AI fantasy render.

### Not the brand

- ~~orange as a default brand accent;~~ *(SUPERSEDED 2026-09-28 → accent follows the product; see below)*
- a fixed default accent colour applied regardless of the product (orange or any other);
- charcoal/orange tech-card language unless orange is genuinely present in the photographed product;
- invented logos, quotation-mark marks, generic 3D-print icons as a substitute for the VF mark;
- synthetic product renders presented as a real Velvet Factory item;
- decorative copy that competes with the photographed object.

## Product Truth — non-negotiable

For any post, carousel, story, reel cover or paid/organic sales surface representing a real printed object:

1. The physical object in the final creative must be the **same real source object** captured in the approved RAW media.
2. Generative editing may **not** change object geometry, silhouette, part count, proportions, surface pattern, color/material appearance when those properties represent the sellable item.
3. Allowed treatment is presentation treatment around the truthful object: crop/composition, exposure, white balance, contrast, color grade, noise/cleanup, distraction/background cleanup, subject separation, framing, brand graphics, typography and layout.
4. Background replacement is allowed only when it does not alter the subject and is not used as evidence of scale, use, environment, durability or another factual claim.
5. If a generated/edited frame cannot be reconciled visually with a real source frame, it is **illustrative only** and cannot be used as a product/showcase/sales image.
6. For real-product commercial/showcase content, `synthetic_subject_change` must be `NONE` and `product_truth_gate` must be `PASS`.

## Review question

Before approval ask: **"If a customer orders because of this image, will the physical item they receive match the object being shown?"**

If the answer is not an unqualified yes, the asset is blocked.

## Owner reconciliation · 2026-09-28

Owner decision (2026-09-28): the target visual language for stills and video is the rich editorial language of the current feed posts (owl 2026-09-19, dragon 2026-09-20, deer 2026-09-23, octopus 2026-09-27). This section reconciles the brand document with that decision and with `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md` (owner amendment 2026-09-28).

- **Feed language:** warm, real-feeling interior around the real product (wood, plants, window side light, design books), a heavy Hebrew headline with an accent rule and a one-line subhead, up to 3 outline-icon chips and up to 3 detail insets or one magnifier crop.
- **Accent follows the product.** Each composition uses one accent colour taken from the product or its scene. Approximate samples from the four reference posts are in `packages/vfbrand/brand-tokens.json` (labelled approximate; they are references, not new brand colours).
- **Logo and brand mark:** navy/gold/ivory. Evidence: the owner visual reference above, and the owner-supplied gold logo files listed in the ChatGPT Project asset manifest `packages/velvetos/chatgpt-project/ASSET-MANIFEST-v6.6.4.json` (`Velvet-Factory-APPROVED-LOGO-GOLD-LIGHT-v1.jpg`, `Velvet-Factory-APPROVED-LOGO-GOLD-DARK-v1.jpg`). On 2026-09-28 the owner supplied three logo rasters, committed under `packages/vfbrand/assets/logo/`: gold on white (full lockup with `3D PRINTING STUDIO`, JPG), gold on navy velvet (full lockup, JPG) and a small black mono PNG with the `@velvets_cloud` handle. The gold lockups are not transparent; transparent PNG/SVG versions are still wanted. Approximate brand gold sampled from the gold-on-white JPG: `#b59761` (recorded in `brand-tokens.json`). The navy velvet backdrop stays the logo/brand-mark field. Brand fonts are not committed; `brand-tokens.json` records them as `missing: owner to supply`. *(Updated later on 2026-09-28: owner decision — verified brand fonts are Rubik for Hebrew (headline 700, subhead 600) and Cinzel for Latin (700/400), OFL, committed under `packages/vfbrand/assets/fonts/`; transparent SVG logos traced from the gold-on-white JPG with a single brand-gold fill were owner-approved and committed under `packages/vfbrand/assets/logo/`.)*
- **Reel cover text:** follows the headline limit of the grid-standard amendment (2–4 lines, 3–7 words), replacing the older 2–5 word cap.
- **Unchanged:** Product Truth (below), the logo lock (exact asset only, never redrawn), and "decorative copy that competes with the photographed object" as a reject.
