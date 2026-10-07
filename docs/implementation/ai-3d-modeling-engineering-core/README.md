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

Current generated registry: 41 records; 31 PROVEN, 1 ACTIVE_AUTHORITY, 1 READY_BOUNDED, 8 CANDIDATE. Exactly 20 Blender cross-station entries are PROVEN_TYPED.

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

## Validation state

Explicit AI3D validation stack: PASS.

Repository regression:

- scripts/check-all.py: 116/116 PASS
- exit code: 0
- sensor side-effect check: repository files unchanged
- full-suite log: evidence/check-all-phase3-20261007.log

## Next implementation phase

Phase 4 is exact-CAD expansion. It must harden the existing build123d primary adapter and CadQuery fallback, qualify bd_warehouse/OCCT-related primitives where useful, add deterministic export/reopen fixtures, and preserve the existing Fabrication Router authority and isolated environment boundaries.
