# Fusion form and surface craft

Use when Autodesk Fusion is the engineering master but the product needs controlled freeform or Class-A-adjacent shape development rather than a simple sketch/extrude stack.

- Protect datums, attachment points, interfaces, envelope limits and keep-out zones before shaping cosmetic surfaces.
- Build silhouette and major section curves first; use guide curves only when they express a real transition or design line.
- Keep T-Spline/Form control topology as sparse and intentional as the desired curvature permits. Extra faces create more opportunities for waviness.
- Judge front, side, top and reflected-highlight behavior; do not accept a surface only because one perspective view looks smooth.
- Maintain tangent/curvature continuity intentionally across transitions that should read as one surface, and allow deliberate breaks where the design calls for an edge.
- Use symmetry while it accelerates exploration, then break it only for a functional or art-direction reason.
- Convert to B-rep only after the form is stable enough that downstream parametric features should reference it.
- Add functional cuts, bosses, mounting interfaces, shell/wall logic and manufacturing features after the exterior form is controlled.
- After every major form edit, remeasure protected interfaces and inspect downstream rebuild health.
- If sculptural freedom becomes more important than an editable CAD master, use the routed DCC/ZBrush path for form exploration and return to CAD for protected engineering interfaces.

A smooth viewport is not proof of a good surface. Inspect highlight flow, section fairness, continuity and exact interface geometry.
