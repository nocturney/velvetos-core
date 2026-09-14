# Findings — Superpowers v6.3 harness delta

## Existing strengths

- `brainstorm-gate.md` already has Spike / Bounded / Architectural routing from Superpowers v6.3.
- `verification-before-claim.md` already enforces evidence-before-claim.
- `critique-review.md` already exceeds ordinary Superpowers review for high-risk work: dual independent reviewers + deterministic proof.
- `implementation-discipline.md` already requires proof-before-code, but not observable RED before executable behavior changes.
- `vf_graceful_escalation.py` already provides retry → fallback → downgrade → escalate and is the correct place to extend autonomy.

## Gaps being closed

1. `executing-plans.md` still says plan gap / second failed verification => stop and ask, which conflicts with autonomy and the existing graduated ladder.
2. No evidence-bearing preflight matrix across tasks that share files/interfaces.
3. No harness-level test-first rule for executable behavior and bug fixes.
4. No lightweight fresh-context reviewer path for ordinary material changes.
5. Parallel fan-out/fan-in exists conceptually in agent rules but is not part of canonical plan execution.
6. `SKILL.md`, `LOOP.md` and `EMBED.md` still contain binary-escalation wording that should be reconciled.

## Guardrails

- A ruling may never override a failing required sensor, missing runtime/provider receipt, human/constitutional gate, security-sensitive decision, destructive/irreversible action, or policy-gated external side effect.
- `safe_ruling` must be opt-in/fail-closed in code.
- No whole `obra/superpowers` install, no second runtime, no mandatory worktrees.
- Structural string checks prove wiring only; behavioral proof must exercise the ladder implementation.
