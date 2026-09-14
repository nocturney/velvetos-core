# Video Toolchain Adapters — Velvet Visual Foundry

Status: **implemented adapters; runtime truth remains per engine**.

This layer adapts useful patterns from `browser-use/video-use`, Remotion and Manim **inside the existing Foundry**. It is not another editor product, orchestrator, queue, media catalog or publishing path.

## Routing

1. **Edit Intelligence** (`scripts/vf_video_edit.py`) prepares a deterministic base cut from real/approved media staged for the job. It borrows useful production rules from video-use: audio-first decisions, word-boundary cuts when transcript evidence exists, 30–200ms edge padding, 30ms audio fades, rendered-output inspection and at most three repair passes.
2. **HyperFrames remains the canonical master compositor.** Hebrew RTL overlays, kinetic typography, multi-shot composition and the social master continue through `HYPERFRAMES-BACKEND.json`.
3. **FFmpeg/SVG remains the deterministic fallback** for simple overlays/captions and emergency render equivalence.
4. **Remotion is an optional animation-slot engine, not a renderer replacement.** It is license-gated. Do not install or use it commercially until `vlicense` records eligibility/company-license evidence.
5. **Manim is an optional technical/explainer slot engine.** It is appropriate for diagrams, measurements and geometry explanations, not as proof that a physical print/test/customer result happened.

## video-use adaptation

This is pattern-adapted, not vendored. We do not vendor the upstream repository and do not adopt its own project memory/state as a VelvetOS source of truth. VelvetOS already has Media Vault, Content Contract, Creative Manifest, Edit Director and Evaluation Engine. We only adapt editing mechanics that strengthen those authorities.

The upstream pattern can use word-level transcription. VelvetOS does **not** add a new paid ASR dependency merely to use the editing pattern. If word timestamps exist from an approved ASR source, `cutPolicy=word-boundary` requires the EDL to attest both cut edges are on word boundaries. Without timestamp evidence, use `visual-only`; never pretend word precision was verified.

## Base edit bridge

```bash
python3 scripts/vf_video_edit.py doctor
python3 scripts/vf_video_edit.py validate request.json
python3 scripts/vf_video_edit.py plan request.json
python3 scripts/vf_video_edit.py run request.json
python3 scripts/vf_video_edit.py inspect request.json
```
`run` normalizes clips to one canvas, applies short in/out audio fades, concatenates deterministically, then writes an ffprobe + SHA-256 receipt. It intentionally does not add public Hebrew copy, overlays or publishing metadata; those remain downstream Foundry responsibilities.

`inspect` samples cut boundaries plus beginning/end frames from the rendered output. It is a decision-point view, not frame dumping.

## Remotion license gate

Reviewed integration target: Remotion `4.0.523`. The upstream commercial license has organization-size conditions rather than being an unrestricted MIT-style production license. VelvetOS therefore records Remotion as `license-gated` instead of silently installing it. A future license approval changes only this slot's eligibility; it does not change Foundry authority or QA.

## Manim host gate

Reviewed integration target: Manim `0.21.0` (MIT), requiring Python `>=3.11`. `sderot-windows` now carries an isolated Python 3.12 toolchain and has completed a real 1080×1920 Manim smoke render verified by ffprobe + SHA-256. Status is therefore `host-smoke-verified` for the Windows technical-slot path. Reprovision with `scripts/bootstrap-manim-host-windows.ps1`; do not auto-install Manim during a content job.

## Truth boundary

A generated Remotion/Manim/HyperFrames artifact can illustrate a concept. It does not prove a measurement, physical geometry/result, failure/success, customer outcome or print quality. Asset Truth and Claim Provenance remain authoritative.

## No second runtime

These adapters never own jobs, queues, retries, publication state, Media Vault records or content authority. They consume the existing content job/EDL and return deterministic media artifacts plus evidence to the same Foundry pipeline.
