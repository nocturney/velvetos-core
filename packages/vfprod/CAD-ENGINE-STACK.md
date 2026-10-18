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


## Drawings, vectors and sheet metal

Phase 9 remains beneath the Fabrication Router and reuses the existing build123d and FreeCAD runtimes.

- FreeCAD 1.1.3 TechDraw is proven headless with a real `TechDraw::DrawPage`, `TechDraw::DrawViewPart`, explicit A4 template and full DXF output. Acceptance requires independent reopen by ezdxf/build123d; projection fragments are not accepted as DXF files.
- `ezdxf 1.4.4` is the independent DXF parser/validator in the canonical build123d environment. A file that cannot be parsed as a complete DXF fails closed.
- The text/glyph path uses build123d `Text` plus explicit font name and exports DXF + SVG. Latin and Hebrew fixtures are reopened and geometry-compared; font files are never copied or bundled as artifacts.
- FreeCAD SheetMetal 0.8.24 is pinned in an isolated checkout with an isolated NetworkX 3.5 dependency. It is not copied into the global FreeCAD installation. Unfold requires explicit thickness, bend radius, K-factor and K-factor standard.
- The proven SheetMetal fixture unfolds an L-shape with 1 mm thickness, 1 mm bend radius and K=0.38 ANSI, then writes a complete DXF and independently reopens it at the same 60 x 48.16769893 mm planar bounds.
- Draftwright 0.4.34 remains an isolated evaluation candidate. It is AGPL-3.0, Alpha, and requires build123d <0.11; it must not downgrade or enter the canonical build123d 0.11.1 environment without a separate product/license and compatibility decision.

The bounded contract is `docs/implementation/ai-3d-modeling-engineering-core/drawings-vectors-sheetmetal-v1.json`; acceptance is `scripts/validate_ai3d_phase9_drawings_vectors_sheetmetal.py`.

## Simulation and optimization (Phase 10)

The existing FreeCAD 1.1.3 FEM runtime is reused, including its bundled Gmsh 4.15.0 mesher and CalculiX 2.22 linear-static solver. This is a bounded provider-level capability under the existing Fabrication Router, not a new FEM or optimization control plane.

- The reference fixture specifies all geometry, material properties, Poisson ratio, supports, pressure direction, units and resource limits explicitly.
- A 40 x 10 x 10 mm synthetic axial-tension bar is solved with two separate second-order tetrahedral Gmsh meshes. Mesh sizes 5 mm and 3 mm yield 1052 and 2018 nodes respectively.
- Independent analytic extension is 0.001904762 mm; fine-mesh mean extension is 0.001889190 mm (0.82% relative error). Normalized mesh-refinement discrepancy is 0.039%.
- Acceptance requires real CalculiX exit code 0, nonempty FRD stress/displacement fields, analytic error threshold, two-mesh agreement, 12 fail-closed negative cases and SHA-256 receipts for .inp/.frd/.dat/FCStd evidence.
- Material, loads, constraints, precision and mesh resource bounds must be present; unknowns fail closed. Solver success is not structural certification or design acceptance.
- No new solver is installed and neither SfePy nor DOLFINx enters the canonical runtime: both remain research candidates.
- TPMS gyroid level-set sampling is RESEARCH_ONLY; it generates no production mesh or strength/printability claims.
- Automatic optimization/promotion into manufacturing remains BLOCKED. Gmsh/CalculiX binaries remain separate GPL-governed CLI dependencies; redistribution or bundling needs an explicit compliance review.
- No printer network, machine action or slicer authority changes are granted.

Contract: `docs/implementation/ai-3d-modeling-engineering-core/simulation-optimization-v1.json`.
Evidence: `docs/implementation/ai-3d-modeling-engineering-core/evidence/phase10-simulation-acceptance-20261008.json`.
Validator: `scripts/validate_ai3d_phase10_simulation.py`.

## DfAM / slicer validation (Phase 11)

The existing `vf_cad.py` bridge and upstream `gcode_tool.py` are retained. This phase does not create another slicer router, overwrite calibrated native profiles or grant access to device upload/start APIs.

