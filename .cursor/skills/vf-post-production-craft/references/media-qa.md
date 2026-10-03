# Media QA and regression

Use objective metrics as evidence, never as the sole definition of quality.

- Align reference and processed streams before comparison: frame count, PTS/timebase, resolution/crop and color interpretation must match the intended comparison.
- Record the metric implementation/model/version. VMAF model choice is part of provenance.
- Prefer per-frame results plus aggregate statistics; averages can hide severe local failures.
- Extract worst-N frames or ranges for visual inspection when the metric supports per-frame scoring.
- Combine complementary probes when useful: perceptual quality, SSIM/PSNR-style structural comparison, color difference, banding and direct frame differences.
- For restoration/enhancement, separately inspect temporal flicker, edge shimmer, warping, face/identity drift, text corruption, hallucinated detail and grain/texture destruction.
- Compare at real playback speed and at relevant viewing scale. A sharpened frame can score better while looking less faithful.
- Keep a source-fidelity policy: PRESERVE work must reject invented evidence even when a metric improves.
- Use golden/reference clips for regression after model/runtime changes, but refresh them only through explicit approval.

Passing metrics means only that the declared comparison passed its criteria; it does not prove creative superiority.