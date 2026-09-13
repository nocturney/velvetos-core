# Critique + review loop — Context Engineering Kit + ECC convergence patterns

Source patterns: `NeoLabHQ/context-engineering-kit` and selectively `affaan-m/ECC` Santa-loop convergence. Embedded into the existing harness; it does not replace deterministic sensors or become an LLM judge-of-record.

## When to use

Use for architecture changes, security-sensitive edits, large PRs, new control-plane behavior, or any change where a single authoring pass can miss a class of failure.

Enable **high-risk mode** for constitution/permissions, automation/runtime/control-plane behavior, publish pipelines, finance/books/payment behavior, secrets/security, or large cross-package changes.

## Standard loop

1. **Author pass** — implement against the task goal and named proof.
2. **Independent critique pass** — inspect the candidate from four lenses: correctness, regression/scope, safety/authority, and operator/user clarity.
3. **Evidence pass** — map every critique item to code, test, sensor, receipt, or explicit `UNPROVEN` state.
4. **Repair pass** — fix only supported findings; do not rewrite merely to satisfy stylistic disagreement.
5. **Re-run proof** — deterministic tests/sensors remain authoritative.
6. **Reflect once** — record one durable lesson only when it generalizes beyond this task; otherwise keep it in the checkpoint.

## High-risk convergence mode

Run up to **3 rounds**:

1. Reviewer A inspects the candidate with no access to Reviewer B's findings.
2. Reviewer B independently inspects the same candidate, ideally through a different model/harness when available.
3. Normalize both outputs into the critique format below.
4. Merge only evidence-backed blocker/important findings.
5. Repair supported findings.
6. Run all deterministic proof required by the task, including `python3 scripts/check-all.py` when applicable.
7. Start the next round with fresh reviewer context.

Convergence requires:

- Reviewer A: no unresolved blocker/important finding.
- Reviewer B: no unresolved blocker/important finding.
- Required deterministic sensors: PASS.
- Required provider/runtime receipts: present and healthy, or task state remains `UNPROVEN`/`BLOCKED`.
- Human/constitutional gates: satisfied.

If convergence is not reached after 3 rounds, do not claim completion or auto-push/auto-publish. Record unresolved findings in the checkpoint.

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
