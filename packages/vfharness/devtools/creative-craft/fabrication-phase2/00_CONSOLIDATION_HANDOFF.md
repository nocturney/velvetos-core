# 00 — Consolidation Handoff: Fabrication / CAD / Slicer

Date: 2026-10-01
Status: PHASE 2 FABRICATION WORK COMPLETE / READY FOR CONSOLIDATION

## Read first

1. `FABRICATION-INTEGRATION-PLAN.md` — complete routing policy, tool roles, slicer policy, evidence boundaries and gap ownership.
2. `fabrication-adapter-contract.json` — machine-readable proposed Creative Craft adapter contract.
3. `CONSOLIDATION-PATCH.md` — exact recommended shared Creative Craft registry/router changes.
4. `phase2-validation-receipt.json` — hashes and PASS validation evidence.

## Authority rule

Do not create a second fabrication router, printer matrix, slicer authority, 3D router or CAD engine registry.
Creative Craft adds one thin `fabrication` adapter and delegates all fabrication intent resolution to `packages/vfprod/FABRICATION-ROUTER.*`.
The existing `vf-3d-router` remains a sub-router entered only when selected by the Fabrication Router.

## Implemented here

The canonical Fabrication Router now correctly resolves the five owner acceptance examples.
Existing-mesh repair/refinement routes through DfAM → existing 3D router → DfAM.
Reference reconstruction with protected interfaces routes through native vision → existing 3D router.
The 3D router now recognizes explicit STL/3MF wording and reference reconstruction cues.
Regression tests were extended and pass.

## Verified acceptance

- `design a printable threaded bracket` → `functional_part_to_print`.
- `reconstruct this reference and preserve exact mounting holes` → `reference_reconstruction`.
- `make this STL printable` → `additive_redesign`.
- `create an engineering drawing from the model` → `engineering_drawing_pdf`.
- `slice for U1 and validate the G-code` → `slice_and_validate`.

`check-vf-3d-router.py` = PASS.
`check-vf-fabrication-router.py` = PASS.
`vf_cad.py doctor` = PASS with canonical Orca, canonical `gcode discover` now sees PrusaSlicer, and printer-control safety remains false.
`vf_cli_anything.py doctor` = PASS after restoring the isolated runtime; strict acceptance = 106 headless tests plus real U1 DfAM/slice/validate PASS.
Shared `CreativeCraftRouter.py` and `creative-craft-registry.json` hashes still exactly match Creative Craft Milestone 1.

## Work intentionally left elsewhere

**Runtime Repairs:** Maya currently needs post-update compatibility repair before it may enter fabrication routing; OpenSCAD Nightly update-health remains owned there. Prusa backend discovery is now healthy.

**Missing Integrations:** typed OpenSCAD subordinate CAD provider; bounded Prusa profile-parity/fallback adapter under canonical gcode/vf_cad; optional bounded Fusion feature writes; SketchUp/LayOut automation; XVL integration; optional typed Meshmixer repair.

**Skills Research:** OpenSCAD procedural workflows; SketchUp spatial planning; XVL technical publication; engine-neutral mesh repair workflows.

## Consolidation action

Apply only the proposed thin Creative Craft integration from `CONSOLIDATION-PATCH.md`.
Do not add direct slicer fallbacks into Creative Craft.
Do not promote Bambu/Elegoo/Flash to automatic slicer authority.
Do not expose physical printer control.
