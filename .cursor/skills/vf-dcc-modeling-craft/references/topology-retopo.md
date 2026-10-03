# Topology and retopology

- Start from downstream behavior: static render, subdivision, deformation, baking or print repair.
- Preserve silhouette first. Spend topology where curvature, deformation or shading needs it.
- Prefer even, intentional edge spacing over arbitrary density; local density changes should have a reason.
- Keep loops coherent around joints, mouths, eyes or other deformation zones when animation/deformation is required.
- Move unavoidable poles and high-valence junctions away from critical deformation and highlight regions when practical.
- Remove accidental doubles, zero-area faces, unintended internal faces and isolated geometry.
- Check face orientation/normals and smoothing behavior after topology changes. For hard-surface assets, inspect long specular highlights; for deforming assets, test representative deformation rather than judging wireframe alone.
- For manual retopo, use the high-resolution form as a reference surface and continuously compare silhouette/proportions.
- Automatic retopology can be acceptable for static or intermediate use after inspection; do not assume it is animation-ready.
- Capture evidence appropriate to the target: neutral turntable for static/shading review, extreme-pose/deformation checks for rigged assets, or bake comparisons for low-poly targets.
