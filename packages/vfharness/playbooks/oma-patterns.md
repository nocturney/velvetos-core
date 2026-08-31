# Playbook — Open Multi-Agent patterns (embed only)

Source: [open-multi-agent/open-multi-agent](https://github.com/open-multi-agent/open-multi-agent) — TypeScript orchestration with dynamic DAG, checkpoints, approvals, Run Viewer.

**Verdict:** `embed` on `vfharness` + `vfops`. **Do not** `npm install @open-multi-agent/core`. Cursor is the office. One existing crew per job.

## What we took

| OMA concept | VF HQ |
|---|---|
| Goal → planned steps | `planned_steps[]` on checkpoint before heavy work |
| Coordinator assigns one crew | `crews/run.md` picks morning-brief / inquiry / content / research / books-data |
| Durable approval / suspend | `status: blocked` + `gate` until lead ₪ or human WhatsApp |
| Checkpoint + resume | `packages/vfharness/state/<task-id>.json` |
| Verify before done | `verification` + computational sensors — not LLM consensus |
| Bounded tokens / cost | Grok quota → HQ tools same turn (`grok-failover.md`) |
| Run replay | `templates/run-receipt.md` + outcome card |

## What we skip

- Dynamic DAG of many coding agents
- `@open-multi-agent/core` as a second runtime
- Swarm fan-out on ₪, send, or license
- OTel / Run Viewer npm stack (checkpoint JSON + receipt is enough)

## When

User mentions OMA, open-multi-agent, or «תזמור דינמי».

## Do

1. One job folder. One crew (`python3 scripts/vfmem.py who <job>`).
2. Write `planned_steps` (3–8 lines) in checkpoint **before** step 3 of `crews/run.md`.
3. On missing ₪ / human close: `blocked` + `gate`, not `worker_done`.
4. Close with outcome card fields mirrored in checkpoint (`outcome`, `pulse`, `verification`).
5. Optional: copy `templates/run-receipt.md` to the job artifact path for audit.

## Do not

Install OMA. Spawn parallel coding agents. Invent Insights or ₪. Claim IG posted without publish tool.
