---
name: vf-web-ui-quality
description: Run the pinned Impeccable methodology only on explicitly named Web/UI surfaces. Never use it for Velvet Factory creative posts, product imagery, or as product truth.
---

# VelvetOS Web/UI quality

Use for frontend, dashboard, Control Center, HTML/CSS or web-component quality work.

1. Read `packages/vfharness/devtools/impeccable-scope.md`.
2. Run `python scripts/check-engineering-quality.py --strict`.
3. Read the upstream pinned skill at
   `.local-devtools/phase4/impeccable/.cursor/skills/impeccable/SKILL.md` as secondary guidance.
4. Use only audit/detect/critique/polish behavior that applies to the named Web/UI target.
5. Existing VelvetOS specs, product truth, brand rules, approvals and sensors override upstream text.
6. Verify the exact changed surface with the repository's own test/sensor before claiming success.

## Hard stops

- Do not run Impeccable `init`; do not create or replace `PRODUCT.md`.
- Do not install or approve global/provider hooks from this wrapper.
- Do not use it in `packages/vfom` or any Instagram/product-photo/creative-post pipeline.
- Do not enable paid/model-provider paths.
