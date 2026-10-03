# CAD host craft notes

Execution authority remains with vf-3d-router and the accepted local adapters.

- Fusion: favor named parameters, constrained production sketches, components and explicit assembly relationships. Use current installed capability rather than pinning a version in this skill.
- Inventor: use model parameters, driven dimensions where appropriate, part/assembly separation and tolerance analysis when stack-up matters.
- AutoCAD: use it for precise DWG/DXF drafting and geometry when history-based solid modeling is not the primary requirement; keep units and coordinate systems explicit.
- FreeCAD: use the existing bounded adapter for explicit workbench or headless operations; preserve the canonical DfAM/slicer path after export.
- OpenSCAD Nightly: treat Nightly as intentional. Discover current syntax/capability at runtime; do not recommend stable merely because the installed build is Nightly.
- Text-to-CAD/build123d/cadgen: keep as the preferred route for functional parametric generation when it already covers the request; this craft skill supplies design discipline, not a competing engine.
