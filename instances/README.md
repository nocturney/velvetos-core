# Instances (frontend scaffolds)

Each folder is a **publishable frontend** office for one business.

| Folder | Target GitHub (create empty, then publish) |
|---|---|
| `velvet-factory/` | `nocturney/velvetos-velvet-factory` |

```bash
# from VelvetOS Core root
PUSH=1 ./scripts/publish-instance.sh velvet-factory nocturney/velvetos-velvet-factory
```

This Cloud Agent token cannot `createRepository` — the owner creates the empty private repo first.

Later: copy a scaffold from `velvet-factory/` or build from `packages/velvetos/presets/`.
