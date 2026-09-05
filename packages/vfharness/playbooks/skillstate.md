# Playbook — SKILLSTATE (embed only)

Source: [SKILLSTATE: Scalable Long-Horizon Agent Skills](https://arxiv.org/abs/2608.26263) (Badhe, Tiwari, Chung — arXiv 2608.26263). HTML: https://arxiv.org/html/2608.26263

**Verdict:** `embed` on `vfharness` Memory + Loop. **Do not** install a second agent runtime, LangGraph stack, or SkillExecBench harness. Cursor is the office.

## Idea in one line

Long skills fail when every turn re-reads the growing chat. Keep an explicit mutable **execution state** (Σ). Each step the model sees only:

| Symbol | Meaning | In VF HQ |
|---|---|---|
| \(P\) | Immutable skill / guide | `AGENTS.md` + pack `SKILL.md` + constitution locks |
| \(\Sigma_t\) | Structured execution state | `packages/vfharness/state/<task-id>.json` (+ optional `execution_state`) |
| \(O_t\) | Latest observation only | Last tool/sensor/env result — summarized, not full history |

After a validated state update, **discard** intermediate reasoning. Do not append \(R_t\) into the next prompt.

## What we took

| SKILLSTATE | VF HQ |
|---|---|
| \(A_t = (P, \Sigma_t, O_t)\) | Open guide + checkpoint + latest observation — not the full transcript |
| Schema once per domain | `templates/checkpoint.schema.json` (not a new schema per job) |
| \(\Sigma_{t+1} = \Sigma_t \oplus \Delta\Sigma_t\) | Patch checkpoint fields; null / clear means delete |
| Discard \(R_t\) after validate | Reasoning stays in-step; next turn reads disk state |
| Bounded prompt footprint | Complements `context-thrift.md` (CCR on tool dumps) |
| Validate before apply | Computational sensor or field check — not LLM-as-judge |

## Cycle (same LOOP, clearer substrate)

```
receive O_t
prompt = (P, Σ_t, O_t)     # not chat history
generate (R_t, ΔΣ_t, a_t)
validate ΔΣ_t              # sensor / schema / field check
Σ ← Σ ⊕ ΔΣ_t               # write checkpoint
discard R_t
execute a_t
```

Maps onto `LOOP.md`: plan → do → sensor → patch checkpoint → next step or escalate.

## Optional checkpoint fields

Use when the job needs domain slots beyond the fixed harness keys:

| Field | Role |
|---|---|
| `execution_state` | Object — domain Σ (flags found, missing fields, shelf slots, …) |
| `latest_observation` | Short string — last \(O_t\) only |

Core keys (`completed_steps`, `next_step`, `artifacts`, `unresolved`, `gate`, …) already are Σ for most HQ jobs. Prefer them first; add `execution_state` only when slots would otherwise leak into chat.

## How this differs from siblings

| Playbook | Job |
|---|---|
| `skillstate.md` | Execution substrate = structured state, not chat |
| `context-thrift.md` | Compress large tool outputs (CCR) before they enter the turn |
| `oma-patterns.md` | Plan preview + durable gate + run receipt |
| `PLANNING-FILES.md` | Three markdown files under `state/<task-id>/` for long jobs |

Use together: thrift the dump → patch Σ → next turn opens (P, Σ, O).

## When

User mentions SKILLSTATE, arXiv 2608.26263, «מצב ביצוע», long-horizon skill, or a multi-step job is drowning in chat history.

## Do

1. Open / create checkpoint before heavy work (`EMBED.md` §4).
2. Each turn: read `AGENTS.md` / pack skill (\(P\)), checkpoint (\(\Sigma\)), and only the latest observation (\(O\)).
3. After a successful step: write the state patch; leave reasoning out of the next prompt.
4. On sensor fail: do not apply a bad \(\Delta\Sigma\); retry once or escalate (`templates/escalation.md`).
5. Compaction = rewrite `completed_steps` + `unresolved` from Σ — not a chat summary dump as the only truth.

## Do not

- Install LangGraph / SkillExecBench / a second Cursor runtime for this paper.
- Replay full Gmail threads, sensor stdout, or prior CoT into every turn.
- Invent ₪ / Insights / blocked bodies to “fill” Σ.
- Treat office map (`vfmem` / `vfgraft`) as task Σ — they route; they do not replace the checkpoint.
