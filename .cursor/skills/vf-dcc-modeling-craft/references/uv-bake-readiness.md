# UV and bake readiness

- Decide whether the asset requires unique UVs, mirrored/stacked regions, UDIMs or no texture UVs at all before unwrapping.
- Place seams where discontinuities are acceptable and where they support flattening with controlled distortion.
- Check UV overlap intentionally: distinguish deliberate stacking from accidental overlap.
- Keep texel density reasonably consistent for regions that need comparable visual detail, unless priority regions justify a difference.
- Leave sufficient island padding for the target resolution/filtering pipeline; do not hardcode a universal pixel value without target evidence.
- Before baking, freeze the low/high relationship, verify transforms/normals and confirm the tangent/normal convention expected downstream.
- Inspect normal, AO, curvature and other baked utility maps directly. Do not judge the bake only through a finished material.
- Treat visible seams, skew, projection contamination and cage misses as bake defects to repair at their source.
