# Cursor packs

Office OS lives here as `packages/<name>/`.

v0.1.0 catalogues every known Velvet Factory Cursor pack. Actual Origin trees were **not** copied in that dump: this HQ environment had GitHub auth only. Origin CLI reported `Not logged in`, `CURSOR_API_KEY` was unset, and `https://origin.cursor.com/{owner}/{repo}.git` rejected the GitHub token.

After `origin auth login` (or `CURSOR_API_KEY`), run:

```bash
chmod +x scripts/vendor-origin-packs.sh
./scripts/vendor-origin-packs.sh
```

Each folder keeps `ORIGIN.md` (slug, agent URL, one-line role). Playbooks from the 30.8.2026 Gemini share and Perplexity PDFs sit in the same folder. Do not invent prices. This repo does not send Instagram — live send stays on Grok Bot.

Constitution and team of 5: [`../constitution/`](../constitution/). Hebrew report: [`../docs/SHARES-2026-08-30.md`](../docs/SHARES-2026-08-30.md).

New packs are catalogued the **same day** they finish (`docs/BACKUP.md`). If Origin will not clone, the map still updates.
