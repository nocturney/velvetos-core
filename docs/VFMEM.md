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
- A second MCP next to Gmail / Calendar / Drive / Canva

`docs/MCP-FIT.md` still says MCP servers are added in Cursor settings after Christian names an account. vfmem is the office-graph layer that lives **in git** so every cloud agent can query it without a binary.

## Later (lead seat only)

If the Mac needs AST over `scripts/*.py`, add codebase-memory-mcp **locally** with `--skip-config` or a manual MCP entry. Do not let the installer rewrite this repo's `.cursor/mcp.json` (Canva stays the only HTTP server committed here).
