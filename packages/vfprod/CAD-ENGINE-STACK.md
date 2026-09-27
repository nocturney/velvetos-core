# CAD Engine Stack

VelvetOS keeps one fabrication authority: `FABRICATION-ROUTER.md`. This stack adds interchangeable execution engines beneath the existing `cad` route; it is not a second control plane.

## Roles

- build123d/cadgen — primary, already verified through text-to-cad.
- CadQuery — secondary B-Rep engine in an isolated Python 3.12 venv.
- JSCAD — secondary lightweight CSG engine in an isolated local Node workspace.
- CAD/CAE Copilot — pilot adapter only; local MCP/backend is allowed, external model-provider calls are not enabled by this integration.
- Forgent3D — pilot workbench only; local visual/rebuild loop, not production authority.
- Graph-CAD — IR design inspiration only.
- Multi-Agent-CAD — decompose → generate → inspect → bounded repair pattern only; no LangGraph/Aider production runtime.
- awesome-cad — ecosystem radar only.
- CADAM — not installed.

## Geometry IR

`GEOMETRY-IR.schema.json` is a small explicit intermediate representation for hierarchy, primitive dimensions and assembly constraints. Missing dimensions stay missing; the validator never infers or invents them. Buildable primitive parts may declare `operation: add|cut` and `translate_mm: [x,y,z]`.

## Chat/runtime build bridge

A fabrication chat request is resolved by `vf_fabrication_router.py decide`, then represented explicitly as Geometry IR, then executed with `vf_cad_stack.py build --engine auto`. Auto selects the first verified local engine in order: build123d, CadQuery, JSCAD. The bridge emits local artifacts plus `build-receipt.json` with SHA-256 evidence and never uploads to or controls a printer. The generic bridge currently builds explicit box/cylinder boolean models; unsupported geometry fails closed and must route through the existing CAD skill/code-generation path rather than inventing geometry.

## Bounded repair

`vf_cad_stack.py repair-next` permits two repair iterations. A third failure returns `FALLBACK_REQUIRED`; it never loops indefinitely.

## Host paths

All heavy runtimes live under `%VELVET_PRINTLAB_ROOT%\tools\cad-stack\` and are intentionally excluded from Core. Core stores only contracts, routing, sensors and evidence.
