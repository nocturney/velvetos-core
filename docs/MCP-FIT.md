# MCP fit for Velvet Factory

Source: [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) (reviewed 2026-08-30).  
Discovery index (Claude Code marketplace — **patterns only**, do not `/plugin install` on Cloud Agent): [buildwithclaude.com](https://buildwithclaude.com/) · [davepoon/buildwithclaude](https://github.com/davepoon/buildwithclaude) `mcp-servers.json` (reviewed 2026-09-03). Embed: [`packages/vfresearch/sources/2026-09-03-buildwithclaude.md`](../packages/vfresearch/sources/2026-09-03-buildwithclaude.md).  
MCP Market mid-week (2026-09-05; Cloudflare on listing pages → GitHub bodies): Blender MCP · Archon · Jeffallan fullstack skills — [`packages/vfresearch/sources/2026-09-05-mcpmarket-three.md`](../packages/vfresearch/sources/2026-09-05-mcpmarket-three.md).  
Grok / ChatGPT / Gemini / Perplexity gap vs this HQ: [`packages/vfmcp/GAP.md`](../packages/vfmcp/GAP.md) (reviewed 2026-08-31).  
HQ **sends Gmail and Instagram via tools** (`constitution/SEND.md`). Boosts and auto-DM stay forbidden. Printers stay on the floor. Treg is not relevant.  
Core **registers** WhatsApp / Sheets / Studio Hub (`packages/vfmcp/CORE-MCP.md`). The factory instance binds via `mcpBind`. Do not invent prices. Do not commit secrets.

The awesome list is a directory of thousands of servers. Most of it is coding, crypto, or other people's SaaS. Below is only what maps onto Velvet Factory packs.

## Already wired (do not duplicate)

These are already in the Cursor / Cloud Agent tool surface. Adding a second MCP for the same job just burns tokens.

| Already here | What it covers | Packs it already feeds |
|---|---|---|
| **Gmail** | Search, read, draft, labels, **send / reply / forward** | `vfsales`, `vfconvert`, `vfops` |
| **Google Drive** | Files and folders; **`create_file`**; Sheets **export** when a workbook is named (`vfbooks/SHEETS.md`) | `vfprod`, `vfcovers`, `vfsku`, `vfresearch`, `vfbooks` |
| **Google Calendar** | Events | `vfseason`, `vfops`, `vfsales` |
| **Canva** | Edit designs, brand-check, bulk-create, resize, `generate-design`. **Ready** on this Cloud Agent (2026-08-31, `DAGoYmCu4c4`) | `vfcovers`, `vfigos`, `vfsku`, `vfcopy` |
| **3D AI Studio** | Text/image → 3D mesh, STL/3MF export. **HTTP** `https://mcp.3daistudio.com/mcp` — OAuth **Desktop** (`.cursor/mcp.json`) **+ Cloud** (Dashboard → Integrations & MCP). See `packages/vfprod/CONNECT-3DAI.md` | `vfprod`, `vfsku`, `vlicense` |
| **Studio MCP Hub** | HTTP `https://studiomcphub.com/mcp`. Free mockup/bg/resize; CMYK/`print_ready` for paper instances. VF skips CMYK. `packages/vfmcp/CONNECT-STUDIOHUB.md` | `vfprod`, `vfcovers`, `vfsku` |
| **WebSearch / WebFetch** | Live web + URL fetch (ChatGPT/Gemini/Perplexity/Grok browse equivalent) | `vfresearch`, `vfgrowth` |
| **GenerateImage** | User-asked stills. Instagram still Canva-first | `vfcovers`, `vfbriefux` |
| **Treg** | **Not relevant** — do not login or `call` | — |
| **Mobbin** | Real-app UI patterns | `vfbriefux` |
| **Superdesign** | Canvas / graphics | `vfcovers`, `vfbriefux` |
| **Grok Bot** | Optional backup only. HQ sends via tools | `vfigos/SEND.md` |

Skip extra Gmail, extra Canva, extra SEO crawlers, and extra “AI visibility” servers unless Treg is missing a specific account.

**Office graph (already in git, not a Cursor MCP add):** [`vfmem`](../packages/vfmem/) takes the *query shape* from [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) (`architecture` / `who` / `impact` / `adr`) and runs it on `vf-desk.json` + `manifest.json`. Do not install their C binary from this repo. Write-up: [`docs/VFMEM.md`](VFMEM.md).

## Installed in Core 2026-08-31 — instance binds what it needs

Constitution: VF WhatsApp **send** stays human `050-2517000`. HQ does not print. No invented ₪. No secrets in git.

Catalog: [`packages/vfmcp/CORE-MCP.md`](../packages/vfmcp/CORE-MCP.md) · [`core-mcp.json`](../packages/vfmcp/core-mcp.json). VF bind: `mcpBind` on `packages/velvetos/samples/velvet-factory.json`.

### 1. WhatsApp — inquiry-to-order · **in Core (draft/search)**

Desktop: [lharries/whatsapp-mcp](https://github.com/lharries/whatsapp-mcp) via [`CONNECT-WHATSAPP.md`](../packages/vfmcp/CONNECT-WHATSAPP.md) (`~/.cursor/mcp.json`). Not in project `mcp.json` (local Go + QR).

VF: `mcpBind.whatsapp.send=false`. Infobip / ManyChat stay off this instance.

Failover (Cloud / no QR):

```
python3 scripts/vf_office.py jobs add --channel WhatsApp --what "…" --phone 050…
python3 scripts/vf_office.py convert draft VF-YYYYMMDD-001
```

Playbook: [`packages/vfconvert/WHATSAPP.md`](../packages/vfconvert/WHATSAPP.md).

### 2. Google Sheets — studio ledger · **in Core (Desktop credentials)**

[freema/mcp-gsheets](https://github.com/freema/mcp-gsheets) on the owner Mac after a service account — [`CONNECT-SHEETS.md`](../packages/vfmcp/CONNECT-SHEETS.md). Not in project `mcp.json` (would override global env).

VF workbooks: `office/ledger/bindings.json`. Without Connect: local CSV + Drive `create_file`. Without an ID write **חסר גיליון**.

```
python3 scripts/vf_office.py jobs list
python3 scripts/vf_office.py jobs csv
```

Playbook: [`packages/vfbooks/SHEETS.md`](../packages/vfbooks/SHEETS.md).

### 3. Print file pipeline · **Studio MCP Hub in `.cursor/mcp.json`**

HTTP `https://studiomcphub.com/mcp` (`studiomcphub`). Cloud: Team MCP like 3DAI — [`CONNECT-STUDIOHUB.md`](../packages/vfmcp/CONNECT-STUDIOHUB.md).

VF skips `print_ready` / CMYK (3D studio). Uses free `remove_background` / `resize_image` if needed. Other print instances can enable CMYK in `mcpBind`. STL preflight stays:

```
python3 scripts/vf_office.py print preflight model.stl
```

Mesh repair: **3D AI Studio**. No wallet / x402 in git. No ₪ from GCX.

Playbook: [`packages/vfprod/PREFLIGHT.md`](../packages/vfprod/PREFLIGHT.md).

## Optional research (do not wire by default)

### prompts.chat — external prompt / skill lookup

| Server | Role | Notes |
|---|---|---|
| [f/prompts.chat MCP](https://prompts.chat/api/mcp) | `search_prompts`, `get_prompt`, `improve_prompt`, `search_skills` | **Research only.** Filter through `constitution/` before any customer or IG copy. Do not bulk-import `prompts.csv`. |

Remote URL: `https://prompts.chat/api/mcp`. Local fallback: `npx -y prompts.chat mcp` (not required on Cloud Agent).

**Packs:** `vfcopy`, `vfmskill`, `vfresearch`. Embedded office templates live in `packages/vfcopy/hq/templates/` — not in the MCP.

## Do this next (read-only growth)

### Instagram research only — never send from HQ

| Server | Role |
|---|---|
| [farukkolip/instapdown-mcp](https://github.com/farukkolip/instapdown-mcp) | Public toolkit: Reels/Story download, hashtags, engagement health, best-time tables. **No auth.** |

Use for `vfigos` review, `vfgrowth` sprints, `vfinsights` reads. Schedule and copy stay in the pack. **Grok Bot still posts.**

### Inbox triage on top of Gmail

| Server | Role |
|---|---|
| [elie222/inbox-zero](https://github.com/elie222/inbox-zero/tree/main/apps/mcp-server) | “What needs a reply / follow-up” on the existing mailbox |

Complements Gmail; does not replace it. Maps to `vfsales` and `vfconvert`.

### Meta Ads — read first

Grok Bot already boosts. If Christian wants Cursor to *read* spend and creative, not launch:

| Server | Role |
|---|---|
| [pipeboard-co/meta-ads-mcp](https://github.com/pipeboard-co/meta-ads-mcp) | Analyze performance, creatives, spend |
| [mikusnuz/meta-ads-mcp](https://github.com/mikusnuz/meta-ads-mcp) | Full Marketing API surface (too many write tools — keep writes off) |

**Read-only in Cursor.** Writes / boosts stay on Grok Bot until a later standing order says otherwise.

**Packs:** `vfigos`, `vfinsights`. Do not invent Insights numbers.

## Only if the studio already uses that product

Do not add these “because they exist on the list.” Add them when Christian confirms the account.

| If VF already has… | Then this MCP | Packs |
|---|---|---|
| WooCommerce / WordPress shop | [wppoland/woocommerce-mcp](https://github.com/wppoland/woocommerce-mcp) (read-only orders / products) | `vfsales`, `vfsku`, `vfbooks` |
| Airtable as the job board | [domdomegg/airtable-mcp-server](https://github.com/domdomegg/airtable-mcp-server) | `vfprod`, `vfops` |
| Xero or QuickBooks | [XeroAPI/xero-mcp-server](https://github.com/XeroAPI/xero-mcp-server) or Synder importer | `vfbooks` |
| A Stripe checkout | official Stripe via a thin wrapper (APIFold lists one) | `vfbooks`, `vfsales` |
| Google Business Profile not yet in Treg | [localseodata/mcp-server](https://github.com/localseodata/mcp-server) | `vfgrowth`, `vfinsights` |
| Reels cut from covers on the Mac | [video-creator/ffmpeg-mcp](https://github.com/video-creator/ffmpeg-mcp.git) or [06ketan/slideshot](https://github.com/06ketan/slideshot) | `vfigos`, `vfcovers` |
| QR on SKU / proof cards | [qr-maker-io/mcp-server](https://github.com/qr-maker-io/mcp-server) | `vfsku` |
| Floor “job done” pings | [teddyzxcv/ntfy-mcp](https://github.com/teddyzxcv/ntfy-mcp) | `vfprod` |
| Blender on the owner Mac (scene edit) | [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) — **Desktop only**; Cloud uses 3DAI | `vfprod` — [`BLENDER-MCP.md`](../packages/vfprod/BLENDER-MCP.md) |

## Do not install

- **Aggregator / “400 tools in one” servers** — they drown the agent and hide the studio tools.
- **Headroom proxy on Cloud Agent** — local compression proxy needs a host process; Cloud VMs are sandboxed. Embed the **pattern** via `packages/vfharness/playbooks/context-thrift.md` (CCR + ContentRouter). Optional Mac-only: `headroom wrap cursor` after lead seat — see `packages/vfmcp/GAP.md`.
- **Blender MCP on Cloud Agent** — needs local Blender + addon. Optional Desktop only (`vfprod/BLENDER-MCP.md`). Concept/STL from HQ stays 3DAI.
- **Archon** ([coleam00/Archon](https://github.com/coleam00/Archon)) — second harness/orchestrator. Embed workflow-gate patterns on `vfe2b` only; do not `curl | bash` / Docker Archon here.
- **Jeffallan fullstack-dev-skills plugin** — Claude Code marketplace skills. Common Ground tiers → `vfmem/MEMORY-UPDATE.md`. No `/plugin install` / `npx skills` on Cloud Agent.
- **Second SEO / GEO / AI-visibility stacks** — Treg is not relevant. Public marketing site from HQ stays locked; AEO skills (e.g. buildwithclaude `ai-search-visibility-audit`) stay **watch** until a public site exists under `vfbiz`. Warehouse `@aeo-foundations-architect` stays off-desk unless named.
- **Second Canva or image-gen farms** — Canva + Superdesign are enough for brand work.
- **Anything that posts, boosts, or DMs Instagram from this HQ.**
- **DeusData/codebase-memory-mcp binary** — coding-agent indexer that writes client config. The office-graph pattern is already `scripts/vfmem.py`. Local AST install only if the lead seat asks, and never by rewriting this repo's `.cursor/mcp.json`.
- **Hosted agent-memory plugins** (context-memory / Slova, memstack install, `basic-memory` Docker) — use `vfmem` + `owner-memory.md` + checkpoints. See `packages/vfmem/MEMORY-UPDATE.md`.
- **`mcp/3d-printer` (Orca/Bambu/OctoPrint…)** — printers stay on the floor. No Print from HQ.
- **Claude Code marketplace bulk install** (`/plugin marketplace add davepoon/buildwithclaude`, `all-agents@buildwithclaude`) — Cursor is the office; embed patterns only.
- **Crypto, x402 marketplaces, coding-agent swarms, aerospace, gaming, home IoT** — not the print floor. Includes [Bindu](https://github.com/GetBindu/Bindu) (`bindufy`, A2A Gateway, USDC) — watch patterns only; see `packages/vfresearch/sources/2026-08-31-bindu.md`. Studio MCP Hub **paid** x402 only after lead seat; free tools are registered in Core.
- **Cold-email infrastructure** — VF is inbound studio sales, not a spam shop.

## How to add one

HTTP no-secret servers go in Core `.cursor/mcp.json` (and Team MCP for Cloud). Servers that need a Mac process or a JSON key go in **`~/.cursor/mcp.json`** — see `packages/vfmcp/mcp.desktop.example.json`. Instances enable a subset with `mcpBind`.

1. Christian names the account (WhatsApp number, Sheet ID, Ads account) if the server needs one.
2. Add **one** server to the Core catalog (`core-mcp.json`) + CONNECT playbook.
3. Keep secrets out of git.
4. Same-day: one line in `CHANGELOG.md` Unreleased + a note here if the choice changes.
5. Pack agents may *use* the new tools. They still do not invent prices or send Instagram. VF WhatsApp send stays human.

## Suggested order

The first three office gaps are in Core (`CORE-MCP.md`). VF bind is `mcpBind`. Next, only if a pack is blocked:

1. Desktop Connect: Sheets credentials + WhatsApp QR (`CONNECT-SHEETS.md`, `CONNECT-WHATSAPP.md`).
2. Cloud Team MCP for `studiomcphub` (same path as 3DAI).
3. 3D AI Studio OAuth on Cloud (`CONNECT-3DAI.md`) if mesh-from-photo is the bottleneck.
4. instapdown (Instagram research, no login).
5. Inbox Zero if the mailbox is the bottleneck.
6. Meta Ads read-only if boost reporting is the bottleneck.
