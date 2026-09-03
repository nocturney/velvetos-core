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

Drive (job files) · 3D AI Studio MCP (`3DAISTUDIO.md`) · site UI failover

## Laws

- License gate (`#vlicense`) before reprint
- No invented ₪ from credits
- No API key in git

Always present in core. An instance enables it via `modulesEnabled`.
