# VelvetOS Core

Shared **backend** OS kernel for Velvet business offices: laws, seats, packs, modules, sensors, presets.

> **Velvet Factory — התחלה פשוטה (עברית):** [`docs/START-HERE-HE.md`](docs/START-HERE-HE.md) — ריפo אחד, לחיצה כפולה על `START-VF.bat`, בלי ריפo שני.

- Identity: `packages/velvetos/CORE.json`
- Modules: `packages/velvetos/modules/`
- Frontend scaffolds: `instances/` (publish with `scripts/publish-instance.sh`)
- Plan: `packages/velvetos/REPOS.md` · Docs: `docs/VELVETOS.md`

**Metaphor:** Core = backend · `VelvetOS — <Business>` = frontend.

HQ **sends Gmail and Instagram via tools** (`constitution/SEND.md`). Grok Bot is optional backup.

Reference studio bind (compat until VF frontend repo is daily workspace): Sderot · WhatsApp `050-2517000` · IG [@velvets_cloud](https://instagram.com/velvets_cloud).

```bash
python3 scripts/velvetos.py core
python3 scripts/velvetos.py modules
python3 scripts/velvetos.py instances
python3 scripts/check-all.py
```

See `CHANGELOG.md`. Harness: [`docs/HARNESS.md`](docs/HARNESS.md). Constitution: [`constitution/`](constitution/).  
Origin slugs: never invent — [`docs/ORIGIN-SLUGS.md`](docs/ORIGIN-SLUGS.md). Do not invent Origin slugs; keep `unknown`.  
Owner-only access steps: [`docs/OWNER-ACTIONS-he.md`](docs/OWNER-ACTIONS-he.md).
