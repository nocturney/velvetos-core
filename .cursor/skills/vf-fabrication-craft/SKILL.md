---
name: vf-fabrication-craft
description: Apply professional additive-manufacturing print-prep, slicer calibration, orientation/support, profile and G-code QA practice across OrcaSlicer, PrusaSlicer, Bambu Studio and vendor reference slicers. Use for preparing a verified model for slicing, diagnosing profile/calibration issues, planning supports/orientation, or reviewing generated G-code. Preserve existing DfAM, slicer and printer boundaries; never upload, start, heat or control a printer.
---

# Velvet Fabrication Craft

Enter through the mandatory `packages/vfprod/FABRICATION-ROUTER.md` for every VelvetOS fabrication request. Add fabrication craft only after the router-selected geometry/DfAM chain reaches print-prep. Keep the upstream `gcode` skill, `vf_cad.py`, printer matrix, DfAM and physical-printer authority unchanged.

## Workflow

1. Resolve printer, nozzle, material, filament instance, process/profile, part function and required surface/fit priorities.
2. Read the needed references: `calibration.md`, `orientation-supports.md`, `dfam-lifecycle.md`, `profile-discipline.md`, `gcode-qa.md`, `verification.md`, `tool-routing.md`.
3. Use current calibrated evidence for the specific machine/material/profile combination. If it is stale or missing, treat calibration as unresolved rather than inventing settings.
4. Slice only after the model and orientation are explicit.
5. Review preview/G-code evidence before handoff to the human printer operator.

## Core rules

- Separate geometry defects from slicer/profile defects.
- Treat filament brand, formulation, color, nozzle and machine as potentially relevant to flow/temperature behavior.
- Use calibration artifacts to establish settings; do not copy universal speed, flow, pressure-advance, retraction or clearance values.
- Choose orientation as a tradeoff among functional strength, dimensional accuracy, surface quality, support burden and print risk.
- Preserve a known-good vendor/profile baseline before tuning.

## Hard stops

- Never upload/start/heat/move/control a printer.
- Never mark a digital slice as a successful physical print.
- Never overwrite a known-good profile without a reversible copy/version.
- Never infer part strength or food/safety suitability from slicer settings alone.

## Completion contract

Report `model_checked`, `profile_resolved`, `calibration_current`, `orientation_reviewed`, `supports_reviewed`, `slice_generated`, `gcode_reviewed`, and `physical_print_proven` separately.