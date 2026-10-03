# Robust parametric modeling

Use when a CAD model must survive expected dimensional or configuration changes.

- List expected change scenarios before modeling: what is likely to grow, move, disappear, repeat, switch configuration or remain protected.
- Anchor stable intent to origin geometry, datums, layout/skeleton sketches and named parameters instead of incidental generated faces.
- Keep master/layout geometry focused on envelopes and interfaces. Let local feature sketches own local detail.
- Minimize dependency depth. A downstream feature should reference the most stable upstream definition that expresses the intended relationship.
- Prefer simple, readable and fully constrained production sketches once their design intent is settled.
- Order features by stability and ownership: primary volumes and functional interfaces before repeated/detail/cosmetic finishing when the process allows it.
- Avoid attaching critical downstream sketches or dimensions to fragile topology created by late fillets, chamfers or pattern instances unless that topology is truly the authority.
- Name important parameters, sketches, features and bodies/components so another operator can infer their purpose.
- Run perturbation tests before sign-off: change representative parameters across realistic ranges, rebuild, then inspect protected interfaces, failures and unintended topology changes.
- Document exceptions where process-specific modeling requires a different order; do not turn feature-order heuristics into universal rules.

A regenerated timeline is necessary but insufficient. The model passes only when the changed result still expresses the intended relationships.