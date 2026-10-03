# Parametric design intent

Use this reference when creating or modifying sketches, parameters or feature history.

- Establish stable reference geometry first: origin planes/axes, construction geometry, datums and named parameters.
- Model the relationships that must survive change, not the coordinates that happen to work once.
- Keep exploratory sketches flexible while the concept is unresolved. Once downstream features depend on a settled sketch, remove unintended degrees of freedom.
- Prefer geometric constraints for relationships and dimensions for design values. Avoid duplicate constraints that encode the same fact twice.
- Use reference/driven dimensions for inspection and derived values rather than creating circular control logic.
- Name parameters by function when they will be reused or exposed. Keep user-facing parameters distinct from intermediate calculations.
- Favor a stable feature order: primary volume -> functional cuts/interfaces -> secondary features -> cosmetic details.
- Before changing an upstream feature, identify downstream consumers and protected interfaces.
- After a parameter change, inspect the full model rather than assuming a regenerated timeline means the design is still correct.

Current official Fusion guidance distinguishes exploratory unconstrained sketches from fully constrained sketches and warns that downstream references to unconstrained geometry can become unpredictable in complex parametric designs. Treat that as a design-intent principle, not a command to over-constrain early concepts.
