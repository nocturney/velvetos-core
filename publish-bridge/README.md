# VelvetOS public publish staging branch

This branch is transport-only. It is **not** the Media Vault, not an approval queue, and not evidence of publication.

Canonical policy lives on `main` in `packages/vfigos/PUBLISH-BRIDGE.md` and `packages/vfigos/PUBLISH-BRIDGE.json`.

Rules:
- stage only exact derivatives already approved for public release;
- never stage Drive originals, private CAD, ambiguous-rights/customer media, secrets, or unapproved price claims;
- normal staged assets belong under `publish-bridge/assets/<YYYY-MM-DD>/<non-PII-correlation>/<content-hash>.<ext>`;
- public URLs are transport inputs to Instagram only after external fetch verification;
- `staged` and `fetch_verified` are not `published_verified`;
- daily cleanup removes expired dated assets from branch HEAD, but Git history is not secure erasure.

The historical `G004/` directory predates the normalized asset layout and remains only while that scheduled publication uses it. New assets must use `assets/`.
