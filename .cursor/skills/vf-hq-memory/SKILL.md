---
name: vf-hq-memory
description: Route a Velvet Factory job through the office graph before opening many packs. Use for מי מטפל, which pack, office map, impact, ADR, or codebase-memory-mcp.
---

# HQ memory

Use when the user asks מי מטפל, which pack, what is the office map, impact of changing a pack, standing decisions, or mentions [codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp).

## Pack

- Pack: `vfmem`
- Pattern source only. **Do not install** their C binary from this repo.

## Run first

```bash
python3 scripts/vfmem.py who <job>
```

Other queries: `architecture`, `impact <pack>`, `impact --git`, `route <stage>`, `dead`, `adr`.

## Then

1. Mention only the returned `@slug`.
2. Open that pack / skill / tool.
3. Keep HQ laws: no send, no invented ₪, no invented Insights, pickup Sderot only.

Do not dump `.cursor/rules/` or the 273-agent warehouse after a graph hit.
