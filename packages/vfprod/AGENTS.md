# vfprod — fabrication/production local guide

Scope: CAD, STEP/STL/3MF/DXF, engineering drawing, DfAM/DFM, slicing analysis and production planning.

- Route fabrication work through `packages/vfprod/FABRICATION-ROUTER.md` / `scripts/vf_fabrication_router.py`.
- Load only the selected pinned skill/tool instructions returned by the router.
- Verified dimensions/specs are required when geometry depends on them.
- Artifact creation is not physical printer authorization. Printer upload/start/control remains a separate protected external/physical effect.
- Use `TEXT-TO-CAD.md`, `SKILL.md` and the selected DCC/CAD guide only when relevant.
- Cost/spend decisions defer to `policy_id: cost.recurring.new`; never choose a paid fallback silently.
- Instance fleet/material facts are Instance/floor context, not Core root context.

Verification: `python3 scripts/check-vfprod.py`, `python3 scripts/check-vf-fabrication-router.py`.
