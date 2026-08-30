# Cursor packs

Office OS lives here as `packages/<name>/`.

v0.1.0 catalogues every known Velvet Factory Cursor pack. Actual Origin trees were **not** copied in that dump: this HQ environment had GitHub auth only. Origin CLI reported `Not logged in`, `CURSOR_API_KEY` was unset, and `https://origin.cursor.com/{owner}/{repo}.git` rejected the GitHub token.

After `origin auth login` (or `CURSOR_API_KEY`), run:

```bash
chmod +x scripts/vendor-origin-packs.sh
./scripts/vendor-origin-packs.sh
```

Each folder keeps `ORIGIN.md` (slug, agent URL, one-line role). HQ overlay (not Origin) lives in `SKILL.md` + `hq/` and survives `scripts/vendor-origin-packs.sh`. Do not invent prices. This repo does not send Instagram — live send stays on Grok Bot.

Share embed map: [`chatgpt-embed-map.json`](chatgpt-embed-map.json). Constitution: [`../constitution/`](../constitution/CONSTITUTION.md).

New packs are catalogued the **same day** they finish (`docs/BACKUP.md`). If Origin will not clone, the map still updates. Do not add a pack that duplicates an existing tool.
