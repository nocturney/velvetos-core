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

Current generated registry: 42 records; 33 PROVEN, 1 ACTIVE_AUTHORITY, 8 CANDIDATE. Exactly 20 Blender cross-station entries are PROVEN_TYPED. Fabrication-authority engine versions come from the runtimes that vf_cad_stack actually executes; bd_warehouse is registered as a bounded proven primitive capability after Phase 4 host acceptance.

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

## Validation state

Explicit AI3D validation stack: PASS.

Repository regression:

- scripts/check-all.py: 116/116 PASS
- exit code: 0
- sensor side-effect check: repository files unchanged
- full-suite log: evidence/check-all-phase4-20261007.log

## Next implementation phase

Phase 5 is the mechanical feature-pack layer: fasteners/threads/gears/bearings/inserts/magnets/fits/snap-fit/living-hinge/enclosure/sheet-metal packs, with unit tests and adversarial parameter/property tests. Mature upstream libraries should be wrapped rather than copied.
