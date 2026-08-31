# VelvetOS — Velvet Factory

Private backup, versions, and changelog for the VelvetOS Cursor office (**instance:** Velvet Factory).

HQ **sends Gmail and Instagram via tools** (`constitution/SEND.md`). Grok Bot is optional backup. Printers stay on the floor.
Cursor packs in `packages/` are the office OS. Core modules: [`packages/velvetos/`](packages/velvetos/) · multi-repo plan: [`REPOS.md`](packages/velvetos/REPOS.md) · docs: [`docs/VELVETOS.md`](docs/VELVETOS.md).

See `CHANGELOG.md`. Standing order (same-day map, no weekly wait): `docs/BACKUP.md`.  
Orchestra (06:15 ChatGPT + Gemini + Perplexity): [`constitution/ORCHESTRA.md`](constitution/ORCHESTRA.md). Grok decides; Cursor opens the three desks.  
Harness (`AGENTS.md` + `packages/vfharness/`): [`docs/HARNESS.md`](docs/HARNESS.md). Agent = Model + Harness. After catalog edits: `python3 scripts/check-all.py`.

Constitution (team of 5, studio facts, skip rules): [`constitution/`](constitution/).  
Share embed 30.8.2026 (Gemini link + Perplexity PDFs): [`docs/SHARES-2026-08-30.md`](docs/SHARES-2026-08-30.md).

## What this repo is

GitHub copy of **VelvetOS — Velvet Factory**. Core modules for other verticals are preloaded under `packages/velvetos/modules/`. Future businesses get their own instance repos that pull from core. Cursor agents built the packs on Origin (`christian-velvet/tmp-…`). This repository is the durable backup, version tag, and changelog — not a second sender.

