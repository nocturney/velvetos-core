# Instances (frontend scaffolds)

Each folder is a **publishable frontend** office for one business.

| Folder | Target GitHub |
|---|---|
| `velvet-factory/` | `nocturney/velvetos-velvet-factory` |
| `_template/` | Copy when creating a new business instance |

Every instance **must** ship `.cursor/environment.json` (Cloud boot → `attach-core`). See `packages/velvetos/INSTANCE-ENV.md`.

```bash
# from VelvetOS Core root
PUSH=1 ./scripts/publish-instance.sh velvet-factory nocturney/velvetos-velvet-factory
```

This Cloud Agent token cannot `createRepository` — the owner creates the empty private repo first.

Later: copy a scaffold from `velvet-factory/` or build from `packages/velvetos/presets/`.
