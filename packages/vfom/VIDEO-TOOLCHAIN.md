# Video Toolchain Adapters — Velvet Visual Foundry

Status: **implemented adapters; runtime truth remains per engine**.

This layer adapts useful patterns from `browser-use/video-use`, Remotion and Manim **inside the existing Foundry**. It is not another editor product, orchestrator, queue, media catalog or publishing path.

## Routing

1. **Edit Intelligence** (`scripts/vf_video_edit.py`) prepares a deterministic base cut from real/approved media staged for the job. It borrows useful production rules from video-use: audio-first decisions, word-boundary cuts when transcript evidence exists, 30–200ms edge padding, 30ms audio fades, rendered-output inspection and at most three repair passes.
2. **HyperFrames remains the canonical master compositor.** Hebrew RTL overlays, kinetic typography, multi-shot composition and the social master continue through `HYPERFRAMES-BACKEND.json`.
3. **FFmpeg/SVG remains the deterministic fallback** for simple overlays/captions and emergency render equivalence.
4. **Remotion is an optional animation-slot engine, not a renderer replacement.** Current owner business headcount is 1, so it is **Free License eligible** for commercial use and automation. Re-check only if relevant project/company headcount reaches 4+ or upstream terms change.
5. **Manim is an optional technical/explainer slot engine.** It is appropriate for diagrams, measurements and geometry explanations, not as proof that a physical print/test/customer result happened.

## Brand assets for compositions

Owner decision 2026-09-28: the verified brand fonts are **Rubik** (Hebrew headline 700, subhead 600) and **Cinzel** (Latin 700/400), shipped as OFL variable TTFs under `packages/vfbrand/assets/fonts/`. Logos (owner rasters and the owner-approved traced transparent SVGs) are under `packages/vfbrand/assets/logo/`. Compositions read paths, hashes, roles and layout limits from `packages/vfbrand/brand-tokens.json` (`brandAssets` in `VIDEO-TOOLCHAIN.json` points there). No other font family is used.

## Rich Reel templates and real-print-file turntable

The owner-approved Reel compositions live under `packages/vfom/hyperframes/templates/` and read `packages/vfbrand/brand-tokens.json` plus a per-Reel variables file. Hebrew layers are explicit RTL; Rubik/Cinzel and the exact SVG logo come only from the token paths. The shared runtime implements `HEADLINE_REVEAL`, `ACCENT_RULE_WIPE`, `CHIP_SEQUENCE`, `INSET_POP` and the relevant existing Velvet presets as deterministic HyperFrames/GSAP timelines.

Render with the repository root as the HyperFrames project and the template as the composition, for example `hyperframes render . -c packages/vfom/hyperframes/templates/rich-still-reel.html --variables-file <vars.json> --strict-variables`. Media variables are repo-relative paths (`packages/...`) bound with `data-var-src`, so HyperFrames discovers the hero/inset images, extracts the real-motion video and mixes the audio track; the runtime resolves brand tokens, fonts and the logo relative to `velvet-reel.js`. Each template loads GSAP 3.14.2 from jsDelivr (the HyperFrames default), so the render host needs that URL reachable or cached.

`scripts/vf_turntable.py` is a subordinate product-motion adapter. It imports a **real print file** (.3mf/.stl/.obj/.glb/.gltf/.blend) in Blender, preserves source geometry, renders a loopable 6–8s 1080x1920@30fps turntable in warm interior lighting, and records an input/output SHA-256 receipt. Colour stays embedded from the print file or uses an explicitly verified hex + evidence source. It never AI-generates the product and never authorizes publication.

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

Remotion uses a `latest-compatible` policy. `4.0.523` is retained only as the version against which the current integration/license review was recorded, not as an execution pin. Owner/business headcount is currently 1; Remotion's current Free License covers individuals and organizations up to 3 people, including commercial use and automation. Re-check eligibility at 4+ relevant people or if upstream terms change. Remotion remains optional and subordinate to Foundry authority/QA.

## Manim host gate

Manim uses a `latest-compatible` policy with `0.21.0` retained as the minimum/recovery baseline (MIT; Python `>=3.11`). The existing `sderot-windows` evidence records a real 0.21.0 / Python 3.12 1080×1920 smoke render verified by ffprobe + SHA-256; that evidence is historical proof, not a runtime lock. Reprovisioning accepts a newer compatible Manim after version/host smoke checks. Do not auto-install or upgrade Manim during a content job.

## Truth boundary

A generated Remotion/Manim/HyperFrames artifact can illustrate a concept. It does not prove a measurement, physical geometry/result, failure/success, customer outcome or print quality. Asset Truth and Claim Provenance remain authoritative.

## No second runtime

These adapters never own jobs, queues, retries, publication state, Media Vault records or content authority. They consume the existing content job/EDL and return deterministic media artifacts plus evidence to the same Foundry pipeline.