- **Live send:** HQ tools — Gmail `send_message` / Instagram via `vfigos/SEND.md`. Grok Bot is optional backup. Printers stay on the floor.
- **Office OS:** Cursor packs under `packages/<name>/` plus `constitution/` plus VelvetOS core modules under `packages/velvetos/`.
- **Workhorses:** Cursor opens ChatGPT, Gemini, and Perplexity at 06:15. Does not invent a blocked body. See [`constitution/ORCHESTRA.md`](constitution/ORCHESTRA.md).
- **Instagram visuals:** Canva (`packages/vfcanva/`, `docs/CANVA.md`). Create / resize / review, then send via `vfigos/SEND.md`.
- **The Agency:** 273 specialist Cursor rules in `.cursor/rules/` (from [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents)). Mention `@slug` to activate. Roster: [`docs/AGENCY-AGENTS.md`](docs/AGENCY-AGENTS.md).
- **Desk:** 28 of those specialists are wired to VF packs and live tools (Gmail read-and-send, Calendar, Drive search-and-create, Canva, WebSearch, Superdesign). Treg is not relevant. Map: [`docs/AGENCY-TOOLS.md`](docs/AGENCY-TOOLS.md).
- **HQ sends Instagram via tools (`constitution/SEND.md`). No auto-DM. No boost.** No pack dump here posts, boosts, or DMs.
- **Studio (this instance):** pickup-only Sderot · WhatsApp 050-2517000 · IG [@velvets_cloud](https://instagram.com/velvets_cloud) · Hebrew product.
- **Five seats (office):** ראש צוות, סטודיו, צמיחה, תפעול, ייצור — mapped onto existing packs, not new ones.

No secrets belong in git. No invented prices or invented Insights.

## The Agency (Cursor specialists)

Installed from [The Agency](https://github.com/msitarzewski/agency-agents) as project-scoped Cursor `.mdc` rules. Warehouse rules are **not** always-on: type `@instagram-curator`, `@studio-operations`, `@brand-guardian`.

The **desk** is always-on (`.cursor/rules/velvet-factory-desk.mdc`). It routes a job to a pack, one `@slug`, and a live tool. Do not pull the other 245 warehouse specialists onto a Sderot print job unless asked.

```bash
# first install or later refresh (keeps the VF desk rule)
./scripts/install-agency-agents.sh
python3 scripts/check-vf-desk.py
python3 scripts/vfmem.py who "בריף בוקר"
```

| | |
|---|---|
| Warehouse catalog | [`.cursor/agency-agents.json`](.cursor/agency-agents.json) |
| Full roster | [`docs/AGENCY-AGENTS.md`](docs/AGENCY-AGENTS.md) |
| Desk + tools | [`docs/AGENCY-TOOLS.md`](docs/AGENCY-TOOLS.md), [`.cursor/vf-desk.json`](.cursor/vf-desk.json) |
| Daily skills | `.cursor/skills/vf-morning-brief`, `vf-inquiry-chain`, `vf-content-sprint`, `vf-marketing-skills`, `vf-makers`, `vf-harness`, `vf-hq-memory`, `vf-graft-map` |
| Guide file | [`AGENTS.md`](AGENTS.md) — wins over the conversation |

These specialists do **not** replace VF packs. They sit next to the office OS. Still no Instagram or Gmail send from this HQ.

## Office overlay (2026-08-30)

The ChatGPT share [סוכני בנייה](https://chatgpt.com/s/t_6a94208d21048191a67144976f50de19) was read and **embedded into existing packs** — no new pack per agent.

| Layer | Where |
|---|---|
| Constitution + tags | [`constitution/`](constitution/CONSTITUTION.md) |
| Daily brief packet | [`packages/vfbriefux/hq/PACKET.md`](packages/vfbriefux/hq/PACKET.md) · slots in `vfops` |
| Per-pack playbooks | `packages/<name>/SKILL.md` + `packages/<name>/hq/` |
| Agent → pack map | [`packages/chatgpt-embed-map.json`](packages/chatgpt-embed-map.json) |
| Hebrew report | [`docs/SHARE-EMBED-he.md`](docs/SHARE-EMBED-he.md) |

Five seats: ראש צוות · סטודיו · צמיחה · תפעול · ייצור. Pickup Sderot only. WhatsApp `050-2517000`. Vendor keeps `hq/` when Origin trees land.

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
| `vfcanva` | Canva desk — Instagram visuals for `@velvets_cloud` (create / resize / review; this HQ does not send). | [bc-2020e135-820c-40b6-a922-e2822b5e81bf](https://cursor.com/agents/bc-2020e135-820c-40b6-a922-e2822b5e81bf) | HQ-native (this repo) |
| `vfmcp` | MCP fit — which awesome-mcp-servers entries map onto VF packs. Write-up: [`docs/MCP-FIT.md`](docs/MCP-FIT.md). | [bc-1764e30f-b592-4805-9586-037da3351d65](https://cursor.com/agents/bc-1764e30f-b592-4805-9586-037da3351d65) | HQ-native (not Origin) |
| `vfe2b` | Awesome-AI-agents desk — patterns from [e2b-dev/awesome-ai-agents](https://github.com/e2b-dev/awesome-ai-agents) on existing packs (no second runtime; this HQ does not send). | [bc-21cee8d9-a82a-468d-b0a5-1d8fa87ef057](https://cursor.com/agents/bc-21cee8d9-a82a-468d-b0a5-1d8fa87ef057) | HQ-native |
| `vfdsh` | Awesome-DSH-plugin desk — patterns from [awesome-dsh-plugin](https://github.com/awesome-dsh-plugin/awesome-dsh-plugin) on existing packs (no DeepSeek Harness; this HQ does not send). | [bc-b4c0a22f-7c08-497e-beac-c4518acbea1d](https://cursor.com/agents/bc-b4c0a22f-7c08-497e-beac-c4518acbea1d) | HQ-native; [`docs/DSH-FIT.md`](docs/DSH-FIT.md) |
| `vfmakers` | Maker-skills desk — patterns from [coreyhaines31/makerskills](https://github.com/coreyhaines31/makerskills) (decide, unstuck, cash pulse, IG rotation, studio brain). No plugin; this HQ does not send. | [bc-888d3ff6-c3ad-43f7-bda3-814c82546324](https://cursor.com/agents/bc-888d3ff6-c3ad-43f7-bda3-814c82546324) | HQ-native; [`docs/MAKERSKILLS-EMBED-he.md`](docs/MAKERSKILLS-EMBED-he.md) |
| `vfagents` | 500 AI Agents fit — office playbooks from the public list; no CrewAI runtime, no send. | [bc-9765dc13](https://cursor.com/agents/bc-9765dc13-6ca2-4c51-a550-6dfb1d3b0027) | HQ-native; [`docs/500-AGENTS.md`](docs/500-AGENTS.md) |
| `vfmskill` | Marketing Skills desk — curated 15/50 skills from [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) on existing packs (copy, social, offer). | [bc-cbd42dd7-d35f-4c48-88f3-1d993d3b1792](https://cursor.com/agents/bc-cbd42dd7-d35f-4c48-88f3-1d993d3b1792) | HQ-native; [`docs/MARKETING-SKILLS.md`](docs/MARKETING-SKILLS.md) |
| `vfom` | OpenMontage desk — clip-factory / hybrid / reference-plan crews on existing packs (no Remotion vendor; this HQ does not send). | [bc-4be8813f](https://cursor.com/agents/bc-4be8813f-000e-43a0-b297-7537bda05d4e) | HQ-native; [`docs/OPENMONTAGE.md`](docs/OPENMONTAGE.md) |
| `vfharness` | Outer harness — six layers (guides, sensors, loop, memory, permissions, observability) on existing packs. No second runtime. | [bc-c6e01d3b-4cbe-4a8c-9b9c-4e87b5aa9ccb](https://cursor.com/agents/bc-c6e01d3b-4cbe-4a8c-9b9c-4e87b5aa9ccb) | HQ-native; [`docs/HARNESS.md`](docs/HARNESS.md) |
| `vfgraft` | Graft office graph — committed markdown map so agents do not re-explore HQ from zero. No npm CLI. | [bc-e154ffc2-061a-4635-8d32-a6bcb145bc64](https://cursor.com/agents/bc-e154ffc2-061a-4635-8d32-a6bcb145bc64) | HQ-native; [`docs/GRAFT.md`](docs/GRAFT.md) |
| `vfmem` | HQ memory graph — structural queries over desk/manifest/Agency maps (pattern from [codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp); no binary). | [bc-8bd6ba75-55a3-4b68-a30e-175d94b67823](https://cursor.com/agents/bc-8bd6ba75-55a3-4b68-a30e-175d94b67823) | HQ-native; [`docs/VFMEM.md`](docs/VFMEM.md) |
| `vffcc` | Free Claude Code fit — [FCC](https://github.com/Alishahryar1/free-claude-code) as a local BYOK map. Does not cut Cursor Cloud usage; no `fcc-server` here. | [bc-5abae8de-a5da-455e-b71c-3db25e3d029c](https://cursor.com/agents/bc-5abae8de-a5da-455e-b71c-3db25e3d029c) | HQ-native; [`docs/FCC-FIT.md`](docs/FCC-FIT.md) |

Constitution (not a pack dump): [`constitution/`](constitution/). Playbook: [`constitution/ORCHESTRA.md`](constitution/ORCHESTRA.md). Hebrew report: [`docs/ORCHESTRA-2026-08-30.md`](docs/ORCHESTRA-2026-08-30.md).

Machine-readable catalog: [`packages/manifest.json`](packages/manifest.json). Per-pack provenance: `packages/<name>/ORIGIN.md`. Playbooks from the Gemini share sit next to `ORIGIN.md` in the same folder — upgrade in place, no duplicate pack.

## v0.1.0 dump status

This environment could not copy Origin trees:

1. `origin` CLI: not logged in (needs `origin auth login` or `CURSOR_API_KEY`).
2. `git clone https://origin.cursor.com/{owner}/{repo}.git` rejected the GitHub token.
3. Pack cloud-agent ids were not readable from this HQ environment (different Origin repos / environments).
4. Slugs for `vfops`, `vfcovers`, `vfinsights`, `vfbooks`, `vfresearch`, `vfbiz`, `vfcopy`, `vlicense`, `vfseason`, `vfsku`, and `vfbriefux` stay `unknown`. Do not invent them. HQ overlay (`SKILL.md` + `hq/`) is the office. Playbook: [`docs/ORIGIN-SLUGS.md`](docs/ORIGIN-SLUGS.md). Recheck 2026-08-31: this token’s `origin repo list` is HQ-only; known `tmp-*` slugs return `token is not scoped`; pack bcIds are not readable here.

Folders exist so a later vendor run can drop the real trees in place. `scripts/vendor-origin-packs.sh` SKIPs empty slugs. Report: `python3 scripts/discover-origin-slugs.py`.

## Vendor actual source later

Needs an Origin token **scoped for `christian-velvet/tmp-*`**, not only HQ. Login alone is not enough. Fill a slug only from the pack agent page or a scoped list — never invent. See [`docs/ORIGIN-SLUGS.md`](docs/ORIGIN-SLUGS.md).

```bash
python3 scripts/discover-origin-slugs.py
# only after a scoped token or a copied slug:
./scripts/vendor-origin-packs.sh
```

Clone URL shape: `https://origin.cursor.com/{owner}/{repo}.git`.

Codebase URLs: `https://cursor.com/codebase/<origin-slug>`.
Cloud agent URLs: `https://cursor.com/agents/<bcId>`.

## Standing order (2026-08-30)

GitHub HQ is the constant backup. On every new pack follow-up, the same day: update `packages/<name>/ORIGIN.md` + `packages/manifest.json`, vendor if Origin clones, append `CHANGELOG.md` Unreleased (date + one Hebrew+English line), push to `main`. If Origin will not clone, still update the map. Grok Bot: see [`docs/BACKUP.md`](docs/BACKUP.md) — reply to this HQ agent with bcId, pack name, and Origin slug if known; quiet if nothing new.
