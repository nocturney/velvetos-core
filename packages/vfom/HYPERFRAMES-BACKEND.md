# HyperFrames Render Backend - Velvet Visual Foundry

Status: active backend contract for Velvet Factory video composition/render.

HyperFrames is a deterministic render backend inside the existing `vfom` pipeline. It is not a second orchestrator, state machine, media catalog, creative authority, or publish path. Creative decisions remain in `CREATIVE-AUTOPILOT.md`, `EDIT-DIRECTOR.md`, the Content Contract, Creative Manifest, Visual OS, Media Vault, Brand Guardian and the existing publish preflight.

## Why this backend exists

The Foundry already requires deterministic composition/render, especially for Hebrew overlays and derivatives. HyperFrames fills that capability with HTML/CSS/media/seekable animation -> rendered video while preserving the existing truth, brand and QA gates.

Use it when the edit needs multi-shot composition, kinetic type, designed overlays, motion graphics, repeatable branded layouts, or deterministic Hebrew text. Keep the existing FFmpeg/SVG path as a failover and as the cheaper path for simple caption burn-in or a single static overlay.

## Ownership boundaries

- Creative Director decides concept, shots, hook, EDL and overlay intent.
- Media Vault supplies real asset refs, rights and Asset Truth.
- vfcopy owns public Hebrew wording. HyperFrames never invents public copy.
- Visual OS / Visual DNA own composition and brand rules.
- HyperFrames owns only deterministic composition and render execution.
- Brand Guardian / Evaluation Engine still decide whether the rendered artifact passes.
- vfigos still owns Instagram publish and live verification.
- A render receipt proves a file was produced and probed. It is never a publish receipt.

## Canonical routing

`Content Contract -> Creative Manifest -> Edit Director -> media resolution -> HyperFrames composition -> check -> rough render -> Evaluation/Repair -> final render -> ffprobe receipt -> derivative factory -> publish preflight`

The machine-readable policy is `HYPERFRAMES-BACKEND.json`. Render requests use `HYPERFRAMES-RENDER.schema.json`. Host execution goes through `scripts/vf_hyperframes.py`.

## Host requirements

The render host is Edge/Office, not the Core catalog runtime.

- Node.js >=22
- a locally installed `hyperframes` CLI at exactly `0.8.35`
- FFmpeg + ffprobe

Installation/cache preparation happens outside a content job on an authorized render host. The bridge performs no dependency download, no `npx` fallback and no silent version switch. `doctor` fails closed when the binary is missing or its version differs from the configured pin. Updating the pin requires reviewing current HyperFrames release behavior, then updating the backend config, bridge constant and sensor together.

## Render stages

### Rough

Use `quality=draft`. The goal is cheap rejection and repair before expensive final work. Rough output is not publishable evidence.

### Review

Use `quality=standard` when a higher fidelity internal comparison is needed.

### Final

Use `quality=high` plus strict-all lint. Final still must pass the existing deterministic/perceptual/reference/artifact checks, copy receipt, rights/claim gates and publish preflight.

The Foundry default remains at most two final renders per content job.

## Hebrew and visible copy

Never ask a generative video model to render Hebrew inside footage when the text can be composed deterministically. Hebrew first-frame hooks, covers and overlays must originate from the existing vfcopy chain and then be rendered as HTML/SVG/text layers. HyperFrames solves rendering fidelity; it does not replace copy quality review.

For RTL compositions:

- set document/overlay direction explicitly (`dir=rtl` or CSS `direction: rtl`);
- use only verified existing brand fonts/templates;
- keep line wrapping deterministic and test the exact final strings;
- preserve Instagram safe zones;
- compare against the no-text baseline where the Visual Copy policy requires it.

## Media truth

Composition source media must resolve to concrete Media Vault assets or explicitly approved generated support assets. Do not invent a missing product view. Synthetic/illustrative visuals may provide atmosphere, transition or support only; they do not prove product geometry, measurements, stress results, failure/success or customer outcomes.

## Frame contract

`HYPERFRAMES-FRAME.md` is the camera/render translation layer for Velvet visual rules. It intentionally contains no invented colors or fonts. It points compositions back to verified brand/template sources.

## Bridge usage

Validate a request and inspect the exact pinned commands without rendering or resolving a binary:

```bash
python3 scripts/vf_hyperframes.py plan path/to/render-request.json
```

Check host prerequisites and the exact HyperFrames version without installing anything:

```bash
python3 scripts/vf_hyperframes.py doctor
```

Run on an authorized render host:

```bash
python3 scripts/vf_hyperframes.py run path/to/render-request.json
```

A successful run performs HyperFrames `check`, renders with the requested stage settings, verifies the result with ffprobe, requires portrait video and required audio, computes SHA-256 and writes a `.receipt.json` next to the output unless another in-project receipt path is provided.

## Failover

If HyperFrames is unavailable or fails after one actionable retry, route the affected render to the existing `ffmpeg-svg-caption-composition` path when that path can preserve the intended artifact. Do not lower the Content Contract, copy, truth, rights or QA thresholds to make a backend pass.

If neither backend can produce the required artifact, report a render blocker. This is not automatically a human creative-choice gate; escalate only under the existing Human Intervention Policy.
