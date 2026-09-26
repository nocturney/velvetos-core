# VelvetOS Tool Authority

Updated 2026-09-26. Machine source: `packages/velvetos/TOOL-STATUS.json`.

## Instagram
Canonical route: `VF gates -> Cloudflare Instagram Publisher -> official Meta Instagram Graph API -> live Graph verification`.

Live scheduler endpoint: `https://velvetos-instagram-publisher.velvetos-vf.workers.dev`.

OpenPost is **FROZEN** after missed scheduled publications without a timely failure alert. It has zero active schedules after migration. Its old implementation is retained only under `packages/vfigos/archive/` as audit/rollback evidence.

The Velvet Instagram MCP bridge (based on `adelaidasofia/instagram-mcp`) is **not Meta-owned**. It remains a read/Insights/live-verification bridge. It is not scheduling authority.

## Forbidden
Canva/vfcanva are forbidden and removed from executable project surfaces. Historical commits/audit artifacts may mention them, but no current route may invoke them.

Run `python3 scripts/check-tool-authority.py` after any tool/routing change.
