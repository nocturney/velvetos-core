# Expert — 3D model analyzer / maker / builder

Module id: `expert-3d-model`

## Provides

Mesh intake, printability analysis, concept generation, repair hints, and STL/3MF handoff — on the print floor and via 3D AI Studio after lead approval. **No print from HQ.**

Extends `production-print`. Playbook: `packages/vfprod/experts/3D-MODEL.md`.

## Packs

`vfprod`, `vfsku`, `vlicense`

## Specialist

`@studio-producer` · `@technical-artist`

## Tools

Drive (job files) · Fabrication Router (`packages/vfprod/FABRICATION-ROUTER.md`) · pinned text-to-cad Skills (`.agents/skills/`) for CAD/viewer/STEP-parts/DfAM/DFM/DXF/drawings/G-code/URDF/SRDF/SDF/SendCutSend preflight · 3D AI Studio MCP (`3DAISTUDIO.md`) for organic/generative work

## Laws

- Resolve `packages/vfprod/FABRICATION-ROUTER.md` before selecting a fabrication tool
- Load the selected pinned `.agents/skills/<skill>/SKILL.md` when available
- `bambu-labs` / printer upload / print-start / heating / motion remain excluded
- License gate (`#vlicense`) before reprint
- No invented ₪ from credits
- No API key in git

Always present in core. An instance enables it via `modulesEnabled`.
