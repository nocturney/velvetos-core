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

Both `nocturney/velvetos-core` and `nocturney/velvetos-velvet-factory` are **public** — Cloud Agents can **read** and `attach-core`. This agent cannot `createRepository`; push needs owner PAT or `cursor[bot]` write on the target repo.

`velvet-factory` is already published on GitHub. Re-run `publish-instance.sh` only when the scaffold changed; merge locally if the remote has diverged.

Later: copy a scaffold from `velvet-factory/` or build from `packages/velvetos/presets/`.
