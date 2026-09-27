# CAD Engine Stack — completion checkpoint

Date: 2026-09-27
Branch: feat/cad-engine-stack-20260927
Base: origin/main

## Implemented

- Existing build123d/cadgen path retained as primary CAD engine.
- CadQuery 2.8.0 installed in isolated Python 3.12 venv under VelvetPrintLab and verified by real STEP/STL export.
- JSCAD installed in isolated local Node workspace and verified by binary STL export plus DfAM mesh inspection: 20x30x10 mm, 12 triangles, watertight, one body.
- Unified machine-readable CAD engine registry added under vfprod.
- Geometry IR v1 schema + validator added; dimensions are explicit and never inferred.
- Bounded repair state allows exactly two repair iterations, then FALLBACK_REQUIRED.
- CAD/CAE Copilot cloned at commit 6e851d3cf513f5ab4225093bd0b5ab35db317663, installed locally without LLM extras, and its MCP smoke passed in stubbed-cad mode with 98 tools.
- Forgent3D cloned at commit d538ca46d9c3766a0a21ba73ba88607ef305dedd. Source/pilot is present but runtime build is intentionally unverified because pnpm is absent; no extra runtime was installed solely to force green.
- Graph-CAD and Multi-Agent-CAD incorporated only as IR / bounded-workflow patterns; no second runtime.
- awesome-cad registered in vfresearch/LINKS.json as ecosystem radar only.
- CADAM explicitly rejected as runtime and not installed.
- Fabrication Router remains the single authority; printer network/upload/start/heating/motion remain disabled.
- All four new cost preflights PASS as FREE_LOCAL.

## Verification

PASS:
- scripts/check-vf-cad-stack.py
- scripts/check-vf-fabrication-router.py
- scripts/check-policy-architecture.py
- scripts/check-critical-syntax.py
- scripts/vf_cad_stack.py doctor
- scripts/vf_cad.py doctor
- git diff --check
- Stage 2A sensor registry audit: 96 sensors, registry matches live

Full suite:
- First run without UTF-8 completed and recorded 26 failures, dominated by Windows cp1252 decode/encode failures.
- Re-run with PYTHONUTF8=1 cleared those encoding failures through the first 22 sensors, then the suite was interrupted inside check-living-studio.py.
- Direct execution of check-living-studio.py with PYTHONUTF8=1 reproduces the same KeyboardInterrupt during its selftest subprocess.
- Therefore the full repository suite is UNPROVEN, not green. This blocker is outside the CAD change surface and was not masked or bypassed.

## Host evidence

See:
- packages/vfharness/state/cad-engine-stack-host-acceptance-2026-09-27.json
- packages/vfharness/state/cad-engine-stack-20260927/check-all.json

## Safety / cost

- Paid provider calls performed: NO
- LLM extras enabled for Copilot: NO
- Printer control enabled: NO
- Production route switched to pilot runtimes: NO
- CADAM installed: NO

## Remaining non-CAD blocker

Investigate the existing living-studio selftest KeyboardInterrupt before claiming a fully green repository suite.

## Rollback

All Core changes are isolated on this branch. Heavy local runtimes live under:
C:\Users\Chris\Documents\VelvetPrintLab\tools\cad-stack

Revert the local branch commit to remove Core wiring. Removing local tool directories is optional and independent from Core rollback.
