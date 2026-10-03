---
name: vf-cad-design-craft
description: Apply professional parametric CAD, industrial/product-design and form-development discipline across Fusion, Inventor, AutoCAD, FreeCAD, OpenSCAD and the existing Text-to-CAD stack. Use for dimensioned functional parts, enclosures/products, assemblies, interfaces, fits, threads, tolerances, Fusion Form/surface work, constraint-driven generative exploration, manufacturing masters, or CAD QA. Add craft and verification only; preserve vf-3d-router, Text-to-CAD, DfAM, slicer and printer authority boundaries.
---

# Velvet CAD Design Craft

For VelvetOS production/fabrication work, enter through the mandatory `packages/vfprod/FABRICATION-ROUTER.md` first. Apply CAD design intent and verification only after that authority has selected a CAD/3D route; when it delegates to `vf-3d-router`, follow that route. Do not create a second CAD router or bypass the existing Text-to-CAD, DfAM, slicer or fabrication authorities.

## Workflow

1. Resolve the manufacturing intent, master format, functional interfaces and supplied dimensions before editing geometry.
2. Read only the references needed for the job:
   - `references/product-design.md` for industrial/product-design phase discipline, affordance, cavity, ergonomics and form locking.
   - `references/design-gates.md` for design-DNA lock, maturity gates, source authority and revision-bound evidence.
   - `references/design-intent.md` for sketches, parameters and change resilience.
   - `references/robust-parametric-modeling.md` for change scenarios, dependency control and perturbation/rebuild testing.
   - `references/fusion-form-surfacing.md` for Fusion Form/T-Spline and surface-led product geometry.
   - `references/surface-quality-qa.md` for highlight/zebra/continuity review and Class-A-adjacent diagnostics.
   - `references/fusion-generative.md` for constraint-driven/generative exploration backed by real loads and manufacturing constraints.
   - `references/fits-threads-tolerances.md` for mating interfaces, threads and uncertainty.
   - `references/dfm-gdt-functional-datums.md` for function-first datum strategy, tolerance stacks and process-aware DFM.
   - `references/ergonomics-cmf.md` for population/task-scoped ergonomics and CMF boundary reasoning.
   - `references/assemblies.md` for components, joints, datums and interface ownership.
   - `references/tool-routing.md` for host-specific craft without changing execution authority.
   - `references/verification.md` before delivery.
3. Preserve a parametric or B-rep master when the task requires editable engineering geometry. Do not substitute a mesh master merely because it renders correctly.
4. Encode dimensions and relationships from evidence. Do not invent a fit, clearance, thread standard, material shrink factor or manufacturing tolerance.
5. Keep critical interfaces simple, named and independently measurable. Separate cosmetic form from functional geometry when practical.
6. After material changes, remeasure protected interfaces and rerun the existing DfAM/export gates.

## Design intent rules

- Use the origin, construction geometry, datums and named parameters to express intent instead of accidental coordinates.
- Allow exploratory under-constrained geometry early, but fully constrain production sketches once the intended geometry is known and downstream features depend on it.
- Avoid redundant or contradictory constraints. Prefer the smallest constraint set that expresses the design.
- Use driven/reference dimensions for measurement where a dimension should not control geometry.
- Prefer symmetric, centered and relational definitions when those relationships are the actual design intent.
- Keep feature dependencies shallow enough that expected parameter changes do not cause unrelated failures.

## Hard stops

- Do not guess missing critical dimensions.
- Do not apply a universal FDM clearance, press-fit value or thread compensation.
- Do not replace a required STEP/B-rep master with STL/OBJ/BLEND.
- Do not treat a successful export as proof that dimensions, fit or topology are correct.
- Do not start, upload to or control a printer.

## Completion contract

Report separately: `design_intent_defined`, `geometry_created`, `interfaces_verified`, `export_verified`, `dfam_checked`, and `physical_fit_proven`.
Only claim `physical_fit_proven` from real physical evidence.