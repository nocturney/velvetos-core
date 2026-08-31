---
name: vf-velvetos
description: Orient on VelvetOS — universal business + social desk with tenant profiles. Use when the user asks for VelvetOS, tenant חדש, multi-IG, אוניברסלי, or another business vertical without breaking Velvet Factory.
---

# VelvetOS

## Pack

- Pack: `velvetos`
- Mention: `@workflow-architect` / `@studio-operations`
- Write-up: `docs/VELVETOS.md`

## Do this

1. Read `packages/velvetos/ACTIVE.json` → load `tenants/<id>.json`.
2. Follow `KERNEL.md` + `PIPELINE.md` + `CHANNELS.md`.
3. If the job is a new vertical: copy from `tenants/_examples/`, fill real facts, keep `status: example` until lead activates.
4. Do not change ACTIVE without lead seat.
5. After edits: `python3 scripts/check-velvetos.py`.

## Do not

- Break velvet-factory while it is active
- Invent ₪, Insights, or IG handles
- Auto-DM / boost
- Create a new pack per business
- Open medical/legal Drive folders unless the user names them
