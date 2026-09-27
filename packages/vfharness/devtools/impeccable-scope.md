# Impeccable scope — Web/UI only

Canonical source: https://github.com/pbakaus/impeccable
Pinned source: `9d715cc4f5564a990ca8345abfdd5df6dc9b41c8`

Role: local development aid for web/frontend quality. It is not a product-truth source,
brand authority, creative director or release gate.

## Allowed

- Audit/detect existing HTML/CSS/frontend UI.
- Critique and polish a named Web/UI surface.
- Use deterministic detector rules locally without an API key.
- Inspect local development pages when the existing project already provides a safe local server.

## Disabled

- `/impeccable init` may not create `PRODUCT.md`; VelvetOS already has canonical product truth.
- No global/provider-native hook installation in this phase.
- No automatic hook that scans every repository edit.
- No LLM/provider API calls for a quality gate.
- No write outside the explicitly named Web/UI target.
- No injection into `packages/vfom`, social-post generation, product-photo editing,
  Instagram creative or other Velvet Factory creative-post flows.

## Invocation contract

Use `.cursor/skills/vf-web-ui-quality/SKILL.md`. It loads the pinned local upstream skill only
after `python scripts/check-engineering-quality.py --strict` passes.

The wrapper narrows upstream behavior: existing repository authority wins, product truth is
read-only, and completion still requires the repository's own sensors/receipts.
