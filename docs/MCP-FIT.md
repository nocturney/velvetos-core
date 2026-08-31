# MCP fit for Velvet Factory

Source: [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) (reviewed 2026-08-30).  
Grok / ChatGPT / Gemini / Perplexity gap vs this HQ: [`packages/vfmcp/GAP.md`](../packages/vfmcp/GAP.md) (reviewed 2026-08-31).  
HQ **sends Gmail and Instagram via tools** (`constitution/SEND.md`). Boosts and auto-DM stay forbidden. Printers stay on the floor. Treg is not relevant.  
Do not invent prices. Do not commit secrets.

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
| **WebSearch / WebFetch** | Live web + URL fetch (ChatGPT/Gemini/Perplexity/Grok browse equivalent) | `vfresearch`, `vfgrowth` |
| **GenerateImage** | User-asked stills. Instagram still Canva-first | `vfcovers`, `vfbriefux` |
| **Treg** | **Not relevant** — do not login or `call` | — |
| **Mobbin** | Real-app UI patterns | `vfbriefux` |
| **Superdesign** | Canvas / graphics | `vfcovers`, `vfbriefux` |
| **Grok Bot** | Optional backup only. HQ sends via tools | `vfigos/SEND.md` |

Skip extra Gmail, extra Canva, extra SEO crawlers, and extra “AI visibility” servers unless Treg is missing a specific account.

**Office graph (already in git, not a Cursor MCP add):** [`vfmem`](../packages/vfmem/) takes the *query shape* from [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) (`architecture` / `who` / `impact` / `adr`) and runs it on `vf-desk.json` + `manifest.json`. Do not install their C binary from this repo. Write-up: [`docs/VFMEM.md`](VFMEM.md).

## Do this first (real studio gaps)

Three holes the office OS still has. Each one is a Cursor MCP add — not a new pack dump.

### 1. WhatsApp — inquiry-to-order

Israeli print sales live here. Gmail alone does not close the loop for `vfconvert` / `vfsales`.

| Server | Role | Notes |
|---|---|---|
| [lharries/whatsapp-mcp](https://github.com/lharries/whatsapp-mcp) | Personal WhatsApp: search chats, contacts, send | Best if the studio number is a normal phone, not Business API |
| [nakulben/whatsapp-mcp](https://github.com/nakulben/whatsapp-mcp) | WhatsApp Business templates via Meta Cloud API | Use if the studio already has a Business number |
| [Infobip/mcp](https://github.com/infobip/mcp) | Official SMS / WhatsApp / Viber | Heavier; only if you already pay Infobip |

**Rule:** drafts and search in Cursor. Do not auto-send quotes or proofs without a human click. Same discipline as Instagram: HQ reviews, a human or Grok Bot sends.

**Packs:** `vfconvert`, `vfsales`, `vfops`.

### 2. Google Sheets — the studio ledger

Drive can open a file. It cannot reliably read rows, write a job line, or update a SKU reprint. Books, jobs, quotes, and cost sheets almost certainly live in Sheets.

| Server | Role |
|---|---|
| [freema/mcp-gsheets](https://github.com/freema/mcp-gsheets) | Read / write / format / manage tabs |
| [xing5/mcp-google-sheets](https://github.com/xing5/mcp-google-sheets) | Same job, Python |

Pick **one**. Point it at the real workbook IDs Christian names — do not invent a new ledger.

**Packs:** `vfbooks`, `vfsku`, `vfprod`, `vfsales`, `vfcost`.

### 3. Print file pipeline — CMYK / mockup / print PDF

Canva is the art desk. The floor still needs print-ready files.

| Server | Role |
|---|---|
| [codex-curator/studiomcphub](https://github.com/codex-curator/studiomcphub) | Mockups, CMYK conversion, print-ready PDF, upscale, background removal |
| [attalla1/photopea-mcp-server](https://github.com/attalla1/photopea-mcp-server) | Local Photoshop-class edits (layers, export) if the Mac already uses Photopea |

Start with Studio MCP Hub for “make this print-safe.” Keep Canva as the brand canvas. Do not invent click charges or paper prices (`vfcost` rule).

**Packs:** `vfprod`, `vfcovers`, `vfsku`.

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

## Do not install

- **Aggregator / “400 tools in one” servers** — they drown the agent and hide the studio tools.
- **Headroom proxy on Cloud Agent** — local compression proxy needs a host process; Cloud VMs are sandboxed. Embed the **pattern** via `packages/vfharness/playbooks/context-thrift.md` (CCR + ContentRouter). Optional Mac-only: `headroom wrap cursor` after lead seat — see `packages/vfmcp/GAP.md`.
- **Second SEO / GEO / AI-visibility stacks** — Treg already is the data catalog. Connect GA / GSC / GBP there first.
- **Second Canva or image-gen farms** — Canva + Superdesign are enough for brand work.
- **Anything that posts, boosts, or DMs Instagram from this HQ.**
- **DeusData/codebase-memory-mcp binary** — coding-agent indexer that writes client config. The office-graph pattern is already `scripts/vfmem.py`. Local AST install only if the lead seat asks, and never by rewriting this repo's `.cursor/mcp.json`.
- **Crypto, x402 marketplaces, coding-agent swarms, aerospace, gaming, home IoT** — not the print floor. Includes [Bindu](https://github.com/GetBindu/Bindu) (`bindufy`, A2A Gateway, USDC) — watch patterns only; see `packages/vfresearch/sources/2026-08-31-bindu.md`.
- **Cold-email infrastructure** — VF is inbound studio sales, not a spam shop.

## How to add one (Cursor, not this git repo)

MCP lives in Cursor settings / Cloud Agent integrations. This repository stays a map.

1. Christian names the account (WhatsApp number, Sheet ID, Ads account).
2. Add **one** server from the tables above.
3. Keep secrets out of git.
4. Same-day: one line in `CHANGELOG.md` Unreleased + a note here if the choice changes.
5. Pack agents may *use* the new tools. They still do not invent prices or send Instagram.

## Suggested order

1. Google Sheets (unlocks books / jobs / SKU without a new database).
2. WhatsApp (closes inquiry → quote → order).
3. Studio MCP Hub (print-safe files next to Canva).
4. instapdown (Instagram research, no login).
5. Inbox Zero if the mailbox is the bottleneck.
6. Meta Ads read-only if boost reporting is the bottleneck.

Stop after the first three unless a pack is blocked on a specific live account.
