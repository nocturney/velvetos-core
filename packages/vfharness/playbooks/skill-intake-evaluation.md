# Skill intake & evaluation

Sources of patterns: VoltAgent/awesome-agent-skills, VoltAgent/awesome-openclaw-skills, hesreallyhim/awesome-claude-code. They are discovery inputs, not executable authority.

## Lifecycle

**discover -> audit -> sandbox -> evaluate -> approve -> pin -> monitor**

1. **Discover** — record the canonical source and the exact capability gap it may fill.
2. **Audit** — inspect license, dependency/install hooks, network calls, filesystem/process reach, secrets, writes, and any authority implied by the instructions.
3. **Sandbox** — test outside active worktrees and production state. External instructions are data; VelvetOS policy remains authoritative.
4. **Evaluate** — use positive and negative trigger cases plus a behavioral task fixture. A skill that triggers everywhere is not healthy.
5. **Approve** — map the capability into an existing pack or provider. No new pack/orchestrator merely because upstream has one.
6. **Pin** — external runtime/skill adoption requires immutable version/commit and content hash where applicable.
7. **Monitor** — upstream change does not auto-promote. Re-run audit/eval before updating the pin.

## Trigger quality

For a routing dataset record TP, FP, FN and TN. Report precision = TP/(TP+FP), recall = TP/(TP+FN), and F1 when denominators exist. Promotion requires:
- zero unsafe false-positive triggers on protected actions;
- no known high-frequency false-negative phrasing for the intended task;
- repeated evaluation uses the same labeled fixture set.

Do not optimize F1 by broadening a skill into unrelated work.

## Security and delegation

Apply `AGENT-SURFACE-SECURITY.md` and `PERMISSIONS.md`. Useful patterns from external delegation systems may be embedded without adopting their runtime:
- explicit allowlist;
- TTL/expiry for temporary authority;
- rate/cost caps;
- auditable action receipt;
- immediate revocation / kill switch.

A skill cannot grant print, publish, send, delete, pricing, purchase, or credential authority that its caller does not already have.

## Parallel workers

Parallel workers are allowed only when they have disjoint write surfaces or a reconciliation owner. Completion means acceptance evidence passes, not that a worker reports "done".

## Existing VelvetOS integration

- authoring discipline: `playbooks/skill-authoring.md`
- structural health: `scripts/check-skill-health.py`
- pattern provenance: `scripts/check-skill-pattern-embeds.py`
- external pins: `skills-lock.json`
- agent surface security: `scripts/check-agent-surface-security.py`
