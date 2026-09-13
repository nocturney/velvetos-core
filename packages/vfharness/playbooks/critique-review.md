# Critique + review loop — Context Engineering Kit pattern

Source pattern: `NeoLabHQ/context-engineering-kit`. Embedded into the existing harness; it does not replace deterministic sensors or become an LLM judge-of-record.

## When to use

Use for architecture changes, security-sensitive edits, large PRs, new control-plane behavior, or any change where a single authoring pass can miss a class of failure.

## Loop

1. **Author pass** — implement against the task goal and named proof.
2. **Independent critique pass** — inspect the candidate from four lenses: correctness, regression/scope, safety/authority, and operator/user clarity.
3. **Evidence pass** — map every critique item to code, test, sensor, receipt, or explicit `UNPROVEN` state.
4. **Repair pass** — fix only supported findings; do not rewrite merely to satisfy stylistic disagreement.
5. **Re-run proof** — deterministic tests/sensors remain authoritative.
6. **Reflect once** — record one durable lesson only when it generalizes beyond this task; otherwise keep it in the checkpoint.

## Critique output

```text
Finding:
Lens: correctness | regression | safety | clarity
Evidence:
Severity: blocker | important | optional
Repair:
Verification:
```

No majority vote can override a failing sensor, a missing provider receipt, a human gate, or a constitutional rule.
