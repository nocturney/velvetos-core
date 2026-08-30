# Cursor packs

Office OS lives here as `packages/<name>/`.

v0.1.0 catalogues every known Velvet Factory Cursor pack. Actual Origin trees were **not** copied in that dump: this HQ environment had GitHub auth only. Origin CLI reported `Not logged in`, `CURSOR_API_KEY` was unset, and `https://origin.cursor.com/{owner}/{repo}.git` rejected the GitHub token.

After `origin auth login` (or `CURSOR_API_KEY`), run:

```bash
chmod +x scripts/vendor-origin-packs.sh
./scripts/vendor-origin-packs.sh
```

Each folder keeps `ORIGIN.md` (slug, agent URL, one-line role). Do not invent prices. This repo does not send Instagram — live send stays on Grok Bot.

HQ-native research packs (not Origin trees): `vfmcp` ([`docs/MCP-FIT.md`](../docs/MCP-FIT.md)), `vfe2b` (e2b-dev/awesome-ai-agents desk), and `vfagents` ([`docs/500-AGENTS.md`](../docs/500-AGENTS.md)).

New packs are catalogued the **same day** they finish (`docs/BACKUP.md`). If Origin will not clone, the map still updates.

Agency specialists that sit on a pack are listed in [`docs/AGENCY-TOOLS.md`](../docs/AGENCY-TOOLS.md). They do not replace these folders.
