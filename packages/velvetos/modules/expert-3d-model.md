# Expert — 3D model analyzer / maker / builder

Module id: `expert-3d-model`

## Provides

One routed 3D capability over the existing production stack: functional CAD, local Blender modeling/reconstruction,
mesh repair, deterministic geometry QA and STL/3MF handoff. **No print from HQ.**

Canonical router: `python scripts/vf_3d.py route --request "..."`.
Playbook: `packages/vfprod/experts/3D-MODEL.md`.
Blender contract: `packages/vfprod/BLENDER-MCP.md`.

## Packs

`vfprod`, `vfsku`, `vlicense` — no separate Blender pack.

## Specialist

`@technical-artist` · `@studio-producer`

## Tools

- Text-to-CAD / STEP / DfAM / Orca bridge: `packages/vfprod/TEXT-TO-CAD.md`.
- Hardened local Blender controller: `blender-ai-mcp` through `scripts/vf_3d.py`.
- Headless geometry/print QA: `design-os-3d-blender`.
- 3D AI Studio only as separately authorized optional capability, never the zero-cost default.

## Laws

- Run the 3D router before selecting a modeling engine.
- Discover installed 3D/slicer tool versions at runtime; exact versions/commits are evidence, never an allowlist or runtime pin.
- Keep parametric functional masters in CAD when STEP/B-rep is the correct source of truth.
- License gate (`#vlicense`) before reprint.
- No invented ₪, dimensions, material properties or physical-print claims.
- No external paid provider escalation without the cost gate.
- No API key in git and no non-loopback Blender control socket.
- No printer upload/start/heat/motion from this module.

Always present in core. An instance enables it via `modulesEnabled`.