- The synthetic Geometry IR model (120 x 80 x 12 mm) is exported by the canonical build123d path as STEP, watertight STL and 3MF. Independent reopen/bounding-box and volume comparisons are required before slicing.
- `vf_cad.py dfam` provides a coarse geometric overhang/support report only. It does not certify strength, fit, layer adhesion or printability.
- Two actual OrcaSlicer 2.4.2 CLI runs via `vf_cad.py slice --execute` were proven offline with the existing Flashforge Creator 5 (`c5`) profile: STL and 3MF each produce 60 layers, 12.05 mm max G-code Z, and pass the canonical G-code validator. No printer is connected.
- The H2D profile emits a documented `G1 X270 Y-0.5 F60000` service travel in its native machine-start G-code, outside the wrapper's current Y>=0 machine envelope. Its offline G-code remains BLOCKED and cannot become print-ready until independently verified motion bounds are supplied; the validator must not silently widen the machine envelope.
- Negative checks block oversize models, direct STEP input, artificially injected out-of-range G-code and unverified H2D service motion.
- All native machine/process/filament profiles and wrappers are checked for exact-byte immutability before and after slicing.
- Other printer keys `u1`, `ecc2`, `c5pro` remain unqualified by this fixture. Even a passing `c5` proof is an offline software-toolchain proof, not approval of a printer or calibrated material.
- OrcaSlicer is installed as a separate AGPL-3.0 application; it must not be included in a closed product installer or bundled as an executable without explicit license compliance review.
- No printer upload, start-print, firmware command execution, machine-control or automatic manufacturing release is permitted.

Contract: `docs/implementation/ai-3d-modeling-engineering-core/dfam-slicer-v1.json`.
Evidence: `docs/implementation/ai-3d-modeling-engineering-core/evidence/phase11-dfam-slicer-acceptance-20261008.json`.
Validator: `scripts/validate_ai3d_phase11_dfam_slicer.py`.

## CAM and GRBL post-only verification (Phase 12)

This phase reuses the already-promoted CreativeCraft `cam.toolpath` route, preferred on mac-mini-office with Fabex 3.0.2 and falling back to Windows. There is no second cross-station CAM router or machine action path.

- A 40 x 30 mm synthetic rectangular contour has explicit source dimensions, a 3 mm flat end mill, 2 mm depth split into -1/-2 mm passes, 5 mm safe clearance, 5/10 mm/min feed/plunge and a 12000 rpm fixture spindle reference. Those numbers are fixture constants **not qualified machining recipes**.
- The existing cross-station Fabex 3.0.2 GRBL output is hash-checked against its existing provenance report and independently re-validated on Windows; the historical Mac run was not repeated during this phase.
- FreeCAD 1.1.3 CAM/Path `grbl_post` is proven headless against a second, explicit-waypoint GRBL fixture. This proves only G-code **postprocessing** of known Path commands, not stock-aware CAM toolpath planning.
- The modal GRBL parser blocks unrecognized machine commands, inch/relative modes, unsafe plunge/rapid movement, missing spindle shutdown, missing terminator, non-fixture feedrates and any trailing motion after shutdown. In total 15 malformed input cases and 18 adversarial G-code variants fail closed.
- CAM executable artifacts have hashes, exact file size, source-geometry bounds and feed/phase receipts. FreeCAD's output timestamps are not expected to be byte-for-byte deterministic, and acceptance relies on decoded geometry and command semantics.
- `cam.grbl_post.freecad` receives bounded provider evidence. The existing `cam.toolpath` remains one `PROVEN_TYPED` route, not duplicated.
- `cam.qualified_machining_process` is BLOCKED: unqualified material, spindle/load/workholding, physical controller dialect, tool collisions, machine motion envelope and independent approval are not established.
- No GRBL was executed on a machine. No spindle, laser or printer network action is authorized and no G-code is labeled production-ready.

