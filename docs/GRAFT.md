# Graft fit for Velvet Factory

Source: [trailhq/Graft](https://github.com/trailhq/Graft) (README read 2026-08-30).  
Pack: [`packages/vfgraft/`](../packages/vfgraft/).  
Check: `python3 scripts/check-vfgraft.py`.

HQ **sends Gmail and Instagram via tools** (`constitution/SEND.md`). Grok is optional backup. Do not invent ₪. Do not commit secrets.

## Verdict

**Embed the pattern. Skip the runtime.**

Graft's claim is the right pain for this office: every Cursor / Cloud Agent onboards from zero, rediscovers the desk, and sometimes opens the 273-specialist warehouse. Humans onboard once. Agents onboard every run.

The npm product does not fit this tree.

| Graft product | Why it misses this HQ |
|---|---|
| `graft build` tree-sitter | Markdown is not a supported language. Packs, skills, constitution, and the desk are skipped. |
| `graft build --deep` | Needs a provider key. Second model bill. |
| `graft/` cache | Gitignored local cache. Cloud Agents do not share it. |
| `graft init` MCP + hooks | Second coding-agent wiring. Locked by `vfe2b`. |
| Telemetry / API key | Secrets do not belong in git. |

What we kept is the part an agent actually reads: a **committed** folder of linked markdown nodes, a token-budgeted map, typed verbs, a blast-radius card, and a check that sources still exist.

## What Graft does (kept)

1. **Real explanations, not a symbol dump.** Each node says what that part of HQ does and how it connects.
2. **A graph you can grep.** No embeddings. No warm index. Files + `[[wikilinks]]`.
3. **Three depths.** Summary (what), sources (where), notes (human, not overwritten).
4. **Blast radius.** If a law or tool mode moves, the card lists what breaks.
5. **Ask table.** Job → two or three nodes, same idea as `graft ask`.

## What we did not install

`@nanonets/graft`, Graft MCP (`graft_find_code` and friends), Claude hooks, a `graft/` directory, or a provider key.

If this repo later grows a real TypeScript/Python app (not an office of Markdown), the lead seat can reopen `graft init --agents cursor --no-mcp`. Until then the office graph is `packages/vfgraft/`.

## How an agent uses it

1. Read [`packages/vfgraft/MAP.md`](../packages/vfgraft/MAP.md).
2. Open the job node (`morning-job`, `inquiry-job`, `content-job`, or `blast`).
3. Follow links into packs and tools that already exist.
4. Stop before send.

## Later (not now)

Graft MCP on a code-heavy subtree. WhatsApp / Sheets / print-pipeline MCP gaps stay in [`docs/MCP-FIT.md`](MCP-FIT.md) — they are not Graft's job.
