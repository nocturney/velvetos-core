# DCC host craft notes

Execution remains on the already accepted local DCC stack.

- Blender: use the existing bounded Blender surface and deterministic gates. Manual retopology is preferred when deformation topology matters; retopology overlay, snapping and Poly Build are useful tools.
- Maya: use Quad Draw/retopology and Maya's modeling tools when the job benefits from character/deformation workflows or existing Maya scene context.
- 3ds Max: use Retopology/ReForm and modifier-based workflows when they fit the existing scene; do not auto-route cloud Flow Retopology because it introduces cloud compute/quota.
- ZBrush: use sculpt, PolyGroups, subdivision, ZRemesher/manual cleanup and UV tools as appropriate, but verify the resulting production mesh outside the sculpt view.
- Meshmixer: treat as a legacy utility/fallback, not a new architectural dependency; Autodesk no longer develops it.
