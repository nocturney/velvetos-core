---
name: vf-pixel-art
description: Design and QA deterministic pixel art, pixel icons, sprite families, sprite sheets and small pixel animations for Velvet workflows when a user asks for pixel art or sprites. Use the upstream pxl JavaScript DSL only after local pinned runtime admission, otherwise prepare a testable source draft and report rendering as NOT_RUN. Do not invoke this for photography, CAD or ordinary vector/logo tasks.
---

# Velvet Pixel Art — conditional pxl adapter

Upstream inspiration and optional renderer: [crsolver/claude-pxl](https://github.com/crsolver/claude-pxl/tree/21fee41f7ecce00bc868d7567f24ffd0f3acc8fa), MIT; upstream has an independent `SKILL.md`. This local Skill is an instruction wrapper **without a bundled pxl binary or upstream source files**.

## Route

1. Require a pixel-art/sprite request. Resolve dimensions, palette size, transparency, static/animation, spritesheet metadata and intended usage. Preserve existing brand/product identity and source rights.
2. Route image-authority decisions through `.cursor/skills/vf-image-design-craft/SKILL.md` and its QA. Do not use this Skill to manufacture unverified real product details or to replace 3D-print manufacturing masters.
3. For a symbolic sprite, draft palette keys and a reproducible `.px.js` with sprite and layer/variant structure. Prefer symmetry/mirror and base+palette-swap variants over pixel duplication.
4. If and **only if** source at the pinned SHA has been reviewed and a local Node >=22.18 `pxl` runtime has already been verified in an isolated authorized workspace, invoke the **local** `node <reviewed-local-root>/bin/pxl.js build <asset.px.js> --out <disposable-output>`. Never run `npx github:...` automatically or fetch/install packages from this Skill.
5. Inspect exact 1x PNG pixels, alpha edges, defined palette, dimensions, frames and sprite-sheet JSON. Exercise two deterministic repeat builds and verify corresponding outputs. Fix and rerender. For failed/missing runtime, state `NOT_RUN` and return source/next gate, not a fake preview.
6. Maintain the existing four-color *total* manufacturing rule, including outline, when routed through the dog portrait/3D-print workflow; do not apply generic palette advice as permission to exceed it.

## Evaluation

See `docs/implementation/office-v2/phase2/owner-creative-agent-tools-intake-2026-10-21.md`. Research candidate `candidate-crsolver-claude-pxl` is `RESEARCHED/NOT_RUN` and does not authorize a system-wide install or publication. Compare exact-pixel evidence with the incumbent approved design workflow.
