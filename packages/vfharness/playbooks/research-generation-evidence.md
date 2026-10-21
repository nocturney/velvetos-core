# Parallel research and generation evidence — reusable harness pattern

Source of architectural inspiration (not copied runtime): [sapientinc/praxist at 5b50658](https://github.com/sapientinc/praxist/tree/5b50658b219d292fe471cfae99a9ec0797429ed7). **Fair Source license; no code copied or executed.** Apply only to bounded research/optimization work that has an executable or independently inspectable metric. Preserve `packages/vfharness/LOOP.md`, Office state and the existing single authority.

## Reusable experiment contract

1. Declare `objective`, metric and direction, baseline artifact/hash, immutable test set, safety constraints, budget, stop condition, owners and rollback plan.
2. Partition *genuinely independent* hypotheses to isolated worktrees/output roots and dynamically allocate subscription-only Claude CLI peers across authorized hosts; do not invent a hard worker-count cap.
3. Require each peer to return exact inputs, code/source hashes, evaluator version, measured result, failed attempts, resource/cost observation, and a reproducible artifact. Raw agent self-report cannot prove success.
4. Score with the **same** blinded/synthetic fixtures and independent QA, including negative controls. Do not optimize the metric by violating a safety constraint or overfitting shared evaluation data.
5. Close a generation with a durable evidence ledger: keep baseline, qualified improvement, explicitly failed but informative tests, and rationale for the next round. Stop if improvement is unproven, cost/rights uncertain, or resources unavailable.
6. Compare incumbent, complete alternative and optional hybrid fairly when Praxist-like research engines are evaluated; keep candidate in Phase 2 registry and `agent-runtime` queue until the same contract is satisfied.

## Compatibility gates

- Codex-native subscription mode is **not** available as a workaround: user's Codex quota must not power agents.
- Claude Code as the visible orchestrator UI is **not** evidence that Praxist peer execution can consume the existing Claude subscription. Prove that first with documented supported CLI behavior and zero paid API calls.
- Verify Fair Source business/revenue/output obligations before any binary install or derivative code.
- Never add a second scheduler, production writer, credential authority or memory database from these patterns.

**Proof:** Task artifact and independent fixture scores, original baseline, peer isolation, exact resource log, rollback/readback. Source intake: `docs/implementation/office-v2/phase2/owner-creative-agent-tools-intake-2026-10-21.md`.
