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
- Google Cloud SDK diagnostics/deploy discipline: `packages/vfharness/playbooks/gcloud-ops.md`
- Handoff/release archive integrity with 7-Zip: `packages/vfharness/playbooks/deterministic-packaging.md`
- Long-horizon state (not chat replay): `packages/vfharness/playbooks/skillstate.md` (arXiv SKILLSTATE)

## Execution routing

Canonical execution semantics live only in `packages/vfharness/LOOP.md`; this skill must not restate or override that loop. Use these trigger routes:

- material engineering/policy/integration → `playbooks/engineering-delivery-chain.md`;
- bug/sensor/tool failure → `playbooks/systematic-debugging.md`;
- human-only blocker → `playbooks/human-step-wizard.md`;
- long task/state recovery → `PLANNING-FILES.md` + `playbooks/skillstate.md`;
- Google Cloud diagnosis/deploy → `playbooks/gcloud-ops.md`;
- archive/handoff packaging → `playbooks/deterministic-packaging.md`;
- new/edited instructions/rules/skills → `playbooks/agent-instruction-qa.md` + `python3 scripts/check-skill-health.py`.

After catalog/rule/pack edits run `python3 scripts/check-all.py`. Cross-tool continuation uses existing `office/control/HANDOFF.json` and `packages/vfmem/HANDOFF.md`; never create a second orchestrator.

## Forbidden

Auto-DM, boost, printer jobs from HQ, invented ₪ or Insights, CrewAI/AutoGPT, LLM-as-judge as a gate for ILS, inventing a blocked source body, claiming the IG feed posted without a publish tool. Gmail `send_message` and IG-via-tools are **allowed** (`constitution/SEND.md`).

## Output

Best artifact + unresolved issues + which sensor/proof ran. Do not hide a red sensor behind fluent Hebrew.
