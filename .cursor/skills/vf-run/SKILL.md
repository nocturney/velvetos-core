---
name: vf-run
description: Coordinate one Velvet Factory job as an Orca-style run — isolate the folder, pick one existing crew, end in worker_done / escalation / decision_gate. Do not install Orca. HQ sends via tools.
---

# Run (Orca desk)

Use when the user asks for משמרת, `@vfe2b run`, Orca run, coordinate this job, or a card with `worker_done` / `escalation` / `decision_gate`.

## Overlay

Read `packages/vfe2b/crews/run.md` and follow it. This is not a sixth product pack.

1. Name the job the user gave. One folder.
2. Pick **one** existing crew and run that crew's file:
   - morning brief → `packages/vfe2b/crews/morning-brief.md` (or `.cursor/skills/vf-morning-brief/SKILL.md`)
   - inquiry / quote → `packages/vfe2b/crews/inquiry.md` (or `.cursor/skills/vf-inquiry-chain/SKILL.md`)
   - content / covers → `packages/vfe2b/crews/content.md` (or `.cursor/skills/vf-content-sprint/SKILL.md`)
   - research → `packages/vfe2b/crews/research.md`
   - books / numbers → `packages/vfe2b/crews/books-data.md`
3. Emit the outcome card from `run.md`. Exactly one of: `worker_done`, `escalation`, `decision_gate`.
4. Stop.

## Laws

- Do not install Orca or a second coding agent. Cursor is the office.
- HQ sends Gmail and Instagram via tools (`constitution/SEND.md`). Customer WhatsApp stays human. Printers stay on the floor.
- Do not invent ₪ or Insights. Missing → **חסר** / **אין במקור**.
- Fan-out (max 3) only for `vfcopy` / `vfcovers`. Never for price or send.
- Three misses on the same fact → circuit break. Do not guess.
