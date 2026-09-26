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

`nocturney/velvetos-core` is **public**; `nocturney/velvetos-velvet-factory` is **private** (verified 2026-09-26 via `gh repo view --json visibility`). Cloud Agents read the frontend only with owner-granted access; core stays readable for `attach-core`. This agent cannot `createRepository`; push needs owner PAT or `cursor[bot]` write on the target repo.

Drift check (check-only, never pushes): `./scripts/sync-instance-scaffold.sh [--check] [--skip-if-inaccessible]` prints `OK` / `DRIFT differ=… scaffold_only=… remote_only=…` / `SKIP`. `check-all.yml` runs it report-only with `--skip-if-inaccessible`; CI's `GITHUB_TOKEN` cannot read the private frontend, so there it normally SKIPs. Run it locally with access for the real diff. The frontend's own `.github/`, `docs/` and `.cursor/mcp.json` are an explicit instance-only allowlist: they're reported but never counted as drift.

Core lock: `velvet-factory/core.lock.yml` is intentionally **not** a SHA pin (`ref: main`, `refPolicy: track-main`). `attach-core.sh`/`verify-core.sh` default to `main`, and `verify-core.sh` fails on a stale vendor copy. `check-velvetos.py` fails if the lock and the scripts' default ref disagree.

Template = union of both sides (2026-09-26 two-way merge). Every fail-closed gate from the published frontend (the brand-asset, creative-transformation and project-request-gate blocks in `vf-desk.json` and the profile, `requiredFor`/`hardRejects`, the `require*` publish flags, OFFERING SHAPE, `check-vf-offering.py` in `verify-core.sh`, verify-on-attach) now lives here alongside core's newer work (VF_PUBLICATION_ROUTE_V1, ORCHESTRA/SEND, offline attach, publication-prep check). `check-velvetos.py` fails if the template loses any of them.

`velvet-factory` is already published on GitHub. Re-run `publish-instance.sh` only when the scaffold changed; merge locally if the remote has diverged.

Later: copy a scaffold from `velvet-factory/` or build from `packages/velvetos/presets/`.
