# vfmedia — media vault local guide

Scope: media intake, catalog, fingerprinting, source movement and media evidence.

- One canonical procedure: `docs/MEDIA-VAULT.md`.
- One canonical catalog: `packages/vfmedia/catalog.json`.
- Upload/folder placement is not creative approval or publication proof.
- Preserve exact bytes/fingerprints/provenance; duplicate detection must not invent a new asset.
- Do not create a parallel media catalog, parallel vault procedure or alternate authority.
- Sharing/permission changes are separate protected external effects.
- Creative/publication instructions are loaded only when the routed task actually enters that domain.

Verification: `python3 scripts/check-vfmedia.py`.
Permission/share boundary: `policy_id: external.permission.mutate`; media intake/catalog evidence cannot authorize permission mutation.
