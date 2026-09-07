---
name: vf-velvetos
description: Orient on VelvetOS Core (backend) vs business frontend instances. Use for VelvetOS, Core, publish-instance, attach-core, modules, or multi-repo split.
---

# VelvetOS

## Pack

- Pack: `velvetos`
- Docs: `docs/VELVETOS.md` · `packages/velvetos/REPOS.md`

## Do this

1. This repo is **VelvetOS Core** (backend / **Kernel**) — `CORE.json` · three layers: `LAYERS.md` · ADR: `ADR-THREE-LAYERS.md`.
2. Event contracts (disk only): `schema/events.catalog.json` — no broker / nervous-system runtime rename.
3. List modules: `python3 scripts/velvetos.py modules`.
4. VF frontend scaffold: `instances/velvet-factory/` — publish with `scripts/publish-instance.sh` after the owner creates the empty GitHub repo.
5. Future businesses = new frontend repos from presets; attach core via `attach-core.sh`.
6. After edits: `python3 scripts/check-velvetos.py`.

## Do not

- Treat Core as the only long-term VF frontend workspace (scaffold exists to cut over)
- Add a second live business frontend inside Core
- Turn Core into an event-bus / IoT nervous-system runtime
- Invent ₪ / Insights / handles
- Auto-DM / boost
- Promise zero-touch close on sale ₪ or customer WhatsApp
