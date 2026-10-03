# OpenPBR material reasoning

Use OpenPBR as a shared material vocabulary when the target stack supports it or when cross-renderer reasoning benefits from a renderer-neutral model.

- Reason in layers and physical roles rather than memorized renderer sliders: substrate/base response, dielectric/metal behavior, roughness/anisotropy, transmission/absorption/SSS, coat, fuzz and emission as applicable.
- Keep color-bearing channels and data channels under the correct color interpretation.
- Treat roughness, IOR, coat and transmission as interacting optical decisions; do not tune each in isolation.
- Preserve energy-conserving behavior and avoid compensating for a broken light/exposure setup by pushing material parameters to extremes.
- Use measured/reference evidence when claiming physical accuracy. Artistic materials may depart from reality, but the departure should be intentional.
- Intermediate metalness can represent transitions or layered/painted conditions; do not enforce a false universal 0-or-1 rule.
- Do not impose arbitrary universal base-color or roughness clamps. The official material model defines parameter domains; project-specific plausible ranges need material/reference evidence.
- Validate under neutral and alternate lighting, and compare the same material intent across target renderers when portability matters.
- Record renderer-specific mapping or unsupported lobes separately from the craft reference.

Canonical semantics come from the current OpenPBR specification; local adapters own application-specific parameter names.