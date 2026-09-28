# Velvet Motion Presets


| Preset | Use | Avoid | Default duration |
|---|---|---|---|
| `HEADLINE_REVEAL` | Bring in the exact approved Hebrew hook after the real product is already visible | Generic title cards or text before product | 0.45-0.65s |
| `ACCENT_RULE_WIPE` | Reveal the one product-following accent rule attached to the headline | Decorative rules disconnected from hierarchy | 0.30-0.50s |
| `CHIP_SEQUENCE` | Introduce up to three verified-fact chips one at a time | Unverified features or simultaneous clutter | 0.22-0.35s per chip |
| `INSET_POP` | Introduce one verified SAME_FRAME_CROP / ALTERNATE_VERIFIED_SOURCE inset | Synthetic details or repeated gratuitous cards | 0.30-0.45s |
| `VELVET_HARD_CUT` | Default transition between meaningful actions | Decorative scene changes | instant |
| `VELVET_MACRO_PUNCH` | Emphasize a mechanical/material detail | Repeated zooms on every beat | 0.20-0.45s |
| `VELVET_FAILURE_FLASH` | Mark a real failed iteration or break point | Fake failure or synthetic proof | 0.10-0.25s |
| `VELVET_PROOF_FREEZE` | Freeze on a verified result, dimension or outcome | Unsupported claims | 0.7-1.4s |
| `VELVET_BLUEPRINT_OVERLAY` | Explain geometry, dimensions or relation between parts | Decorative technical graphics without evidence | 0.8-2.5s |
| `VELVET_STRESS_SLOWMO` | Real stress/load moment where slowdown improves comprehension | Generic beauty shots | 0.5-2.0s |
| `VELVET_MATERIAL_LABEL` | Consistent material identification such as Nylon/ASA/PETG | Long explanatory cards | 0.8-1.8s |
| `VELVET_FINAL_STAMP` | Very short final conclusion or verified state | Long logo outro | 0.4-0.9s |

## Implementation

The four rich-editorial presets and `VELVET_HARD_CUT`, `VELVET_MACRO_PUNCH`, `VELVET_MATERIAL_LABEL`, and `VELVET_FINAL_STAMP` are implemented in `packages/vfom/hyperframes/velvet-reel.js` as paused GSAP timeline helpers. HyperFrames owns seek/playback; templates register the populated timeline only after brand tokens and `document.fonts.ready` resolve.

## Rules

- Hard cut is the default.
- Use slow motion only for a meaningful proof/test moment.
- Keep real studio sound audible when it increases credibility.
- Use verified brand fonts/colors/templates only. Missing verified token means reuse an existing approved template rather than inventing one.
- Motion must support the story, subject hierarchy or proof. If removing an effect improves clarity, remove it.
- Never let a motion treatment imply a physical measurement, stress result, failure or success that is not supported by real evidence.
