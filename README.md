# VELVET FACTORY HEADQUARTERS & OS

Private backup, versions, and changelog for Velvet Factory Cursor packs.

Grok Bot (5 seats) still runs live Instagram, Gmail, and printers.
Cursor packs in `packages/` are the office OS.

See `CHANGELOG.md`. Standing order (same-day map, no weekly wait): `docs/BACKUP.md`.

Constitution (team of 5, studio facts, skip rules): [`constitution/`](constitution/).  
Share embed 30.8.2026 (Gemini link + Perplexity PDFs): [`docs/SHARES-2026-08-30.md`](docs/SHARES-2026-08-30.md).

## What this repo is

GitHub copy of the studio office OS. Cursor agents built the packs on Origin (`christian-velvet/tmp-…`). This repository is the durable backup, version tag, and changelog — not the live sender.

- **Live:** Grok Bot (5 seats) — Instagram, Gmail, printers.
- **Office OS:** Cursor packs under `packages/<name>/`.
- **This HQ does not send Instagram.** No pack dump here posts, boosts, or DMs.
- **Studio:** pickup-only Sderot · WhatsApp 050-2517000 · IG [@velvets_cloud](https://instagram.com/velvets_cloud) · Hebrew product.
- **Five seats (office):** ראש צוות, סטודיו, צמיחה, תפעול, ייצור — mapped onto existing packs, not new ones. Grok «5 seats» is the live sender.

No secrets belong in git. No invented prices or invented Insights.

## Packs (v0.1.0)

| Pack | What it does | Agent | Origin |
|---|---|---|---|
| `vfigos` | VF Instagram OS — Instagram office pack (review and schedule; this HQ does not send). | [bc-c4a53ee3](https://cursor.com/agents/bc-c4a53ee3) | [christian-velvet/tmp-20e9908caebda9d0](https://cursor.com/codebase/christian-velvet/tmp-20e9908caebda9d0) |
| `vfcost` | Studio cost pack — unit economics and spend, without invented prices. | [bc-a4dc99c9](https://cursor.com/agents/bc-a4dc99c9) | [christian-velvet/tmp-8a55585f5a73bd06](https://cursor.com/codebase/christian-velvet/tmp-8a55585f5a73bd06) |
| `vfconvert` | Conversion pack — inquiry-to-order path. | [bc-9644a175](https://cursor.com/agents/bc-9644a175) | [christian-velvet/tmp-4460086f23171633](https://cursor.com/codebase/christian-velvet/tmp-4460086f23171633) |
| `vfgrowth` | Growth pack — content sprints and acquisition work. | [bc-e68393a0](https://cursor.com/agents/bc-e68393a0) | [christian-velvet/tmp-0093db8b6deea44f](https://cursor.com/codebase/christian-velvet/tmp-0093db8b6deea44f) |
| `vfprod` | Production pack — print-floor and job tracking. | [bc-cd4a5cde](https://cursor.com/agents/bc-cd4a5cde) | [christian-velvet/tmp-c9ca74be9225ac7d](https://cursor.com/codebase/christian-velvet/tmp-c9ca74be9225ac7d) |
| `vfsales` | Sales pack — quotes and follow-up. | [bc-28017566](https://cursor.com/agents/bc-28017566) | [christian-velvet/tmp-b467d4882113eabd](https://cursor.com/codebase/christian-velvet/tmp-b467d4882113eabd) |
| `vfops` | Operations pack — run-the-studio procedures. | [bc-93fbfca6](https://cursor.com/agents/bc-93fbfca6) | slug not found in this dump |
| `vfcovers` | Covers pack — brief and post cover art. | [bc-390e0de1](https://cursor.com/agents/bc-390e0de1) | slug not found in this dump |
| `vfinsights` | Insights pack — performance reads; does not invent metrics. | [bc-02df9e72](https://cursor.com/agents/bc-02df9e72) | slug not found in this dump |
| `vfbooks` | Books pack — receivables and studio ledger work. | [bc-280dd241](https://cursor.com/agents/bc-280dd241) | slug not found in this dump |
| `vfresearch` | Research pack — source gathering and notes. | [bc-01278e9b](https://cursor.com/agents/bc-01278e9b) | slug not found in this dump |
| `vfbiz` | Business pack — studio strategy and decisions. | [bc-3921041e](https://cursor.com/agents/bc-3921041e) | slug not found in this dump |
| `vfcopy` | Copy desk — homework, draft, and lint. | [bc-b6bc8b8c-136d-4d95-812e-177991534e42](https://cursor.com/agents/bc-b6bc8b8c-136d-4d95-812e-177991534e42) | slug not found in this dump |
| `vlicense` | License gate — studio license / access check. | [bc-0a6460b1](https://cursor.com/agents/bc-0a6460b1) | slug not found in this dump |
| `vfseason` | Seasonal calendar — studio calendar and season marks. | [bc-2a4a3260](https://cursor.com/agents/bc-2a4a3260) | slug not found in this dump |
| `vfsku` | SKU cards and repeats — product cards and reprint runs. | [bc-68f7f06c](https://cursor.com/agents/bc-68f7f06c) | slug not found in this dump |
| `vfbriefux` | Brief format research — morning-brief layout and UX notes. | [bc-9e0be231](https://cursor.com/agents/bc-9e0be231) | slug not found in this dump |

Machine-readable catalog: [`packages/manifest.json`](packages/manifest.json). Per-pack provenance: `packages/<name>/ORIGIN.md`. Playbooks from the Gemini share sit next to `ORIGIN.md` in the same folder — upgrade in place, no duplicate pack.

## v0.1.0 dump status

This environment could not copy Origin trees:

1. `origin` CLI: not logged in (needs `origin auth login` or `CURSOR_API_KEY`).
2. `git clone https://origin.cursor.com/{owner}/{repo}.git` rejected the GitHub token.
3. Pack cloud-agent ids were not readable from this HQ environment (different Origin repos / environments).
4. Slugs for `vfops`, `vfcovers`, `vfinsights`, `vfbooks`, `vfresearch`, `vfbiz`, `vfcopy`, `vlicense`, `vfseason`, `vfsku`, and `vfbriefux` were not in the known list and could not be discovered without Origin list access.

Folders exist so a later vendor run can drop the real trees in place.

## Vendor actual source later

```bash
origin auth login
# or: export CURSOR_API_KEY=…
./scripts/vendor-origin-packs.sh
```

Clone URL shape: `https://origin.cursor.com/{owner}/{repo}.git`.

Codebase URLs: `https://cursor.com/codebase/<origin-slug>`.
Cloud agent URLs: `https://cursor.com/agents/<bcId>`.

## Standing order (2026-08-30)

GitHub HQ is the constant backup. On every new pack follow-up, the same day: update `packages/<name>/ORIGIN.md` + `packages/manifest.json`, vendor if Origin clones, append `CHANGELOG.md` Unreleased (date + one Hebrew+English line), push to `main`. If Origin will not clone, still update the map. Grok Bot: see [`docs/BACKUP.md`](docs/BACKUP.md) — reply to this HQ agent with bcId, pack name, and Origin slug if known; quiet if nothing new.
