# Bake diagnostics

- Diagnose bake failures by source layer: geometry/high-low relationship -> transforms/normals -> UV/seams/texel density -> cage/ray setup -> tangent basis/normal convention -> image target/color interpretation -> downstream renderer.
- Separate deliberate UV stacking/UDIM use from accidental overlap and verify the active UV set explicitly.
- Use checker/numbered UV tests to reveal stretching, flips, seam placement and registration before baking.
- Inspect normal, AO, curvature and other utility maps directly; a beauty material can hide projection contamination.
- Treat skew, cage misses, projection bleed, visible seams, mirrored tangent errors and padding bleed as different failure classes.
- Do not hardcode universal cage distances or padding pixels; scale, target resolution, filtering and geometry determine them.
- Validate the exported/reimported low asset and the actual baked images, not only the live DCC scene.
- For cross-renderer handoff, separate material identity/binding, texture path/UV/color space, lighting/exposure/display transform and individual lobe diagnosis.
