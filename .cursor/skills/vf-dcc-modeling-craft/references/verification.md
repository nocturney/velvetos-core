# DCC geometry verification

Check the exact deliverable or a re-opened export.

1. Compare silhouette/proportions against the locked reference or source measurements.
2. Inspect topology density, poles, non-manifold edges, accidental internal geometry and normals.
3. For deformation use, test representative bends/poses rather than declaring success from a bind pose.
4. For subdivision, inspect for pinching, waviness and support-loop artifacts at final subdivision level.
5. For UV assets, inspect seams, distortion, overlap intent and packing state.
6. For bake targets, inspect the baked maps individually and the final shaded result.
7. For printed output, pass the result back through the existing 3D/DfAM pipeline; DCC mesh QA is not print proof.
