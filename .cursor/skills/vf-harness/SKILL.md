---
name: vf-harness
description: Run the Velvet Factory outer harness — guides, sensors, bounded loop, checkpoint, escalate. No second runtime. HQ sends via tools (constitution/SEND.md).
---

# VF harness

Use when the user asks for רתמה, harness, AGENTS.md, checkpoint, escalate, harden a repeating agent failure, or **Grok Bot quota failover** / פרסום חי בזמן מכסה ריקה.

## Packs and specialists

- Pack: `vfharness` (infrastructure, not a sixth seat)
- Mention: `@workflow-architect` (desk) — `@multi-agent-systems-architect` only if the user asks for that warehouse slug
- Guide file wins over the conversation: `AGENTS.md`
- Grok quota outage: `packages/vfharness/playbooks/grok-failover.md` + `grok-outage-tools.md` + `packages/vfigos/QUEUE.md` + `LIVE-PACKET.md`
- Truncated / skeleton output: `packages/vfharness/playbooks/full-output-enforcement.md` (from taste-skill `output-skill`)
- Success claims: `packages/vfharness/playbooks/verification-before-claim.md` (from obra/superpowers)
- New/edited HQ skills: `packages/vfharness/playbooks/skill-authoring.md`

## Loop

1. Read `AGENTS.md` + `packages/vfharness/EMBED.md`.
2. Plan steps on an **existing** pack. Do not open a new product pack for an idea.
3. Execute one step. After catalog/rule/pack edits: `python3 scripts/check-all.py`.
4. Sensor or field-check fails → fix once → fail again → fill `packages/vfharness/templates/escalation.md` and stop.
5. Long task (5+ tool calls): open `packages/vfharness/state/<task-id>/` with `task_plan.md`, `findings.md`, `progress.md` per `PLANNING-FILES.md`. Re-read at session start.
6. Before close: write `checkpoint.json` from the checkpoint schema. For a משמרת: `planned_steps` before heavy work; `gate` when blocked on ₪ or human field. See `playbooks/oma-patterns.md`.
7. Grok down: **send** the office brief (`htmlBody` תצוגה 3) to `nocturney@gmail.com`. Live IG → `vfigos/SEND.md` (tool or Canva+Drive+Gmail). Do not claim the feed posted if no publish tool fired.

## Forbidden

Auto-DM, boost, printer jobs from HQ, invented ₪ or Insights, CrewAI/AutoGPT, LLM-as-judge as a gate for ILS, inventing a blocked source body, claiming the IG feed posted without a publish tool. Gmail `send_message` and IG-via-tools are **allowed** (`constitution/SEND.md`).

## Output

Best artifact + unresolved issues + which sensor ran. Do not hide a red sensor behind fluent Hebrew.
