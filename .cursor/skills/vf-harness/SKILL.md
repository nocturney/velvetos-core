---
name: vf-harness
description: Run the Velvet Factory outer harness — guides, sensors, bounded loop, checkpoint, engineering delivery, instruction QA, human-only gates and escalation. No second runtime. HQ sends via tools (constitution/SEND.md).
---

# VF harness

Use when the user asks for רתמה, harness, AGENTS.md, checkpoint, escalate, harden a repeating agent failure, material engineering delivery, agent/rule prompt QA, a human-only setup gate, or **Grok Bot quota failover** / פרסום חי בזמן מכסה ריקה.

## Packs and specialists

- Pack: `vfharness` (infrastructure, not a sixth seat)
- Mention: `@workflow-architect` (desk) — `@multi-agent-systems-architect` only if the user asks for that warehouse slug
- Guide file wins over the conversation: `AGENTS.md`
- Grok quota outage: `packages/vfharness/playbooks/grok-failover.md` + `grok-outage-tools.md` + `packages/vfigos/QUEUE.md` + `LIVE-PACKET.md`
- Truncated / skeleton output: `packages/vfharness/playbooks/full-output-enforcement.md` (from taste-skill `output-skill`)
- Success claims: `packages/vfharness/playbooks/verification-before-claim.md` (from obra/superpowers)
- Skill-first: `packages/vfharness/playbooks/skill-first.md` (from obra `using-superpowers`)
- New/edited HQ skills: `packages/vfharness/playbooks/skill-authoring.md` + `agent-instruction-qa.md`
- Material engineering change: `packages/vfharness/playbooks/engineering-delivery-chain.md`
- Human-only blocker: `packages/vfharness/playbooks/human-step-wizard.md`
- Bugs/tool failures: `packages/vfharness/playbooks/systematic-debugging.md`
- Long-horizon state (not chat replay): `packages/vfharness/playbooks/skillstate.md` (arXiv SKILLSTATE)

## Loop

1. Read `AGENTS.md` + `packages/vfharness/EMBED.md`.
2. Plan steps on an **existing** pack. Do not open a new product pack for an idea.
3. Material engineering/policy/integration work → `engineering-delivery-chain.md`: recover settled decisions → implementation spec → vertical tickets → branch implementation → quality + spec review → PR/CI → runtime proof.
4. Execute one step. After catalog/rule/pack edits: `python3 scripts/check-all.py`.
5. Sensor or field-check fails → `systematic-debugging.md`; fix the supported root cause. Repeated/full failure → fill `packages/vfharness/templates/escalation.md` and stop guessing.
6. If the only blocker is genuinely human-only, use `human-step-wizard.md`: finish everything else first, request the minimum action, then verify and resume yourself.
7. Long task (5+ tool calls): open `packages/vfharness/state/<task-id>/` with `task_plan.md`, `findings.md`, `progress.md` per `PLANNING-FILES.md`. Re-read at session start. Each turn: guide \(P\) + checkpoint \(\Sigma\) + latest observation \(O\) only (`playbooks/skillstate.md`).
8. Before close: write `checkpoint.json` from the checkpoint schema. For a משמרת: `planned_steps` before heavy work; `gate` when blocked on ₪ or human field. See `playbooks/oma-patterns.md`.
9. New/edited agent instructions, rules or skills → `agent-instruction-qa.md` + `python3 scripts/check-skill-health.py`; keep routers thin and one authority per rule.
10. Grok down: **send** the office brief (`htmlBody` תצוגה 3) to `nocturney@gmail.com`. Live IG → `vfigos/SEND.md` (tool or Canva+Drive+Gmail). Do not claim the feed posted if no publish tool fired.

## Forbidden

Auto-DM, boost, printer jobs from HQ, invented ₪ or Insights, CrewAI/AutoGPT, LLM-as-judge as a gate for ILS, inventing a blocked source body, claiming the IG feed posted without a publish tool. Gmail `send_message` and IG-via-tools are **allowed** (`constitution/SEND.md`).

## Output

Best artifact + unresolved issues + which sensor/proof ran. Do not hide a red sensor behind fluent Hebrew.
