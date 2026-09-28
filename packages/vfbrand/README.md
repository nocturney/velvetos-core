# vfbrand · brand tokens

`brand-tokens.json` is the shared, machine-readable token file for Velvet Factory creative. Docs read it now; HyperFrames templates are expected to read it later.

What it holds:

- **accents** — four accent colours sampled from the published reference posts (owl 2026-09-19 copper `#a86838`, dragon 2026-09-20 antique gold `#a87838`, deer 2026-09-23 light gold `#f8c888`, octopus 2026-09-27 amber `#f8a848`). They are labelled `sampled from published posts 2026-09-28, approximate`. The accent follows the product; these are matching references, not a fixed palette.
- **layout** — the headline / accent rule / subhead / chip / inset limits from the owner amendment of 2026-09-28 in `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`.
- **reel** — the default Reel beat order and end-card CTA text from `packages/vfom/HYPERFRAMES-FRAME.md`.
- **fonts** and **logo** — status `missing: owner to supply`, with `null` values and empty file lists. Nobody fills these in by guessing a font family or pointing to a logo file that is not committed. When the owner commits the files, list their repository paths under `files` and change `status`.

Authority order: Product Truth and the canonical docs (`BRAND-SOURCE-OF-TRUTH.md`, the grid standard, `VISUAL-DNA.json`) win over this file.

Sensor: `scripts/check-brand-tokens.py` checks that the file exists, has the required keys, keeps the layout limits in sync with `VISUAL-DNA.json`, and that fonts/logo are either committed files or explicitly `missing`.
