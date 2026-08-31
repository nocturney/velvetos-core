---
name: vf-velvetos
description: Orient on VelvetOS Core (backend) vs business frontend instances. Use for VelvetOS, Core, publish-instance, attach-core, modules, or multi-repo split.
---

# VelvetOS

## Pack

- Pack: `velvetos`
- Docs: `docs/VELVETOS.md` · `packages/velvetos/REPOS.md`

## Do this

1. This repo is **VelvetOS Core** (backend) — `CORE.json`.
2. List modules: `python3 scripts/velvetos.py modules`.
3. VF frontend scaffold: `instances/velvet-factory/` — publish with `scripts/publish-instance.sh` after the owner creates the empty GitHub repo.
4. Future businesses = new frontend repos from presets; attach core via `attach-core.sh`.
5. After edits: `python3 scripts/check-velvetos.py`.

## Do not

- Treat Core as the only long-term VF frontend workspace (scaffold exists to cut over)
- Add a second live business frontend inside Core
- Invent ₪ / Insights / handles
- Auto-DM / boost
