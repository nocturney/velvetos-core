# vfbrand · brand tokens

`brand-tokens.json` is the shared, machine-readable token file for Velvet Factory creative. Docs read it now; HyperFrames templates are expected to read it later.

What it holds:

- **accents** — four accent colours sampled from the published reference posts (owl 2026-09-19 copper `#a86838`, dragon 2026-09-20 antique gold `#a87838`, deer 2026-09-23 light gold `#f8c888`, octopus 2026-09-27 amber `#f8a848`). They are labelled `sampled from published posts 2026-09-28, approximate`. The accent follows the product; these are matching references, not a fixed palette.
- **layout** — the headline / accent rule / subhead / chip / inset limits from the owner amendment of 2026-09-28 in `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`.
- **reel** — the default Reel beat order and end-card CTA text from `packages/vfom/HYPERFRAMES-FRAME.md`.
- **logo** — status `committed`: three owner-supplied rasters in `assets/logo/` (gold on white full lockup JPG, gold on navy velvet full lockup JPG, small black mono PNG with the `@velvets_cloud` handle) plus two transparent SVGs traced from the gold-on-white JPG with a single brand-gold fill (full lockup and mark only; `traced from owner JPG, owner-approved 2026-09-28`). Every file has a sha256.
- **brandMark** — navy velvet field + gold; brand gold `#b59761` sampled approximately from the gold-on-white JPG. The navy hex is not sampled (textured backdrop) and stays `missing: owner to supply`.
- **fonts** — status `committed` (owner decision 2026-09-28): Rubik (Hebrew; headline 700, subhead 600) and Cinzel (Latin; 700 and 400), Google Fonts variable TTFs under `assets/fonts/<family>/` with their `OFL.txt`. Two families, the VISUAL-DNA maximum.

Authority order: Product Truth and the canonical docs (`BRAND-SOURCE-OF-TRUTH.md`, the grid standard, `VISUAL-DNA.json`) win over this file.

Sensor: `scripts/check-brand-tokens.py` checks that the file exists, has the required keys, keeps the layout limits in sync with `VISUAL-DNA.json`, and that fonts/logo are either committed files or explicitly `missing`.
