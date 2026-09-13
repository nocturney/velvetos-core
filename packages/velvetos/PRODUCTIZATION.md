# VelvetOS productization workflow — selective PM patterns

Source pattern: `phuryn/pm-skills`. The marketplace is not installed. High-value product-management workflows are mapped onto the existing VelvetOS planning and evidence model.

## Workflow

1. **Problem frame** — user/business problem, current workaround, evidence, non-goals.
2. **Discovery** — interviews/feedback/usage evidence; separate requests from underlying jobs.
3. **Assumption map** — desirability, viability, feasibility, adoption; mark high-impact/low-evidence assumptions first.
4. **Prioritization** — impact, confidence, effort, reversibility, operational risk. A loud request is not automatically priority one.
5. **PRD-lite** — outcome, actors, source-of-truth changes, states, gates, success measures, failure modes, rollout/rollback.
6. **Launch plan** — staged exposure, owner/operator communication, instrumentation, support/failover.
7. **Outcome review** — compare observed result with success measures; promote durable learning into existing memory/retro paths.

## Required artifact fields

`problem`, `evidence`, `target_outcome`, `non_goals`, `assumptions`, `risks`, `success_measures`, `rollback`, `owner`, `next_decision`.

This is for turning VelvetOS capabilities into a coherent product. It does not create a new business runtime, PM database, or parallel roadmap system.
