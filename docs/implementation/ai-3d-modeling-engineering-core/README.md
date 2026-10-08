# AI 3D Modeling & Engineering Core

Status: isolated implementation; no runtime authority change.

This directory implements the staged capability-expansion plan from the 2026-10-07 START HERE handoff. It does not replace or bypass an existing VelvetOS authority.

## Authority boundaries

The following remain authoritative and unchanged:

- Fabrication Router: packages/vfprod/FABRICATION-ROUTER.json
- Fabrication policy: packages/vfprod/FABRICATION-ROUTER.md
- 3D specialist router: .cursor/skills/vf-3d-router/SKILL.md
- CAD execution bridge: scripts/vf_cad.py and scripts/vf_cad_stack.py
- CreativeCraft live runtime registry
- Blender Capability Host and station routing
- Existing slicer and printer safety boundaries

Nothing here grants printer network control, upload/start-print, machine control, production publication authority, or a second routing authority.

## Isolated baseline

Worktree: D:\Velvet\Worktrees\ai-3d-modeling-engineering-core-20261007
Branch: feat/ai-3d-modeling-engineering-core-20261007
Base: origin/main@47f74c7f39d6f4868e8be930992e744734f561fd

Runtime state was checked before implementation and overrides stale handoff snapshots.

## Phase 0 - readiness

phase0-readiness-baseline-20261007.json records G1-G4 GREEN:

- Office 2.0 Phase 3B is PILOT_ACTIVE/GREEN.
- cam.toolpath is promoted/proven and cross-station tested.
- the worktree is isolated from the dirty legacy Creative Craft worktree.
- Fabrication Router, vf-3d-router, CAD bridges, tool status and Blender/CreativeCraft registries were snapshotted and hashed.
- targeted authority/router checks passed.

## Phase 1 - capability inventory

phase1-capability-inventory-v0.json snapshots:

- 25 Fabrication Router intents
- 5 CAD engines
- 38 CreativeCraft tools
- 271 Blender providers
- 89 Blender capability labels
- 20 cross-station proven typed capabilities

phase1-overlap-gap-map-v0.json separates provider abundance from proven/promoted capability. The P0 gap is proof/control-plane, benchmark and qualification depth, not another general CAD/mesh/slicer router.

Explicit validation:

  py -3.11 scripts/validate_ai3d_phase1.py

## Phase 2 - CAD Capability Registry v1

Files:

- cad-capability-registry-v1.schema.json
- cad-capability-registry-v1.json
- scripts/build-ai3d-capability-registry.py
- scripts/validate_ai3d_capability_registry.py

The registry is deliberately non-authoritative staging. Existing proven routes are recorded first. Research candidates remain CANDIDATE until fixture, license and resource qualification pass.

Current generated registry after Phase 12: 84 records; 61 PROVEN, 1 ACTIVE_AUTHORITY, 18 CANDIDATE, 1 RESEARCH_ONLY and 3 BLOCKED. Exactly 20 Blender cross-station entries are PROVEN_TYPED. Fabrication-authority engine versions come from the runtimes that vf_cad_stack actually executes; Phase 4-12 PROVEN records require bounded validation evidence.

## Phase 3 - Engineering Contract and common artifact protocol

Files:

- engineering-contract-v1.schema.json
- artifact-report-v1.schema.json
- scripts/ai3d_protocol.py
- scripts/validate_ai3d_phase3.py
- fixtures/phase3/*

Contract invariants:

- source units are explicit and normalized CAD length is mm to align with velvetos.geometry-ir.v1.
- coordinate system and datums are explicit.
- expected bodies, dimensions/tolerances, functional interfaces and material/process assumptions are explicit.
- critical dimensions cannot be assumed or unknown and require evidence.
- hidden dimensions may not be invented.
- printer network control and machine control remain false.

Artifact reports require exact engine/version/adapter/runtime/profile plus SHA-256 and byte count for every input/output artifact. The validator can verify hashes against real files.

Negative tests prove fail-closed behavior for assumed critical dimensions, unresolved manufacturing blockers and tampered artifact hashes.

## Phase 4 - Core exact CAD expansion

Files and authority surfaces:

- packages/vfprod/EXACT-CAD-PATTERNS.json
- packages/vfprod/CAD-ENGINE-REGISTRY.json
- scripts/vf_cad_stack.py
- scripts/ai3d_exact_cad_probe.py
- scripts/validate_ai3d_phase4_exact_cad.py
- evidence/phase4-exact-cad-acceptance-20261007.json
- evidence/phase4-bd-warehouse-runtime-install-20261007.json

Implemented and proven:

- one cross-engine primitive frame: XY-centered, Z-min at zero, then explicit global translate_mm.
- build123d remains primary and preserves STEP+STL as the default artifact set.
- explicit build123d export profiles add 3MF, GLB, DXF and SVG without changing default behavior.
- STEP/3MF/STL/DXF/SVG are reopened and geometry-checked, not accepted merely because files exist.
- CadQuery remains a separate fallback venv and now proves the same fixture bounds as build123d.
- JSCAD remains secondary and proves the same coordinate frame within tessellation tolerance.
- semantic face selection uses geometry predicates and unique extrema; numeric face-index fallback is forbidden.
- planar-mate, concentric-axis, fixed-offset and clearance-interface patterns require explicit datums/dimensions and fail closed on missing evidence.
- bd_warehouse 0.3.0 is installed in the canonical build123d venv with --no-deps; build123d stayed at 0.11.1 and the existing OCP package stayed unchanged.
- first curated bd_warehouse fixtures are SocketHeadCapScrew, HexNut and PlainWasher; broader mechanical packs remain deferred to Phase 5.
- serializer byte identity is recorded but is not falsely required for STEP/3MF/DXF; acceptance requires per-artifact hashes plus deterministic reopened geometry/semantics.

Phase 4 validation:

  py -3.11 scripts/validate_ai3d_phase4_exact_cad.py

## Phase 5 - Mechanical feature packs

Files:

- packages/vfprod/MECHANICAL-FEATURE-PACKS.json
- scripts/ai3d_mechanical_features.py
- scripts/validate_ai3d_phase5_mechanical.py
- evidence/phase5-mechanical-feature-acceptance-20261007.json

Promoted bounded packs:

- fasteners: socket-head cap screw, hex nut and plain washer via bd_warehouse.
- threads: solid ISO thread via bd_warehouse; `simple=true` is explicitly rejected for geometry output because it does not carry a solid.
- gears: bounded spur gear wrapper via bd_warehouse.
- bearings: single-row deep-groove bearing with upstream size-table validation.
- inserts: heat-set insert with upstream provider/size validation.
- magnets: native cylindrical pocket tool with explicit radial and axial clearances; no material/process fit is inferred.
- fits: explicit cylindrical clearance/interference calculator; no fit class or clearance is guessed.
- enclosure: bounded open-top rectangular shell with explicit outer dimensions, wall and floor thickness.

Still CANDIDATE:

- snap-fit: blocked on material strain, print orientation, layer adhesion and cycle-life evidence.
- living hinge: blocked on material/process compatibility, hinge thickness, bend radius and cycle-life evidence.
- sheet metal: blocked until a bend-aware runtime and bend allowance/K-factor policy are qualified.

Phase 5 acceptance executes 11 positive fixtures and 16 adversarial cases. All promoted geometry exports STEP+STL with hashes; invalid parameters and candidate-only packs fail closed.

Phase 5 validation:

  py -3.11 scripts/validate_ai3d_phase5_mechanical.py

## Phase 6 - Mesh / organic / implicit expansion

Files:

- mesh-organic-specialists-v1.json
- scripts/validate_ai3d_phase6_mesh.py
- evidence/phase6-mesh-organic-acceptance-20261007.json
- evidence/phase6-rtree-runtime-install-20261007.json

Proven bounded specialists:

- Trimesh 5.1.1: existing provider proof plus explicit geometry variant-batch fixtures.
- Manifold3D 3.5.4: existing Blender-host boolean/remesh route is reused; no duplicate typed operation is created.
- PyMeshLab 2025.7.post1: existing cleanup/retopology provider is reused and its print-cleanup fixture remains provider-level evidence.
- libigl 2.6.3: bounded simulation-analysis provider record with functional fixture evidence.
- Open3D 0.20.0: bounded reconstruction provider proof with downsample and ICP fixtures.
- native Blender sculpt/voxel-remesh: existing Blender Capability Host providers remain the authority; sculpt.organic is provider-proven but not typed-promoted.
- Trimesh + rtree 1.4.1: signed-distance queries are proven behind an explicit watertight-mesh/query-point contract.

OpenVDB remains CANDIDATE. Neither pyopenvdb nor openvdb has a matching distribution in the canonical Windows geometry runtime, and no Blender-native OpenVDB path is promoted without a reproducible bounded fixture.

The 10 already-promoted mesh/scan typed capabilities are explicitly reused. Phase 6 does not create a second mesh router and does not promote provider proof into PROVEN_TYPED state.

Phase 6 validation:

  py -3.11 scripts/validate_ai3d_phase6_mesh.py
  py -3.11 scripts/validate_ai3d_capability_registry.py

## Phase 7 - Reverse engineering / scan-to-CAD

Files:

- reverse-engineering-scan-to-cad-v1.json
- scripts/ai3d_reverse_engineering.py
- scripts/validate_ai3d_phase7_reverse_engineering.py
- evidence/phase7-reverse-engineering-acceptance-20261007.json
- evidence/phase7-geomdl-runtime-install-20261007.json

The existing Blender-host provider `pipeline_scan_to_cad` remains the composite scan-to-CAD route. Phase 7 does not create a second scan router or CAD authority.

Proven bounded behavior:

- existing scan.pointcloud, scan.clean and scan.register typed capabilities are reused.
- COLMAP 4.2.1, Meshroom 2025.1.0 and Open3D 0.20.0 remain provider components for registration/reconstruction; existing functional evidence is preserved.
- segmentation is explicit: a `segment_ref` selects an upstream/user-provided segment. Automatic semantic feature recognition is not claimed.
- primitive fitting currently supports explicit `box_axis_aligned` and `cylinder_z` families only.
- a synthetic cylinder point cloud with distractor segment fits exactly to diameter 20 mm, height 30 mm and explicit translation; known-dimension anchors are checked and mismatch fails closed.
- the fitted primitive is emitted as `velvetos.geometry-ir.v1`, rebuilt through the existing build123d authority path, exported to STEP and reopened at the expected 20 x 20 x 30 mm bounds.
- geomdl 5.4.0 (MIT) is installed in the existing geometry-core Python 3.12 runtime with `--no-deps`; no existing geometry package changed.
- geomdl least-squares surface fitting is proven behind a structured-grid and explicit fit-error-threshold contract. Its NURBS surface is reconstruction evidence only and never manufacturing truth.
- NURBSFit 2026 remains CANDIDATE_RESEARCH pending GoCoPP C++ qualification, NURBSDiff compatibility, PyTorch3D/CUDA qualification and a reproducible VelvetOS fixture.

Negative controls block missing primitive family, missing segment reference, dimension-anchor mismatch and NURBS fitting without an explicit error threshold.

Capability Registry after Phase 7: 60 records, 46 PROVEN, 13 CANDIDATE, 1 ACTIVE_AUTHORITY, and still exactly 20 PROVEN_TYPED.

Phase 7 validation:

  py -3.11 scripts/validate_ai3d_phase7_reverse_engineering.py
  py -3.11 scripts/validate_ai3d_capability_registry.py

## Phase 8 - Assemblies, motion, collision and ECAD/MCAD

Files:

- assembly-motion-ecad-v1.json
- scripts/ai3d_assembly_motion_ecad.py
- scripts/validate_ai3d_phase8_assembly_ecad.py
- evidence/phase8-assembly-ecad-acceptance-20261007.json

Proven bounded behavior:

- build123d 0.11.1 RevoluteJoint fixture uses an explicit Z-axis and 0-180 degree range; the 15-degree sampled sweep detects the expected obstacle collision window and blocks an out-of-range 181-degree request.
- static collision is measured by exact B-Rep intersection volume; the fixture is clear at non-colliding states and reaches approximately 199.529 mm^3 collision volume at 45 degrees.
- FreeCAD 1.1.3 Assembly runs headless with Assembly::AssemblyObject, Assembly::JointGroup, a grounded part and a real Fixed joint. The solver converges and emits FCStd + STEP evidence.
- KiCad CLI 10.0.6 exports the installed Arduino Nano template as a board-only STEP. Reopened board bounds are 43.18 x 17.78 x 1.51 mm.
- the existing pipeline_pcb_to_enclosure is reused. A clearance-positive enclosure reports 0 mm^3 interference; the negative fixture reports approximately 165.263 mm^3.
- component-complete KiCad STEP remains CANDIDATE_BLOCKED_FIXTURE because the installed Arduino Nano template references KICAD9_3DMODEL_DIR .wrl headers that do not resolve in the KiCad 10 model tree.
- URDF/Pinocchio remains CANDIDATE_NOT_INSTALLED. It is optional and will only be admitted if a real articulated-mechanism task exceeds the proven build123d/FreeCAD joint path.

Capability Registry after Phase 8: 68 records, 52 PROVEN, 15 CANDIDATE, 1 ACTIVE_AUTHORITY, and still exactly 20 PROVEN_TYPED.

Phase 8 validation:

  py -3.11 scripts/validate_ai3d_phase8_assembly_ecad.py
  py -3.11 scripts/validate_ai3d_capability_registry.py

## Phase 9 - Drawings, vectors and sheet metal

Files:

- drawings-vectors-sheetmetal-v1.json
- scripts/ai3d_drawings_vectors_sheetmetal.py
- scripts/validate_ai3d_phase9_drawings_vectors_sheetmetal.py
- evidence/phase9-drawings-vectors-sheetmetal-acceptance-20261007.json

Proven bounded behavior:

- FreeCAD 1.1.3 TechDraw runs headless with a real DrawPage, DrawSVGTemplate and DrawViewPart. The formal drawing fixture emits a complete DXF and reopens it independently through ezdxf/build123d.
- DXF acceptance is fail-closed: a projection fragment is not accepted as a DXF file, and an intentionally invalid DXF is rejected by the independent parser.
- build123d text/glyph fixtures cover Latin and Hebrew text using an explicit Arial font name. DXF round-trip preserves the fixture bounds within 1e-6 mm; SVG is accepted within 0.001 mm. No font file is copied or bundled.
- FreeCAD SheetMetal 0.8.24 is pinned at commit a1cf212d8b86b3849e5cc12070226d5d4bded2a3 in an isolated runtime. NetworkX 3.5 is injected from a separate isolated site-packages directory; the global FreeCAD installation is unchanged.
- Sheet-metal unfold requires explicit thickness, bend radius, K-factor and K-factor standard. The fixture uses 1 mm thickness, 1 mm radius and K=0.38 ANSI, unfolds one 90-degree bend, emits a complete DXF with 8 LINE entities, and reopens at 60 x 48.16769893 mm planar bounds.
- Draftwright 0.4.34 is installed only in an isolated evaluation venv. It remains CANDIDATE: the package is AGPL-3.0, Alpha, and resolves build123d 0.10.0 because it requires build123d <0.11, while the canonical runtime remains build123d 0.11.1.
- The license classifier explicitly treats AGPL as review-required before generic GPL matching, preventing Draftwright from contaminating the commercial-clean lane.

Capability Registry after Phase 9: 73 records, 56 PROVEN, 16 CANDIDATE, 1 ACTIVE_AUTHORITY, and still exactly 20 PROVEN_TYPED.

Phase 9 validation:

  py -3.11 scripts/validate_ai3d_phase9_drawings_vectors_sheetmetal.py
  py -3.11 scripts/validate_ai3d_capability_registry.py

## Phase 10 - Simulation, optimization and TPMS research

Files:

- simulation-optimization-v1.json
- fixtures/phase10/axial-bar-tension.json
- scripts/ai3d_simulation_contract.py
- scripts/ai3d_phase10_freecad_driver.py
- scripts/validate_ai3d_phase10_simulation.py
- scripts/ai3d_tpms_research.py
- evidence/phase10-simulation-acceptance-20261008.json

The existing FreeCAD 1.1.3 FEM runtime includes Gmsh 4.15.0 and CalculiX 2.22 as CLI executables; no new solver or parallel authority was installed. A synthetic steel axial-tension reference bar (40 x 10 x 10 mm; 210000 MPa Young's modulus; Poisson 0.30; explicitly fixed x-min face; 10 MPa outward pressure on x-max face) is verified by real second-order Gmsh volume meshing and a genuine CalculiX linear-static solve.

- Coarse mesh: 1052 nodes, 493 volume elements, mean end displacement 0.001888454 mm.
- Fine mesh: 2018 nodes, 1033 volume elements, mean end displacement 0.001889190 mm.
- Analytical elastic reference: 0.001904762 mm; fine-mesh relative error 0.8175%; normalized intermesh displacement difference 0.03894%.
- Both solver runs yield .inp/.frd/.dat/FCStd artifacts with SHA-256 and byte-count receipts.
- 12 adversarial contract controls block missing/inferred material, loading, supports, unsafe/unbounded resources, mismatched units and unauthorized optimization acceptance.
- The bounded TPMS gyroid periodic-level-set experiment remains RESEARCH_ONLY. It outputs no manufacturable mesh and makes no strength or printability claim.
- SfePy and DOLFINx remain CANDIDATE_NOT_INSTALLED; automated design optimization acceptance remains BLOCKED.
- Gmsh and CalculiX are reused as external FreeCAD-bundled CLI tools. Binary redistribution or bundling requires separate GPL compliance review; proving a local solve does not authorize a product bundle.
- The Fabrication Router, printer, slicer and machine safety boundaries are unchanged. This fixture is not structural certification or a customer design.

Phase 10 validation:

  py -3.11 scripts/validate_ai3d_phase10_simulation.py
  py -3.11 scripts/validate_ai3d_capability_registry.py

## Phase 11 - DfAM and slicer validation

Files:

- dfam-slicer-v1.json
- scripts/validate_ai3d_phase11_dfam_slicer.py
- evidence/phase11-dfam-slicer-acceptance-20261008.json

The existing `vf_cad.py` and `gcode_tool.py` are reused as the sole offline slicer authority; no new slicer router or native machine profile was written. OrcaSlicer 2.4.2 is used as a standalone installed CLI and remains subject to its AGPL-3.0 licensing and no-bundling-without-review policy.

- The synthetic 120 x 80 x 12 mm Geometry IR source is built through the existing build123d CAD authority to STEP, STL and 3MF with SHA-256 receipts. STEP/STL/3MF are reopened and bounds/mesh topology validated.
- The existing DfAM tool measures geometrical support/overhang estimates. This is not a strength assessment, certified fit, or manufacturing approval.
- Real offline Orca slicing from both STL and 3MF succeeds with the existing Flashforge Creator 5 `c5` profile: both emit 60 layers, 12.05 mm reported max-z, nonempty extrusion and temperature commands, and G-code accepted by the canonical bounds validator.
- The real H2D native machine-start script contains `G1 X270 Y-0.5 F60000`, while the current generic validation profile declares Y >= 0 mm. The generated Orca G-code therefore remains BLOCKED_MOTION_BOUNDS until an independently verified service-motion envelope can be adopted. No machine limits were silently relaxed.
- The 4 negative checks block out-of-bed geometries, STEP submitted directly for slicing, injected out-of-range G-code and unsupported H2D start motion. All native profile and wrapper hashes remain unchanged.
- Other printers (`u1`, `ecc2`, `c5pro`) are not marked proven by this Phase 11 fixture.
- `PROVEN_OFFLINE_ONLY` is a CLI/toolchain claim, not a printer-firmware command audit, calibrated material claim or production print authorization. All device upload/start/network controls remain disabled.

Phase 11 validation:

  py -3.11 scripts/validate_ai3d_phase11_dfam_slicer.py
  py -3.11 scripts/validate_ai3d_capability_registry.py

## Phase 12 - Bounded offline CAM and GRBL verification

Files:

- cam-toolpath-v1.json
- fixtures/phase12/rect-outline.json
- scripts/ai3d_cam_contract.py
- scripts/ai3d_phase12_freecad_post.py
- scripts/ai3d_cam_gcode_validator.py
- scripts/validate_ai3d_phase12_cam.py
- evidence/phase12-cam-acceptance-20261008.json

The pre-existing `cam.toolpath` PROVEN_TYPED route remains unchanged, preferring mac-mini-office with Fabex CNC 3.0.2 and Windows fallback. This phase does not create another CAM routing operation or change the CreativeCraft station configuration.

- Existing cross-station Fabex `rect_cutout_grbl_v1` report and G-code were checked for unchanged SHA-256, exact fixed profile, Mac/Windows provenance and fresh Windows-side independent G-code validation. The historical Mac execution was not repeated or falsely described as a fresh dispatch.
- FreeCAD 1.1.3 CAM/Path `grbl_post` runs headless and produces actual GRBL output from synthetic, explicitly specified contour waypoints; it is a proven **postprocessing** path only, not a stock-aware machining operation.
- Both variants agree within 0.15 mm contour bounds on a 40 x 30 mm outer rectangular benchmark with 3 mm end mill, two passes to -1 and -2 mm, 5 mm safe clearance, 5/10 mm/min plunge/cut feed and 12,000 rpm *synthetic fixture* spindle reference.
- The independent modal parser accepts the two bounded GRBL dialects while blocking 18 adversarial alterations, including G20/inches, G91/incremental, M4/laser, heater codes, excessive feeds, out-of-envelope travel, rapid below stock, incorrect spindle, missing shutdown and trailing commands.
- The input contract separately blocks 15 invalid/unqualified material, tool, geometry, feed, units, postprocessor, machine and safety cases.
- A `PROVEN_PROVIDER` record is added only for FreeCAD GRBL post. The existing 20 PROVEN_TYPED records stay at 20; `cam.qualified_machining_process` is BLOCKED until real-material cutting data, workholding, tool collisions, machine envelope and independent acceptance exist.
- No printer upload/start, CNC dispatch, spindle/laser actuation, actual machining or automatic manufacturing approval occurred.

Phase 12 validation:

  py -3.11 scripts/validate_ai3d_phase12_cam.py --artifacts-root D:\\Velvet\\Artifacts\\AI3D\\YYYY-MM-DD\\new-phase12-artifact-directory
  py -3.11 scripts/validate_ai3d_capability_registry.py

## Phase 13 - Integration against latest origin/main

The Phase 12 feature tree at `9d9e4be2` was reconciled against
`origin/main@a2d065cb` in an isolated Phase 13 worktree. Git
reported no conflicts; the reviewed local merge commit is `ca4037d8`.
The upstream main changes (Office 2.0, DeerFlow comparative-research policy
and other unrelated work) were preserved without modification of their source.

- Phase 10 Gmsh/CalculiX two-mesh FEM recheck: PASS, no machine control.
- Phase 11 STEP/STL/3MF -> Orca offline slicing recheck: PASS, C5 STL and 3MF each 60 layers; H2D remains BLOCKED_MOTION_BOUNDS.
- Phase 12 FreeCAD GRBL post + reused historical Fabex cross-station proof recheck: PASS, 15 malformed CAM requests and 18 bad G-code mutations blocked.
- Windows path normalization in the Phase 11 validator compares canonical resolved paths rather than literal string spelling. No G-code safety bound was relaxed.
- Full merged-tree regression: 118/118 PASS; sensors reported no repository file mutations.
- Merge receipt: `evidence/phase13-integration-acceptance-20261008.json`.
- Full suite log: `evidence/check-all-phase13-integrated-main-20261008.log`.
- Subsequent `origin/main@08fd11f8` competitor-research update was merged separately at commit `755301dc` without conflicts or modifying upstream source. The Office Phase 2, fabrication and capability registry checks passed, followed by another full 118/118 merged-tree regression.
- Latest-main receipt: `evidence/phase13-latest-main-acceptance-20261008.json` and `evidence/check-all-phase13-latest-main-20261008.log`.
- These are local feature-branch merges, not evidence that remote GitHub `main` has already been updated.

## Phase 14 - Additional printer profiles, offline only (2026-10-08)

Phase 13/PR #601 merged on GitHub `main` at `8ee3b5a4`.
Phase 14 was developed on a separate feature branch based on
`main@d838d790`; it is not a claim of hardware qualification or printer activation.

Evidence and sources:

- `printer-profile-audit-v1.json`
- `scripts/validate_ai3d_phase14_printer_profiles.py`
- `evidence/phase14-printer-profiles-acceptance-20261008.json`
- `packages/vfprod/CAD-ENGINE-REGISTRY.json` (pointer, not source of truth)
- The existing `slicer-router/printer_matrix.json` remains authoritative; no duplicate slicer router or local/native printer profiles were edited

A new copy of the explicit 120 x 80 x 12 mm synthetic Geometry IR fixture
was exported as STEP/STL/3MF, then genuinely sliced by the already-installed
OrcaSlicer 2.4.2 through the canonical `vf_cad.py` bridge.
Both STL and 3MF generated G-code for all three profiles, with 60 layers
and explicit nozzle/bed commands:

| Profile | Offline slicer+generic validator | Manufacturing / firmware status |
|---|---|---|
| Snapmaker U1 | Both STL and 3MF passed generic XY/Z bounds and extrusion | CANDIDATE: vendor-specific executable commands unaudited |
| Flashforge Creator 5 Pro | Both STL and 3MF passed generic XY/Z bounds and extrusion | CANDIDATE: vendor-specific executable commands unaudited |
| Elegoo Centauri Carbon 2 | Both generated output; generic validator rejected native service move `G1 X127 Y-1.2 F20000` following `G180 S7` | BLOCKED_MOTION_BOUNDS: independent service envelope needed |
| Bambu H2D | Phase 11 native Y=-0.5 failure retained; not requalified | BLOCKED_MOTION_BOUNDS |

Generated files are external offline artifacts; the git evidence includes
SHA-256 hashes and bounded command reports, not production G-code to be
flashed or uploaded. The generic parser leaves some vendor-specific commands
unrecognized, including U1-specific and C5Pro machine macros; a clean generic
motion report is **not** a safe-firmware certification.

The source snapshot includes three native files and one deterministic wrapper
for each of U1, C5Pro, ECC2 and H2D, plus the canonical matrix (17 SHA-256
identities total). Every source file and wrapper was hash-identical
before/after.
Negative fixtures block STEP input, oversized geometry, injected unsafe
U1/C5Pro motions, ECC2 negative-Y movement and unchanged H2D service travel.
No profile rewrite, printer network/upload/start, temperature action or physical
machine motion was performed.

Read-only receipt verification:

  py -3.11 scripts/validate_ai3d_phase14_printer_profiles.py --verify-recorded

To repeat on a connected authorized Windows host only, use an unused, isolated
destination below `D:/Velvet/Artifacts/AI3D`:

  py -3.11 scripts/validate_ai3d_phase14_printer_profiles.py --capture-root D:\\Velvet\\Artifacts\\AI3D\\YYYY-MM-DD\\new-proof-directory

All vendor firmware dialect, workholding/print reality, material calibration,
print-start and machine-service-motion permissions require separate,
model-specific provenance, tests and explicit production authority.

Phase 14 integration onto `main@75410a2f` was reviewed as local merge
`2fc3d9b4`, without conflicts. Office v2 Phase 3B, fabrication and AI3D
validators passed, followed by the full 118/118 regression. The phase remains
in the feature branch pending GitHub PR/CI and is not a production release.
Integration receipt: `evidence/phase14-main-integration-acceptance-20261008.json`.
Full-suite log: `evidence/check-all-phase14-integrated-main-20261008.log`.

## Validation state

Explicit AI3D validation stack: PASS. Current integration branch tested against
`origin/main@08fd11f8` for Phase 13. Phase 14 runs independently on
`main@d838d790` with an additional 118/118 regression. Physical H2D/CNC
and automatic manufacturing-release gates remain blocked.


Repository regression:

- scripts/check-all.py: 118/118 PASS
- exit code: 0
- sensor side-effect check: repository files unchanged
- Phase 14 full-suite log: evidence/check-all-phase14-20261008.log

## Next implementation phase

Next: after Phase 14 is independently integrated, qualify vendor-specific U1/C5Pro firmware commands and separately investigate ECC2/H2D service-motion envelopes using authoritative device evidence. Unverified profiles remain blocked for production. Material/tool qualification and automatic manufacturing approval also remain explicitly deferred.
