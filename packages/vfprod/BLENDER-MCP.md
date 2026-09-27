# VelvetOS Blender stack — local routed execution

Status: **INTEGRATED CONTRACT · LOCAL RUNTIME MUST PASS `python scripts/vf_3d.py doctor`**
Seat: **production** (`vfprod`) through the existing `expert-3d-model`.
This is not a new pack, runtime, printer controller or source of truth.

## Decision

The canonical entrypoint is:

```text
request
  -> python scripts/vf_3d.py route --request "..."
  -> TEXT_TO_CAD | BLENDER_NATIVE | HYBRID_CAD_THEN_BLENDER
  -> geometry/print QA
  -> STL/3MF + master source
  -> existing slicer dry-run / human floor handoff
```

Functional parametric work stays on `TEXT-TO-CAD.md`. Blender is selected for organic,
sculptural, reference-driven and existing-mesh work. Mixed jobs keep a STEP functional
master before Blender refinement instead of converting Blender into a CAD authority.

## Version policy — capability, not allowlist

VelvetOS is **version-agnostic** for this stack. It uses the installed version that is
actually present on the host and accepts it by capability checks, not by a hard-coded
Blender release, MCP release, source commit or slicer release.

- `BLENDER_BIN` may explicitly select Blender; otherwise `vf_3d.py` discovers installed
  Blender executables and selects the highest observed installed version.
- The selected Blender must expose the `blender_ai_mcp` addon in that same Blender
  installation, with the addon enabled and its installed RPC file passing the loopback
  hardening contract.
- `blender-ai-mcp` and `design-os-3d-blender` report their installed version from their
  local package metadata. A receipt is valid only when its recorded version matches the
  version currently installed. There is no permitted-version list.
- After a component upgrade, rerun acceptance/benchmark evidence before making a release
  acceptance claim. Runtime discovery may proceed when live capability checks pass; stale
  historical evidence is not a version ban.
- Exact versions, source revisions, hashes and paths in receipts are provenance snapshots
  of what was tested, never runtime pins.

The same rule applies to OrcaSlicer in `vf_cad.py`: the matrix executable/version fields
are hints and evidence. Runtime discovery checks `ORCASLICER_BIN`, PATH, VelvetPrintLab
tool directories and common local install locations, then uses the best installed candidate.

## Primary Blender controller

Primary interactive controller: `blender-ai-mcp`.

VelvetOS uses its curated `llm-guided` / macro / measure / assert surface. Raw Python is
not the normal public contract. The local addon must be hardened to loopback
`127.0.0.1`; its RPC port is resolved from the installed hardened addon rather than
assumed from a release number or fixed runtime constant.

An open TCP port is not evidence by itself. When Blender is live, `vf_3d.py doctor`
performs the framed Blender RPC `ping` protocol and distinguishes a real Blender endpoint
from another local service.

External OpenRouter/Gemini/provider vision is disabled. The component remains
`PAID_OPTIONAL` only because those optional upstream paths exist; VelvetOS supplies no
paid-provider credentials and does not auto-escalate to them.

The canonical MCP adapter uses `llm-guided` over `stdio`, disables the prompt bridge,
sets `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1` and `HF_DATASETS_OFFLINE=1`, and
keeps vision and telemetry off. If the optional LaBSE model is not cached locally, routing
falls back to local keyword/resolver paths rather than downloading a model at runtime.
The accepted bootstrap surface on this host contains nine tools.

Local root:

```text
%VELVET_PRINTLAB_ROOT%\tools\blender-ai-mcp
```

The MCP adapter is optional. ChatGPT can use the same stack through the authorized host
connection and `scripts/vf_3d.py`; other MCP clients may consume
`python scripts/vf_3d.py mcp-config`. MCP is an adapter, not the only control path.

## Geometry / print evidence

`design-os-3d-blender` is the local headless QA layer. Upstream releases may describe a
particular Blender target, but VelvetOS does not convert that description into a version
lock. The installed Blender is accepted only after the real headless and production-gate
capability path succeeds on this host.

It contributes `AGENT_OK / AGENT_FAIL` execution contracts, part-spec validation and the
production geometry gate. A gate PASS is digital geometry evidence only; it is not proof
of load, fit, material behavior or a successful physical print.

Local root:

```text
%VELVET_PRINTLAB_ROOT%\tools\design-os-3d-blender
```

## Workflow knowledge, not another runtime

`cc-blender-skill` is a reference library for source-locked reconstruction, multiview
refinement, fit repair, UV/texture and quality-loop patterns. VelvetOS does not depend on
its Claude runtime.

## Legacy fallback

`mcp-for-blender` remains legacy/fallback only. If a bounded task genuinely requires it,
keep the socket on localhost, enable its safe mode where supported, disable telemetry where
supported, and do not enable Premium or paid/external generation. Its broad Python surface
is why it is not the default controller.

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
safety gate before Blender.

## Hard boundaries

- no printer upload, start, heat, home, jog or network control;
- no new recurring cost and no paid API/provider call without explicit owner approval;
- no external vision/provider escalation from a local failure;
- no synthetic claim that a digital gate proves a physical print;
- no second printer matrix, second production SoT or second office runtime;
- no Blender-first route for work whose engineering master belongs in STEP/B-rep;
- no runtime allowlist tied to a specific tool version or upstream commit.

Verification: `python scripts/check-vf-3d-router.py`, then `python scripts/vf_3d.py doctor`
and a real `python scripts/vf_3d.py benchmark` on the target host.
