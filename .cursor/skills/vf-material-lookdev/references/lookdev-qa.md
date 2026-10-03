# Lookdev QA

1. Inspect the material in a neutral/reference lighting setup for baseline response.
2. Inspect under at least one alternate environment or light angle to expose roughness, normal and reflection issues.
3. Check at close and intended-view distances for scale-dependent noise or tiling.
4. Verify seams, UV borders, texture padding and mip/filter behavior where the target viewer permits.
5. Compare material cues against the source/reference: color family, roughness range, reflectance behavior, relief scale and wear logic.
6. Disable complex effects one channel at a time when diagnosing a problem.
7. Export textures using the destination template/convention, then re-import or inspect exact files.

A pleasing viewport screenshot is not enough; the exported maps must remain coherent in the destination pipeline.