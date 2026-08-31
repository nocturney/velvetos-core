# blast

## Summary

Blast radius for this office: which jobs and tools break when a law, tool mode, or desk row moves. Read this before editing the always-on desk rule or Gmail/Calendar/Canva modes.

## Sources

- `.cursor/rules/velvet-factory-desk.mdc`
- `.cursor/vf-desk.json`
- `packages/vfgraft/MAP.md`

## Links

- validates [[laws]]
- validates [[desk]]
- validates [[tools]]
- validates [[skills]]
- uses [[maps]]

## Notes

| If this moves | What depends on it |
|---|---|
| Desk laws / `velvet-factory-desk.mdc` | Every skill, every seat, every job node |
| Gmail mode (read → send) | [[morning-job]], [[inquiry-job]], `vfbooks` |
| Pipeline stages | `vfconvert`, `vfsales`, `vfprod`, `vfbooks` pickup |
| Canva disconnect | [[content-job]], `vfcovers`, `vfigos` — failover to `studio/render.py` then Superdesign |
| Grok-bot boundary | `vfigos` send, `vfsales` close, printers — quota outage → QUEUE / LIVE-PACKET human post (`docs/GROK-FAILOVER.md`) |
| Seat list / sixth seat | Constitution, brief slots, desk check |
| Treg without login | `vfinsights`, `vfgrowth`, `vfresearch` live reads — WebSearch / «אין ספירה»; music → HeyOrca |
| Research desk wall (ChatGPT/Gemini/Perplexity) | 06:15 orchestra — failover to open desks same turn; never invent body |
| Web / image native tools | `vfresearch`, `vfcovers` — failover in `constitution/ORCHESTRA.md`; Instagram still Canva-first |

Do not "fix" a missing ₪ or Insights number to make the blast look closed.
Do not sit idle when a tool is down — hand off per [[tools]] / `constitution/ORCHESTRA.md`.
