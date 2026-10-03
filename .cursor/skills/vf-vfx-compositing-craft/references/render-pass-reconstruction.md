# Render-pass reconstruction

- Confirm pass identity, premultiplication, color space, alpha behavior and renderer semantics before rebuilding beauty.
- Reconstruct only passes that are intended to combine mathematically; do not invent a generic AOV formula across renderers.
- Compare the reconstructed result against the accepted beauty/reference before using the graph for creative adjustment.
- Keep utility/data passes distinct from display color and avoid display transforms inside linear arithmetic.
- Document any pass that is missing, approximated or intentionally excluded.
- Upstream material/lighting truth remains owned by the 3D/material pipeline; comp adjustments must not silently redefine the asset.
