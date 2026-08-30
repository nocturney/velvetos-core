---
name: vfmem
description: Query the Velvet Factory office graph (pack / specialist / tool) without dumping the 273-rule warehouse. Pattern from codebase-memory-mcp; no third-party binary.
---

# vfmem

Use when the user asks מי מטפל, which pack, office map, impact of a change, or points at [codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp).

## Do this

```bash
python3 scripts/vfmem.py who <job>
python3 scripts/vfmem.py architecture
```

Then open only the named pack and mention only that `@slug`.

## Do not

- Install the DeusData binary or add it to `.cursor/mcp.json` from this repo
- Activate warehouse specialists
- Invent ₪ or Insights
- Send Gmail or Instagram
