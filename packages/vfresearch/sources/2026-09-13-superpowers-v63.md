# obra/superpowers v6.3 — VelvetOS gap review

**Reviewed:** 2026-09-13  
**Source:** https://github.com/obra/superpowers  
**Release reviewed:** v6.3.0 (2026-08-12)  
**Decision:** absorb selected execution-discipline patterns into existing `vfharness`; do **not** install/vendor the Superpowers runtime/plugin as a second harness.

## What VelvetOS already had

- brainstorming gate with Spike / Bounded / Architectural routing;
- writing/executing plans playbooks;
- systematic debugging;
- verification-before-claim;
- proof-before-code implementation discipline;
- high-risk dual-review convergence;
- graduated retry/fallback/downgrade/escalation ladder;
- branch-based Git workflow without mandatory Cloud worktrees.

## Accepted delta

### 1. Rulings, not stalls

Adopted as a fail-closed `safe_ruling` rung in the existing `vf_graceful_escalation.py` ladder.

Canonical receipt:

```text
Ruling: <decision> — <why> — <cost_if_wrong>
```

Allowed only for local, reversible ambiguity outside security/authority/external-side-effect gates. Required sensors/receipts cannot be overruled.

### 2. Evidence-bearing plan preflight

Before Task 1, `executing-plans.md` now requires actual rows for:

- self-consistency of every task;
- every task pair sharing file/interface/state/output-input;
- producer/consumer relation, finding, and action.

A plain "scan is clean" is not evidence.

### 3. Test-first executable behavior

`implementation-discipline.md` now distinguishes executable behavior from structural/prose changes:

- code/bugfix/automation: RED → GREEN → REFACTOR when behavior can be exercised;
- RED must fail for the expected reason;
- tests should be falsifiable and prefer real behavior;
- grep/string presence can prove wiring, not runtime behavior;
- Markdown/copy/static data/config do not receive ceremonial test theater.

### 4. Fresh-context review

Ordinary material changes now receive a lightweight reviewer packet with Goal, Spec, focused diff/base-head, scope, proof and known limitations — not the author's full reasoning history.

High-risk VelvetOS review remains stronger than the upstream default: two independent reviewers + deterministic proof + receipts/gates.

### 5. Parallel fan-out/fan-in discipline

Plan execution may dispatch independent tasks in parallel only when there is no shared-write state, producer/consumer dependency, or unresolved shared gate. Fan-in requires conflict inspection and integration proof. Nested/unbounded agent spawning is not adopted.

## Rejected / not adopted

- installing `obra/superpowers` as a runtime/plugin dependency;
- mandatory `subagent-driven-development` runtime;
- mandatory worktrees on Cloud workspaces;
- any rule that weakens VelvetOS human/constitutional gates;
- reviewer reruns of expensive proof solely because existing evidence is inconvenient to read.

## VelvetOS artifacts

- `packages/vfharness/scripts/vf_graceful_escalation.py`
- `scripts/check-vfharness-execution-discipline.py`
- `packages/vfharness/playbooks/executing-plans.md`
- `packages/vfharness/playbooks/writing-plans.md`
- `packages/vfharness/playbooks/implementation-discipline.md`
- `packages/vfharness/playbooks/critique-review.md`
- `packages/vfharness/LOOP.md`
- `packages/vfharness/EMBED.md`
- `packages/vfharness/SKILL.md`
- `scripts/check-skill-pattern-embeds.py`

## Verification contract

- structural wiring: `python3 scripts/check-skill-pattern-embeds.py`;
- safe-ruling behavior: `python3 scripts/check-vfharness-execution-discipline.py`;
- whole repository: `python3 scripts/check-all.py`;
- live worker/provider claims still require their existing runtime/provider receipts and, where applicable, `check-runtime-doctor.py --strict`.
