# VelvetOS Blender stack — local routed execution

Status: **INTEGRATED CONTRACT · LOCAL RUNTIME MUST PASS `python scripts/vf_3d.py doctor`**
Seat: **production** (`vfprod`) through the existing `expert-3d-model`.
This is not a new pack, runtime, printer controller or source of truth.

## Decision

VelvetOS does not expose one generic "Blender agent". The canonical entrypoint is:

```text
request
  -> python scripts/vf_3d.py route --request "..."
  -> TEXT_TO_CAD | BLENDER_NATIVE | HYBRID_CAD_THEN_BLENDER
  -> geometry/print QA
  -> STL/3MF + master source
  -> existing OrcaSlicer dry-run / human floor handoff
```

Functional parametric work stays on `TEXT-TO-CAD.md`. Blender is selected for organic,
sculptural, reference-driven and existing-mesh work. Mixed jobs keep a STEP functional
master before Blender refinement instead of converting Blender into a CAD authority.

## Primary Blender controller

Primary interactive controller: [PatrykIti/blender-ai-mcp](https://github.com/PatrykIti/blender-ai-mcp),
pinned by the local install receipt to commit
`43253155440f78ce208f7c4264bb8be6fb784ec7` (upstream v3.3.0 line).

VelvetOS uses its curated `llm-guided` / macro / measure / assert surface. Raw Python is
not the normal public contract. The local add-on is **patched before use** from upstream
`HOST = "0.0.0.0"` to `127.0.0.1` and uses the reserved local port `18765`; `vf_3d.py doctor`
fails unless this hardening is visible. An open TCP port is not evidence by itself: when Blender
is live, the doctor performs the framed Blender RPC `ping` protocol and reports `PASS`, `OFFLINE`
or `FAIL` rather than mistaking another local service for Blender.
External OpenRouter/Gemini/provider vision is disabled. The component is classified
`PAID_OPTIONAL` only because those optional upstream paths exist; VelvetOS locks the
selected mode to zero incremental cost and supplies no paid-provider credentials.

The canonical MCP adapter is `llm-guided` over `stdio`, with the prompt bridge disabled,
`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1` and `HF_DATASETS_OFFLINE=1`.
This keeps the normal bootstrap surface at nine tools and prevents the upstream LaBSE
router from downloading a model at runtime. If LaBSE is absent locally, the upstream
router falls back to local keyword/TF-IDF-style resolution. Acceptance on this host proved
both the nine-tool bootstrap and a goal-first `picnic_table_workflow` match while offline.

Local root:

```text
%VELVET_PRINTLAB_ROOT%\tools\blender-ai-mcp
```

The MCP adapter is optional. ChatGPT can use the same stack immediately through the
authorized host connection and `scripts/vf_3d.py`; Cursor/other MCP clients may consume
`python scripts/vf_3d.py mcp-config`. MCP is an adapter, not the only control path.

## Geometry / print evidence

[design-os-3d-blender](https://github.com/jangtrinh/design-os-3d-blender) is the local
headless QA layer, pinned to commit
`61390fd535d812a1763ec0d2b3fd9304591fa3e0`.

It contributes Blender 5.2 knowledge, `AGENT_OK / AGENT_FAIL` execution contracts,
part-spec validation and the production geometry gate. A gate PASS is digital geometry
evidence only; it is not proof of load, fit, material behavior or a successful physical print.

Local root:

```text
%VELVET_PRINTLAB_ROOT%\tools\design-os-3d-blender
```

Upstream host tests document macOS/Linux; Windows support is therefore never assumed.
Promotion on this host requires the real `vf_3d.py benchmark` against the installed Blender.
## Workflow knowledge, not another runtime

[RobLe3/cc-blender-skill](https://github.com/RobLe3/cc-blender-skill) is used as a
reference library for source-locked reconstruction, multiview refinement, fit repair,
UV/texture and quality-loop patterns. VelvetOS does **not** install its Claude Code
orchestrator and does not depend on Claude for this route.

## Legacy fallback

[ahujasid/mcp-for-blender](https://github.com/ahujasid/mcp-for-blender) is legacy/fallback
only. If a bounded task genuinely requires it, keep the socket on localhost, set
`BLENDER_MCP_SAFE_MODE=1`, disable telemetry where supported, and do not enable Premium,
Hyper3D, Hunyuan3D or other paid/external generation. Its unauthenticated socket and broad
Python surface are why it is not the default VelvetOS controller.

## Commands

```bash
python scripts/vf_3d.py route --request "..."
python scripts/vf_3d.py doctor
python scripts/vf_3d.py benchmark
python scripts/vf_3d.py run-pass --script <job-root/script.py>
python scripts/vf_3d.py gate --scene <part.blend> --spec <part.spec.json> --report <report.json>
python scripts/vf_3d.py mcp-config
```

`run-pass` only accepts scripts under `VELVET_3D_JOB_ROOT` and applies a local static
safety gate before Blender. Final manufacturing checks still flow through `vfprod`,
`vlicense`, the printer matrix and the existing slicer route.

## Hard boundaries

- no printer upload, start, heat, home, jog or network control;
- no new recurring cost and no paid API/provider call without explicit owner approval;
- no external vision/provider escalation from a local failure;
- no synthetic claim that a digital gate proves a physical print;
- no second printer matrix, second production SoT or second office runtime;
- no Blender-first route for work whose engineering master belongs in STEP/B-rep.

Verification: `python scripts/check-vf-3d-router.py`, then `python scripts/vf_3d.py doctor`
and a real `python scripts/vf_3d.py benchmark` on the target host.
