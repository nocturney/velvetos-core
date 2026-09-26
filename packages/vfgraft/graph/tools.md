# tools

## Summary

Gmail (`nocturney@gmail.com`) is read-and-send; Calendar and Drive keep their existing office roles. Instagram scheduling/publish authority is the Cloudflare Publisher (`packages/vfigos/PUBLISHER.json`) -> official Meta Instagram Graph API. The Instagram MCP bridge is read/Insights/live verification only. Canva/vfcanva are removed/forbidden; OpenPost is frozen. Treg is not relevant.

## Sources

- `.cursor/vf-desk.json`
- `docs/AGENCY-TOOLS.md`
- `docs/CANVA.md`
- `packages/vfmcp/GAP.md`
- `constitution/SEND.md`

## Links

- part_of [[desk]]
- validates [[laws]]
- depends_on [[grok-bot]]

## Notes

For Instagram publication, route through `packages/vfigos/SEND.md`; never fall back to Canva or OpenPost. iCloud is Mac-only; Cloud reads the Drive mirror. 3D AI Studio keeps its scoped rules.

**Failover:** any tool down → backup tool **same turn** (`constitution/ORCHESTRA.md`). No empty finish. No invented ₪ / Insights / blocked body. Do not wait for Christian or Grok.
