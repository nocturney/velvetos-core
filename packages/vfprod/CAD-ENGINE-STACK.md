# CAD Engine Stack

VelvetOS keeps one fabrication authority: `FABRICATION-ROUTER.md`. This stack adds interchangeable execution engines beneath the existing `cad` route; it is not a second control plane.

## Roles

- build123d/cadgen — primary, already verified through text-to-cad.
- CadQuery — secondary B-Rep engine in an isolated Python 3.12 venv.
- JSCAD — secondary lightweight CSG engine in an isolated local Node workspace.
- CAD/CAE Copilot — pilot adapter only; local MCP/backend is allowed, external model-provider calls are not enabled by this integration.
- Forgent3D — pilot workbench only; local visual/rebuild loop, not production authority.
- Graph-CAD — IR design inspiration only.
- Multi-Agent-CAD — decompose → generate → inspect → bounded repair pattern only; no LangGraph/Aider production runtime.
- awesome-cad — ecosystem radar only.
- CADAM — not installed.

## Geometry IR

`GEOMETRY-IR.schema.json` is a small explicit intermediate representation for hierarchy, primitive dimensions and assembly constraints. Missing dimensions stay missing; the validator never infers or invents them. Buildable primitive parts may declare `operation: add|cut` and `translate_mm: [x,y,z]`.

## Chat/runtime build bridge

A fabrication chat request is resolved by `vf_fabrication_router.py decide`, then represented explicitly as Geometry IR, then executed with `vf_cad_stack.py build --engine auto`. Auto selects the first verified local engine in order: build123d, CadQuery, JSCAD. The bridge emits local artifacts plus `build-receipt.json` with SHA-256 evidence and never uploads to or controls a printer. The generic bridge currently builds explicit box/cylinder boolean models; unsupported geometry fails closed and must route through the existing CAD skill/code-generation path rather than inventing geometry.

## Bounded repair

`vf_cad_stack.py repair-next` permits two repair iterations. A third failure returns `FALLBACK_REQUIRED`; it never loops indefinitely.

## Host paths

All heavy runtimes live under `%VELVET_PRINTLAB_ROOT%\tools\cad-stack\` and are intentionally excluded from Core. Core stores only contracts, routing, sensors and evidence.
## Exact CAD hardening

Phase 4 keeps this stack under the same Fabrication Router authority.

- Primitive local frame is fixed to XY-centered with Z-min at zero; `translate_mm` is then applied as an explicit global translation.
- build123d remains the primary engine. Its default output remains STEP + STL for backward compatibility.
- Explicit `--formats` may request build123d STEP, STL, 3MF, GLB, DXF and SVG. DXF/SVG are semantic 2D face/profile exports, not arbitrary projections.
- CadQuery remains a separate fallback environment. JSCAD remains a lightweight secondary mesh engine.
- Every executed build receipt records the exact engine version, coordinate frame, input SHA-256, normalized-IR SHA-256, profile references and per-output SHA-256.
- Reopen acceptance for exact-CAD uses deterministic geometry/semantic checks. Byte equality is recorded but is not required for serializers such as STEP/3MF/DXF that may encode non-geometric metadata.
- Semantic selection rules live in `EXACT-CAD-PATTERNS.json`: geometry predicates and explicit datums are required; numeric face-index fallback is forbidden and ambiguity fails closed.
- `bd_warehouse==0.3.0` is the bounded curated mechanical primitive library in the canonical build123d venv. It is not a new authority. Initial proven fixtures are socket-head cap screw, hex nut and plain washer; broader feature packs are promoted separately.
## Mechanical feature packs

`MECHANICAL-FEATURE-PACKS.json` and `scripts/ai3d_mechanical_features.py` extend the same CAD stack; they are not a second authority.

Promoted packs wrap mature upstream primitives where available: fasteners, solid ISO threads, spur gears, deep-groove bearings and heat-set inserts use `bd_warehouse`. Magnet pockets, explicit fit calculations and the bounded open-top enclosure use small native build123d/VelvetOS wrappers with all dimensions/clearances explicit.

Snap-fit, living-hinge and sheet-metal packs are intentionally non-executable candidates until their material/process or bend-policy blockers are qualified. Unknown feature IDs and invalid/adversarial parameters return BLOCKED.

## Assemblies, motion, collision and ECAD/MCAD

Phase 8 remains beneath the same Fabrication Router and reuses the existing FreeCAD, KiCad and PCB-to-enclosure providers.

- build123d revolute joints require an explicit axis and angle range. The proven motion path samples a bounded sweep; it does not claim continuous collision detection between samples.
- build123d static collision uses exact B-Rep intersection volume. A positive fixture proves clear states and colliding states, and an out-of-range joint angle fails closed.
- FreeCAD 1.1.3 Assembly is proven headless with a real Assembly::AssemblyObject, Assembly::JointGroup, grounded part and Fixed joint solver fixture. This is a provider capability, not a second assembly authority.
- KiCad CLI 10.0.6 is proven for board-only STEP export. The resulting board solid is reopened in the canonical build123d runtime and checked against enclosure shells with positive and negative interference fixtures.
- The existing pipeline_pcb_to_enclosure remains the composite electronics/enclosure route. Phase 8 validates it rather than replacing it.
- Component-complete KiCad STEP export remains a candidate for the current Arduino Nano fixture because the installed template references KICAD9_3DMODEL_DIR .wrl pin-header models while the KiCad 10 install contains same-name .step models. Board-only proof must not be reported as component-complete proof.
- URDF/Pinocchio remains an optional non-installed candidate until an articulated-mechanism task demonstrates a capability gap not already covered by build123d/FreeCAD joints and an isolated runtime passes dependency/license fixtures.

The bounded contract is docs/implementation/ai-3d-modeling-engineering-core/assembly-motion-ecad-v1.json; host acceptance is scripts/validate_ai3d_phase8_assembly_ecad.py.
