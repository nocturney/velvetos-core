# Cursor packs

Office OS lives here as `packages/<name>/`.

v0.1.0 catalogues every known Velvet Factory Cursor pack. Actual Origin trees were **not** copied in that dump: this HQ environment had GitHub auth only. Origin CLI reported `Not logged in`, `CURSOR_API_KEY` was unset, and `https://origin.cursor.com/{owner}/{repo}.git` rejected the GitHub token.

After `origin auth login` (or `CURSOR_API_KEY`), run:

```bash
chmod +x scripts/vendor-origin-packs.sh
./scripts/vendor-origin-packs.sh
```

Each folder keeps `ORIGIN.md` (slug, agent URL, one-line role). HQ overlay (not Origin) lives in `SKILL.md` + `hq/` and survives `scripts/vendor-origin-packs.sh`. Playbooks from the 30.8.2026 Gemini share and Perplexity PDFs sit in the same folder. Do not invent prices. This repo does not send Instagram — live send stays on Grok Bot.

Constitution and team of 5: [`../constitution/`](../constitution/). Hebrew reports: [`../docs/SHARE-EMBED-he.md`](../docs/SHARE-EMBED-he.md), [`../docs/SHARES-2026-08-30.md`](../docs/SHARES-2026-08-30.md).

`vfcanva` is HQ-native (tree lives here). Instagram visuals go through Canva MCP; see `docs/CANVA.md`.

HQ-native research packs (not Origin trees): `vfmcp` ([`docs/MCP-FIT.md`](../docs/MCP-FIT.md)), `vfe2b` (e2b-dev/awesome-ai-agents desk), `vfagents` ([`docs/500-AGENTS.md`](../docs/500-AGENTS.md)), and `vfharness` ([`docs/HARNESS.md`](../docs/HARNESS.md) — six-layer outer harness on existing packs).

Share embed map: [`chatgpt-embed-map.json`](chatgpt-embed-map.json). Constitution: [`../constitution/`](../constitution/CONSTITUTION.md). Orchestra: [`../constitution/ORCHESTRA.md`](../constitution/ORCHESTRA.md).

HQ overlays (orchestra, brief, gates) live next to `ORIGIN.md`. `scripts/vendor-origin-packs.sh` keeps them when Origin trees land.

New packs are catalogued the **same day** they finish (`docs/BACKUP.md`). If Origin will not clone, the map still updates. Do not add a pack that duplicates an existing tool.

Agency specialists that sit on a pack are listed in [`docs/AGENCY-TOOLS.md`](../docs/AGENCY-TOOLS.md). They do not replace these folders.
