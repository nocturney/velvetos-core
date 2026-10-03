# Video restoration and enhancement

Use for Topaz Video or another accepted restoration surface after editorial decisions are substantially locked.

- Diagnose the dominant problem first: noise, compression, softness, interlace, motion blur, instability, low resolution or frame-rate need. Do not apply a generic 'enhance' preset to every clip.
- Classify the goal as PRESERVE, RESTORE or CREATIVE. Evidence-bearing and product-identity footage defaults to PRESERVE.
- Discover the model/filter inventory from the installed runtime; model names and versions are volatile and must not be hard-coded as permanent craft rules.
- Process a short demanding test segment before a long job. Compare source and output at real playback speed, not only on a paused frame.
- Diagnose cadence/interlace/timebase and structural defects before enhancement. Repair reversible upstream problems before denoise/upscale when possible; processing in the wrong order can destroy information needed by later stages.
- Keep denoise, upscale, stabilization and interpolation as separable stages unless a tested model/preset intentionally combines them.
- Check temporal shimmer, face/identity drift, edge wobble, texture crawling, oversharpening and plastic skin after every model change.
- Frame interpolation is not restoration of missing ground truth; verify occlusion, fast motion, cuts and repeated patterns carefully.
- Creative/generative enhancement may invent detail. Never use it silently on technical/product evidence or anything requiring exact source fidelity.
- Preserve a clean intermediate after irreversible stages when the job justifies it, so failures can be isolated without recomputing the whole chain.
- Use objective comparison metrics only when source/output alignment is valid; extract worst/stress frames and inspect them visually.
- Record source metadata, model/filter, parameters, output metadata and before/after QA in the job receipt.
