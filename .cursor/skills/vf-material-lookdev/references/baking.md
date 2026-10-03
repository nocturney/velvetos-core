# Baking craft

- Confirm low-poly, high-poly and cage/match strategy before baking.
- Use match-by-name or equivalent isolation when nearby parts would contaminate one another.
- Inspect cage intersections and projection misses. In current Substance Painter, visible cage intersections are an explicit warning sign for bake artifacts.
- Use a custom cage when automatic/distance-based projection cannot cleanly describe the surface relationship.
- Set output resolution and dilation from target needs; do not hardcode one value for all assets.
- Inspect normal, world-space normal, AO, curvature, position, thickness and ID maps as applicable.
- Read the bake log and treat warnings/errors as QA evidence.
- For skewed projections, fix geometry/cage/projection direction or use bounded skew-correction tooling rather than accepting distorted detail.
- Re-bake after geometry, UV, hard-edge or normal changes that invalidate the previous maps.