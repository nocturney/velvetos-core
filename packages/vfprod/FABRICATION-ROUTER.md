# Fabrication Router

Status: **ACTIVE · mandatory for fabrication/CAD requests**

This router decides which tool or skill to use before engineering work begins. It extends `vfprod`; it is not a second runtime or printer source of truth.

## Decision rule

Natural-language entrypoint: `python scripts/vf_fabrication_router.py decide --request "<request>" [--file <path>]`. It returns the resolved intent, primary tool, chain, confidence and reason. High/medium-confidence decisions execute that route; low-confidence decisions require the agent to resolve the intent against this document and then call `route --intent`.

Use the smallest verified tool chain that can produce and check the requested result.

1. **No artifact / no exact geometry needed** → use native reasoning for calculations, tolerances, tradeoffs and requirements.
2. **Photo or sketch is input** → use native vision to extract visible constraints, then route the actual engineering work. Never infer hidden/critical dimensions from pixels.
3. **Functional/dimensional CAD** → use `cad`.
4. **Reference reconstruction with protected functional interfaces** → use native vision for visible constraints, then the existing `vf-3d-router` so it can choose `TEXT_TO_CAD`, `BLENDER_NATIVE` or `HYBRID_CAD_THEN_BLENDER`; never infer hidden dimensions.
5. **Existing mesh that needs repair/refinement before print prep** → run `dfam-check`, then the existing `vf-3d-router`, then re-run DfAM on the changed mesh.
6. **Organic/sculptural/generative mesh** → prefer 3D AI Studio; use `dfam-check` before print preparation.
7. **Named standard/off-the-shelf part** → use `step-parts` before creating placeholder geometry.
8. **Visual review of STEP/STL/3MF/GLB/DXF/URDF/SRDF/SDF** → use `cad-viewer`.
9. **Additive manufacturability** → use `dfam-check`; use orientation analysis when supports/overhangs/orientation matter.
10. **Slicing/G-code** → use `gcode` with the existing VelvetPrintLab Orca router and printer matrix.
11. **Dimensioned manufacturing PDF** → use `engineering-drawing`.
12. **2D profile / flat pattern / laser-waterjet-router layout** → use `dxf`.
13. **CNC / sheet metal / injection molding review** → use `dfm`.
14. **Robot descriptions** → use `urdf`, `srdf` or `sdf` according to the requested artifact.
15. **SendCutSend** → use `sendcutsend` for preflight only; never submit an order.
16. **Visual concept only** → native image generation may be used, but it is not dimensional CAD.

The machine-readable routes live in `FABRICATION-ROUTER.json`.

The `cad` route may use interchangeable local execution engines declared in `CAD-ENGINE-REGISTRY.json`. The registry is subordinate to this router: it chooses an implementation for deterministic CAD, never a new intent or authority. `scripts/vf_cad_stack.py doctor` verifies the local engine layer; Geometry IR and the two-attempt repair bound are defined in `CAD-ENGINE-STACK.md`. For chat-driven functional CAD, resolve the intent here first, materialize only explicit dimensions/constraints into Geometry IR, then call `scripts/vf_cad_stack.py build --engine auto`; unsupported geometry fails closed into the existing CAD skill/code-generation route rather than being guessed.

## Installed upstream skills

Project-pinned copies from `earthtojake/text-to-cad`:

- `cad`
- `cad-viewer`
- `dfam-check`
- `dfm`
- `dxf`
- `engineering-drawing`
- `gcode`
- `sdf`
- `sendcutsend`
- `srdf`
- `step-parts`
- `urdf`

The upstream `bambu-labs` skill is deliberately excluded.

For local agents, load the selected skill from `.agents/skills/<skill>/SKILL.md` and follow it rather than reimplementing it from memory. Grok-compatible copies are under `.grok/skills/`.

For ChatGPT/HQ sessions where those project Skills are not natively discoverable, this router is the authority: resolve the selected skill, read its pinned `.agents/skills/<skill>/SKILL.md` from the repository/authorized host, and execute through the authorized host/tooling. Skill presence alone is not proof that its runtime works.

## Automatic chains

Typical chains:

- Functional part: `cad → cad-viewer`
- Photo/sketch to functional part: `native vision → cad → cad-viewer`
- Assembly with a known purchased component: `step-parts → cad → cad-viewer`
- New FDM part to print file: `cad → cad-viewer → dfam-check → gcode`
- Reference reconstruction with protected interfaces: `native vision → vf-3d-router → cad-viewer`
- Reference reconstruction to print: `native vision → vf-3d-router → dfam-check → gcode`
- Existing mesh repair/refinement: `dfam-check → vf-3d-router → dfam-check → cad-viewer`
- Organic model for printing: `3D AI Studio → dfam-check → gcode`
- Manufacturing sheet: `engineering-drawing`
- Cut layout: `dxf → cad-viewer`
- MoveIt description: `urdf → srdf → cad-viewer`

Do not invoke every available skill. Use only the chain required by the task.

## Additive routing specifics

`VelvetPrintLab\slicer-router\printer_matrix.json` stays authoritative for H2D, U1, ECC2, Creator 5 and Creator 5 Pro. A text-to-cad profile may derive from it but may not replace it.

Before slicing a new or materially changed part:
- verify mesh/scale;
- run DfAM;
- run orientation analysis when build orientation could materially affect supports/quality;
- then slice and validate G-code.

A previous DfAM receipt may be reused only when the mesh bytes and relevant print process have not changed.

## Hard safety boundary

This integration may generate, inspect, review, convert and slice files. It may not:
- control printer networking;
- upload to a printer;
- start, pause or cancel a print;
- heat or move printer hardware;
- submit a SendCutSend order.

Those actions require a separate explicitly authorized production-floor route. `bambu-labs` is not installed by this integration.

## Fallback policy

Use built-in/native capabilities when they are the better tool:
- reasoning for calculations and requirement analysis;
- vision for interpreting supplied images/sketches;
- image generation for non-dimensional concept art.

Use the specialized skill when the result depends on deterministic geometry, exact measurements, a manufacturing file, a CAD-specific review, or slicer validation.

If a specialized skill fails, do not silently replace exact engineering output with an approximation. Use another verified tool only when it is semantically equivalent; otherwise report the blocker.

## Verification

Run:
```
python scripts/vf_fabrication_router.py list
python scripts/vf_fabrication_router.py decide --request "תכנן תושבת למיסב 608ZZ ותכין להדפסה"
python scripts/vf_fabrication_router.py route --intent functional_cad_create_edit
python scripts/check-vf-fabrication-router.py
python scripts/vf_cad.py doctor
```

A route is active only when the selected skill is installed, its runtime requirements are present where applicable, and the relevant host/tool smoke passes.
