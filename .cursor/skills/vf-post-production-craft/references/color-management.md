# Color management and pipeline

Resolve color interpretation before creative grading or compositing.

- Identify source encoding/color metadata first: camera/log/raw interpretation, still-image profile, CG/render space or already-display-referred source.
- Keep input transform, working space, creative look and display/output transform conceptually separate so errors can be diagnosed.
- Record the OCIO/ACES/config version or equivalent project color-management state when reproducibility matters.
- Work in a scene-referred or otherwise appropriate managed space for operations that assume scene-linear relationships; do not perform lighting/compositing math in an arbitrary display encoding.
- Choose the working space for the actual pipeline rather than assuming ACEScg/ACEScct is mandatory for every job.
- Match exposure, balance and scene continuity before adding the creative look.
- Use scopes plus the intended display path. No single skin-line, IRE or saturation target replaces visual intent and source truth.
- Check gamut compression/clipping, highlight behavior and saturated emitters after transforms.
- Review the final output transform and encoding for each required delivery such as SDR/HDR rather than deriving one by blind conversion from the other.
- Never grade around an incorrectly tagged or interpreted source.
- Perform a readback by re-opening a representative rendered output through the intended display/output path; a correct project setting does not prove the encoded file is interpreted correctly.

When a project uses ACES/OCIO, treat current approved configs as data assets; the craft Skill should not fork a parallel color-runtime stack.