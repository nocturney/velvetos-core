# CAD Engine Stack — implementation spec

## Goal
Extend the existing vfprod/text-to-cad path with a single engine contract that can detect and verify build123d/cadgen, CadQuery and JSCAD locally, while keeping CAD/CAE Copilot and Forgent3D as bounded pilots. Add a Geometry IR contract and a deterministic bounded-repair state machine without introducing a second agent runtime.

## Non-goals
- No printer network control, upload or print start.
- No paid model/API calls.
- No LangGraph/Aider/Multi-Agent-CAD production runtime.
- No Graph-CAD model/checkpoint installation.
- No CADAM runtime.
- No replacement of Fabrication Router or VelvetPrintLab printer matrix.

## Authority / SoT
AGENTS.md; packages/vfprod/FABRICATION-ROUTER.md; packages/vfprod/TEXT-TO-CAD.md; constitution/NO_NEW_RECURRING_COST.md; packages/velvetos/LAYERS.md.

## Acceptance criteria
1. Existing build123d/cadgen route remains PASS.
2. CadQuery is isolated locally and can headlessly export valid STEP and STL.
3. JSCAD is isolated locally and can headlessly export STL.
4. Core exposes one machine-readable CAD engine registry and doctor.
5. Geometry IR validates hierarchy, primitives, dimensions and explicit constraints without inventing dimensions.
6. Bounded repair permits at most two repair iterations before fallback/block.
7. CAD/CAE Copilot and Forgent3D are cloned/probed as pilots only; no paid provider or parallel control plane is enabled.
8. awesome-cad is registered as ecosystem radar, not installed as runtime.
9. Fabrication/router sensors and full repository checks remain green.

## Evidence
Targeted CAD stack sensor + vf_cad/vf_fabrication_router doctors + actual local export probes + check-all.

## Risk / gates
NO_NEW_RECURRING_COST; no secrets; no provider credentials; no printer actions; no second runtime.
