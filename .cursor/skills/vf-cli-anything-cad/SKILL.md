---
name: vf-cli-anything-cad
description: Route scoped agent-native FreeCAD work through the pinned CLI-Anything adapter while preserving text-to-cad and vf_cad as canonical CAD/DfAM/slicer authorities.
---

# CLI-Anything CAD adapter

Use when the request specifically benefits from iterative structured FreeCAD operations, explicit workbench commands, or headless STEP/STL/FCStd export.

1. Read `packages/vfprod/TEXT-TO-CAD.md` and `packages/vfharness/devtools/cli-anything.json`.
2. Run `python scripts/vf_cli_anything.py doctor`.
3. Use `python scripts/vf_cli_anything.py freecad -- <args>` for the scoped operation.
4. After geometry export, run the existing `scripts/vf_cad.py` DfAM/slicing path and its applicable verification.
5. Keep physical printer upload/start/heating/motion outside this adapter.

## Routing

- Plain-language functional/parametric part generation stays on text-to-cad.
- Explicit iterative FreeCAD operations may use this adapter.
- DfAM, printer profiles, OrcaSlicer execution and G-code validation stay on `vf_cad.py`.
- CLI-Anything 3MF is not routable while its pinned test suite has known failures.

## Hard stops

Do not invoke `preview`, `motion` or `repl`; the adapter blocks them. Do not bypass the pinned overlay or use CLI-Anything as a second runtime, slicer authority, memory authority, release path, or printer-control surface.
