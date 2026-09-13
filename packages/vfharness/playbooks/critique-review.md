# Critique + review loop — Context Engineering Kit + ECC + Superpowers fresh-review patterns

Source patterns: `NeoLabHQ/context-engineering-kit`, selectively `affaan-m/ECC` Santa-loop convergence, and `obra/superpowers` requesting/receiving-code-review discipline. Embedded into the existing harness; it does not replace deterministic sensors or become an LLM judge-of-record.

## When to use

Use a **light fresh-context review** for any material ordinary change before merge/completion claim when a second pass can catch correctness, regression or scope mistakes.

Use the full standard loop for architecture changes, security-sensitive edits, large PRs, new control-plane behavior, or any change where a single authoring pass can miss a class of failure.

Enable **high-risk mode** for constitution/permissions, automation/runtime/control-plane behavior, publish pipelines, finance/books/payment behavior, secrets/security, or large cross-package changes.

## Fresh-context review — default for material ordinary changes

The reviewer gets the work product and the requirements, **not the author's full conversation/reasoning history**.

Reviewer packet:

```text
Goal:
Spec / authority pointer:
Base / head or focused diff:
Files in scope:
Out of scope:
Proof already run + receipts:
Known limitations / UNPROVEN items:
```

Review lenses:

1. correctness vs Goal/Spec;
2. regression/scope creep;
3. safety/authority boundaries;
4. operator/user clarity where relevant.

Output:

```text
Finding:
Lens: correctness | regression | safety | clarity
Evidence:
Severity: blocker | important | optional
Repair:
Verification:
```

Rules:

- Fresh reviewer should not inherit the author's assumptions by default.
- Read existing test/sensor/receipt evidence before re-running it. Re-run only if evidence is stale, ambiguous, missing coverage, or the repair changes the proof target.
- Fix blocker/important findings that are evidence-backed. Optional style disagreements do not force churn.
- A reviewer opinion cannot override a deterministic failing sensor, missing provider/runtime receipt, human gate or constitutional rule.

For multi-task plans, perform a fresh whole-plan review after fan-in even if individual tasks were reviewed.

## Standard loop

1. **Author pass** — implement against the task goal and named proof.
2. **Independent critique pass** — inspect the candidate from four lenses: correctness, regression/scope, safety/authority, and operator/user clarity.
3. **Evidence pass** — map every critique item to code, test, sensor, receipt, or explicit `UNPROVEN` state.
4. **Repair pass** — fix only supported findings; do not rewrite merely to satisfy stylistic disagreement.
5. **Re-run proof** — deterministic tests/sensors remain authoritative; do not rerun unchanged proof solely because narration is inconvenient.
6. **Reflect once** — record one durable lesson only when it generalizes beyond this task; otherwise keep it in the checkpoint.

## High-risk convergence mode

Run up to **3 rounds**:

1. Reviewer A inspects the candidate with no access to Reviewer B's findings.
2. Reviewer B independently inspects the same candidate, ideally through a different model/harness when available.
3. Both receive fresh reviewer packets, not the author's full reasoning history.
4. Normalize both outputs into the critique format.
5. Merge only evidence-backed blocker/important findings.
6. Repair supported findings.
7. Run all deterministic proof required by the task, including `python3 scripts/check-all.py` when applicable.
8. Start the next round with fresh reviewer context if another round is needed.

Convergence requires:

- Reviewer A: no unresolved blocker/important finding.
- Reviewer B: no unresolved blocker/important finding.
- Required deterministic sensors: PASS.
- Required provider/runtime receipts: present and healthy, or task state remains `UNPROVEN`/`BLOCKED`.
- Human/constitutional gates: satisfied.

If convergence is not reached after 3 rounds, do not claim completion or auto-merge/auto-publish. Record unresolved findings in the checkpoint.

## Parallel-plan review

When `executing-plans.md` used parallel fan-out:

- each worker result can receive a scoped fresh review;
- the final reviewer must inspect the integrated diff/artifact after fan-in;
- shared-file/interface conflicts discovered at review time go back to the plan preflight/ruling logic rather than being silently reconciled;
- reviewers do not spawn unbounded nested reviewers/agents.

No majority vote can override a failing sensor, a missing provider receipt, a human gate, or a constitutional rule.
