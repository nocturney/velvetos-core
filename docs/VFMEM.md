# HQ memory — codebase-memory-mcp, what we actually took

Source: [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) (read 2026-08-30).  
Paper: [arXiv:2603.27277](https://arxiv.org/abs/2603.27277).  
Pack: [`packages/vfmem/`](../packages/vfmem/).  
Check: `python3 scripts/check-vfmem.py`.

HQ **sends Gmail and Instagram via tools** (`constitution/SEND.md`). Grok is optional backup.  
Do not invent prices. Do not commit secrets. Do not `curl | bash` their installer from this repo.

## What the repo is

A local C MCP: tree-sitter graph, 15 tools, sub-ms queries, optional 3D UI. Their claim is 99% fewer tokens than file-by-file grep. The installer writes agent config.

## What helps Velvet Factory

The **query shape**, not the binary.

The office OS is already a graph: packs ↔ seats ↔ 28 desk specialists ↔ tools ↔ skills ↔ laws. Agents were paying the file-by-file tax on 273 warehouse rules.

| CBM tool | HQ command | Why it maps |
|---|---|---|
| `get_architecture` | `scripts/vfmem.py architecture` | One map instead of reading every pack |
| `search_graph` | `scripts/vfmem.py who <job>` | Pack + `@slug` + tool |
| `trace_path` | `scripts/vfmem.py impact <id>` | Blast radius before an edit |
| `detect_changes` | `scripts/vfmem.py impact --git` | Diff → packs |
| `manage_adr` | `scripts/vfmem.py adr` | Standing laws, read-only |
| dead-code | `scripts/vfmem.py dead` | Warehouse vs real missing files |
| Route nodes | `scripts/vfmem.py route` | The one pipeline |

The graph is rebuilt each run from `packages/manifest.json`, `.cursor/vf-desk.json`, `.cursor/agency-agents.json`, and `.cursor/skills`. No SQLite in git. No invented nodes.

## What we did not take

See [`packages/vfmem/LOCK.md`](../packages/vfmem/LOCK.md) and the skip rows in [`packages/vfmem/catalog.json`](../packages/vfmem/catalog.json).

- Native installer / daemon / `:9749` UI
- Hybrid LSP and 162-language AST (this repo is markdown packs)
- Cross-service HTTP / gRPC edges

`docs/MCP-FIT.md` still says MCP servers are added in Cursor settings after Christian names an account. vfmem is the office-graph layer that lives **in git** so every cloud agent can query it without a binary.

## Later (lead seat only)



## Cognee local semantic backend — 2026-09-23

`vfmem` remains the canonical memory/office graph. Cognee is now an **optional local
derived index** behind it, defined by `packages/vfmem/cognee.json` and
`packages/vfmem/scripts/vf_cognee.py`.

The integration deliberately does not create a second authority layer:

- canonical files and live systems remain sources of truth;
- sync is one-way from a curated 66-source / 13-category durable allowlist into a content-hash dataset;
- every source carries category, authority and freshness metadata;
- ingestion keeps each canonical source as its own deterministic derived Cognee document, then runs local granular `cognify` chunking;
- the local embedding contract is multilingual FastEmbed (`paraphrase-multilingual-MiniLM-L12-v2`, 384d) with 384-token chunks;
- recall returns explicit chunks with a fail-closed mapping back to canonical source path/SHA/category/authority/freshness, and still requires canonical verification before action;
- cloud model credentials are ignored by default; the reference mode is keyless/local;
- an unavailable or unhealthy Cognee runtime falls back to the original vfmem search;
- secrets, credentials, raw transcripts, customer-sensitive data and live finance/production/publication/inventory/schedule state are denied.

Operator details and the staged update/rollback procedure: [`packages/vfmem/COGNEE.md`](../packages/vfmem/COGNEE.md).