Contract: `docs/implementation/ai-3d-modeling-engineering-core/cam-toolpath-v1.json`.
Evidence: `docs/implementation/ai-3d-modeling-engineering-core/evidence/phase12-cam-acceptance-20261008.json`.
Validator: `scripts/validate_ai3d_phase12_cam.py`.

## Phase 14 additional printer profiles — offline capability only

The existing canonical `vf_cad.py` route generated real OrcaSlicer 2.4.2
G-code for a 120×80×12 mm synthetic part on STL and 3MF separately, for
Snapmaker U1, Elegoo Centauri Carbon 2 and Creator 5 Pro. Each emitted 60
layers, declared temperature commands and nonempty extrusion.

- U1: generic bounds/extrusion validation **PASS** on both inputs, but
  vendor-specific executable G-code commands were reported unknown. Registered
  **CANDIDATE**, not a qualified production job.
- Creator 5 Pro: generic bounds/extrusion validation **PASS** on both inputs,
  but vendor-specific executable commands were reported unknown. Registered
  **CANDIDATE**, not a qualified production job.
- ECC2: actual offline slices generated but existing generic validator
  blocked native start service `G180 S7` -> `G1 X127 Y-1.2 F20000`,
  outside declared Y>=0. Registered **BLOCKED**, with no silent relaxation.
- H2D: retains its separate Phase 11 Y=-0.5 **BLOCKED** status; neither
  hardware service envelope has independent verification.

An immutable source fingerprint covers the existing printer matrix, three
native vendor JSON files + one deterministic text-to-CAD wrapper per machine
(four machines including H2D); 17 identities unchanged after the full
six-slice validation. Negative controls block STEP input, over-bed geometry,
injected unsafe G-code coordinates, and both known service-envelope cases.

Phase 14 does not modify the canonical printer profile source of truth,
create duplicate routing authority, bundle upstream AGPL components,
connect to any printer, upload/heat/move, or approve manufacturing. Generic
G-code parser success cannot certify unsupported vendor firmware commands.

Contract: `docs/implementation/ai-3d-modeling-engineering-core/printer-profile-audit-v1.json`.
Evidence: `docs/implementation/ai-3d-modeling-engineering-core/evidence/phase14-printer-profiles-acceptance-20261008.json`.
Validator: `scripts/validate_ai3d_phase14_printer_profiles.py --verify-recorded`.

## Phase 15 command/dialect inventory — static research only

The repository now records **unrecognized executable G-code tokens** from
the six Phase 14 offline STL and 3MF fixture outputs, using their original
SHA-256 receipts and the existing canonical generic G-code parser's literal
supported-command set. This inventory neither recognizes vendor commands
as approved nor connects to devices.

- U1: 29 distinct token types outside the generic parser; 24 appear in
  native machine/process script text. Some are expected Snapmaker macros,
  others generic slicer constructs or conventional G-code such as `G17`.
- ECC2: six token types outside that parser, four mentioned in native source.
  Its documented upstream Orca profile contains the same `G180 S7` and
  `Y=-1.2` sequence, but **physical** service motion is not qualified.
- C5Pro: four unrecognized types, with only `M191` mentioned in the
  native machine start script. An independently verified firmware dialect
  mapping is still missing.
- No source contains production firmware-version attestation. The 17 native
  profile/wrapper/matrix SHA-256 identities stayed unchanged, and each local
  G-code SHA-256 matches the previous accepted fixture receipt.
- Negative tests prove that new unknown commands and malformed tokens are
  surfaced instead of silently accepted. The analyzer executes no G-code.
  A machine or slicer control plane is not introduced.
- The existing U1/C5Pro CANDIDATE and ECC2/H2D BLOCKED status remain
  unchanged. No machine hardware may be heated/moved/started by this route.

Contract: `docs/implementation/ai-3d-modeling-engineering-core/firmware-dialect-audit-v1.json`.
Evidence: `docs/implementation/ai-3d-modeling-engineering-core/evidence/phase15-firmware-dialect-inventory-20261008.json`.
Validator: `scripts/ai3d_phase15_firmware_dialect_inventory.py --verify-recorded`.
