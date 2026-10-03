# Texture pipeline QA

Use between authored/generated source images and final DCC material binding.

- Inspect source resolution, channel count, bit depth, alpha, declared/assumed color space and intended semantic role before conversion.
- Separate color transforms from data-channel handling. Roughness, metalness, normals, masks and similar data are not display-referred color.
- Validate the OCIO/config identity used for conversion when color-managed transforms are part of the pipeline.
- Generate renderer-optimized tiled/mipmapped textures only after source interpretation is correct; optimization cannot repair a wrong color transform.
- Keep the original source texture and deterministic conversion recipe/provenance so runtime textures can be regenerated.
- Check normal-map convention, alpha behavior, premultiplication expectations and channel packing before binding.
- Re-open or inspect generated textures and compare dimensions/channels/metadata with the recipe.
- On cross-DCC handoff, verify that named spaces and texture semantics survive rather than assuming matching filenames imply matching interpretation.

This is pipeline QA, not a second material-authoring authority.