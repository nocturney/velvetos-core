# Assemblies and interface ownership

- Use components/parts to reflect real replaceable or independently manufactured items.
- Give each functional interface one clear owner. Avoid duplicated driving dimensions in multiple components when one source can drive the relationship.
- Define assembly location from functional datums and joints/constraints, not visual alignment.
- Protect interfaces that other parts reference; cosmetic edits must not silently change them.
- Check motion or clearance only over the range required by the design; do not infer real-world load or wear behavior from collision-free CAD motion.
- For derived or linked geometry, record the source and refresh state before sign-off.
- Before export, confirm component orientation, units, part count and whether the receiving workflow expects individual parts or an assembly structure.
