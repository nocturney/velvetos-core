# Surface quality QA

Use for freeform/product surfaces where highlight behavior and continuity are part of the design quality.

- State continuity intent at every important boundary: deliberate positional break, tangent transition or curvature-smooth transition.
- Evaluate silhouette, section fairness and reflected-highlight flow; a visually smooth viewport under one light is not evidence of fair surfaces.
- Use sparse control topology and stable patch boundaries. Extra control points or T-Spline faces can introduce waviness without adding useful control.
- Inspect long reflections or zebra-style bands across transitions to reveal pinching, flat spots and oscillation.
- Check curvature/comb behavior where the host exposes it, especially through blends and inflection zones.
- Keep poles, extraordinary vertices and trim boundaries away from hero highlight paths when practical.
- Distinguish a designed crease from a continuity defect. Not every boundary should be G2-smooth.
- Test under at least one neutral/high-contrast reflection environment before material beauty work.
- Recheck protected interfaces after surface edits and after conversion between Form/T-Spline, surface and B-rep representations.
- Capture comparable review views so a later revision cannot hide degraded continuity with a new camera or light.

Do not claim Class-A compliance unless the actual project defines that requirement and the accepted toolchain can measure it.