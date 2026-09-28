# Velvet Factory Frame Contract for HyperFrames

## VF_PUBLICATION_ROUTE_V1 - current publication scope

Run `scripts/vf_publication_evidence.py --phase production` before production and `--phase delivery` before review delivery, with the exact manifest/content ID. A file-path or static wiring pass is not creative approval. Preserve source pixels, purposeful editorial richness and independent source/reference/copy/brand/final review evidence.

Authority remains `VISUAL-OS.md` and `VISUAL-DNA.json`. This file translates those rules into a render-frame contract without inventing a new visual identity.

> LEGACY / provenance only for VF publication; not a provider route: ## Canvas

Primary social master: portrait 9:16. Keep the subject and public text outside platform UI collision areas. Cropping a source must preserve the proof-bearing detail; never trade proof for a prettier crop.

## Visual archetype

> SUPERSEDED 2026-09-28 (kept for history): "Compose as a tactile engineering lab / material-intelligence workshop: real workbench, real machine action, material texture, controlled shadows and practical workshop energy."

**Default look since the owner decision of 2026-09-28:** the same rich editorial language as the feed stills (reference posts: owl 2026-09-19, dragon 2026-09-20, deer 2026-09-23, octopus 2026-09-27). A warm, real-feeling interior around the real product: wood, plants, window side light, design books; warm grade; one accent colour that follows the product. Layout limits come from the owner amendment of 2026-09-28 in `OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, and tokens from `packages/vfbrand/brand-tokens.json`.

Printer, workbench and process footage stay allowed as **beats inside a Reel** (real machine action, hands, material texture, proof moments). They are no longer the default frame look. Avoid generic AI chrome, random neon gradients and stock-looking workshop treatment.

## Reel structure (default)

1. **Hook card** — the Hebrew headline (2–4 lines, 3–7 words) with its accent rule and a one-line subhead, over a slow push-in on the real product in its warm interior. The first frame already shows the product.
2. **Chips** — up to 3 outline-icon chips animate in, one at a time, each stating a verified fact about this product.
3. **Detail inset** — a literal crop of the source frame (`SAME_FRAME_CROP`) or another real frame (`ALTERNATE_VERIFIED_SOURCE`), shown as an inset card or magnifier; never a synthesized detail.
4. **Real footage beats** — printer, process, handling or use footage from verified sources; these beats may be clean (`NO_TEXT`).
5. **End card** — the CTA `לפרטים והזמנות — שלחו לנו הודעה כאן באינסטגרם` and the exact owner-supplied logo. While the logo file is `missing: owner to supply` in `brand-tokens.json`, the end card omits the logo rather than drawing one.

Text is never baked into generated footage; every text layer is a deterministic overlay. Text, chips and insets never cover the product.

## First frame

The first frame must lead with at least one of: action, result, tension, clear detail or physical proof. Never spend the opening on a long logo intro or generic greeting.

## Motion

Default vocabulary is intentionally narrow: hard cut, motivated macro push-in, proof freeze, and slow motion only when it clarifies meaningful physical proof. Additional motion must map to `MOTION-PRESETS.md`; decorative motion without story value is a failure.

## Typography and RTL

- Public Hebrew text comes from the vfcopy pipeline; render only the approved exact string.
- Use explicit RTL direction for Hebrew layers.
- Use no more than two verified existing brand fonts/templates.
- Do not invent font families, weights, hex colors or gradients.
- ~~Prefer a clean no-text frame when copy does not beat the no-text baseline.~~ SUPERSEDED 2026-09-28: hook and end cards carry the editorial text layout above; footage beats may stay clean when that frame is stronger without text. The `NO_TEXT` comparison is still recorded in the visual-copy decision.
- Keep overlay hierarchy readable at phone size and outside Instagram UI/safe zones.

## Color

Use verified brand/template colors only. When an accent exists, keep one dominant accent per composition. Since 2026-09-28 the accent follows the product; the approximate accent samples in `packages/vfbrand/brand-tokens.json` are references for matching, not a fixed palette. If a verified token is unavailable, do not invent a replacement color; fall back to an already approved neutral/template treatment.

## Subject lock

When product geometry matters, composition must preserve the Content Contract Subject Pack invariants. HyperFrames may reframe real footage but must not synthesize a missing proof angle or silently alter product/material identity.

## Audio

Preserve real studio sound when it strengthens proof (machine, click, snap, handling, room tone). Music supports proof and pacing; it must not replace evidence. Reel/story masters require a real non-near-silent audio result unless intentional silence is explicitly justified under Foundry policy.

## Output QA hooks

A rendered frame is not accepted because it is technically valid. Existing Evaluation Engine gates remain mandatory: aspect ratio, resolution, safe zones, subtitle bounds, audio, frame integrity, Brand, Hook, composition, Reality, Originality, subject/material/geometry fidelity and artifact checks.

## Velvet Factory Visual Standard Gate — mandatory (`VF_VISUAL_STANDARD_GATE`)

## VF_VISUAL_STANDARD_GATE

Before public creative execution, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`. Bind SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897` and require `visualStandard.gate=PASS`. Missing/mismatched authority is `visual_standard_unavailable`; generic visual fallback is forbidden.
