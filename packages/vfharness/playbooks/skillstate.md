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
| `component_state` | Operational SoC enum: `Idle` · `Processing` · `Degraded` · `Syncing` · `Blocked` (ADR-THREE-LAYERS). Distinct from task `status`. |
| `execution_state` | Object — domain Σ (flags found, missing fields, shelf slots, …) |
| `latest_observation` | Short string — last \(O_t\) only |
| `events` | Optional log of catalog events (`velvetos/schema/events.catalog.json`) |

Core keys (`completed_steps`, `next_step`, `artifacts`, `unresolved`, `gate`, …) already are Σ for most HQ jobs. Prefer them first; add `execution_state` only when slots would otherwise leak into chat.

When a tool fails mid-job: set `component_state` to `Degraded`, emit `tool.failover` / `sensor.degraded`, follow `playbooks/degraded-mode.md`.

## How this differs from siblings

| Playbook | Job |
|---|---|
| `skillstate.md` | Execution substrate = structured state, not chat |
| `context-thrift.md` | Compress large tool outputs (CCR) + **phase-boundary** table (when to compact) |
| `oma-patterns.md` | Plan preview + durable gate + run receipt |
| `PLANNING-FILES.md` | Three markdown files under `state/<task-id>/` for long jobs |

Use together: thrift the dump → patch Σ at phase boundaries → next turn opens (P, Σ, O). Never compact mid-implementation.

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

## Phase A — read-only task-state audit (SWC-CODEX-001)

`scripts/vf_task_state.py` reads the existing checkpoints and the unchanged
`templates/checkpoint.schema.json`. It produces JSON; it does not execute a
task, rewrite state, send, publish, or change the live brief. This is a reader
on the existing harness, not a second agent runtime. Brief integration is a
separate phase requiring coordination approval.

```bash
# Audit all state/**/*.json, including historical records.
python3 scripts/vf_task_state.py
# Audit one checkpoint; paths are relative to the checkout root.
python3 scripts/vf_task_state.py packages/vfharness/state/swc-codex-001.json
# Require local artifact integrity evidence for every selected task.
python3 scripts/vf_task_state.py --require-verified packages/vfharness/state/swc-codex-001.json
# Behavioral sensor, also discovered automatically by check-all.py.
python3 scripts/check-vf-task-state.py
```

Use `--root /path/to/checkout` to select a different local workspace. Relative
artifact paths resolve against that root, not against the checkpoint directory.
An absent local artifact means absent **in this checkout**; it says nothing
about another machine. A partial checkout can therefore report local absences.

### Evidence and report meaning

Escalation histories written by `vf_graceful_escalation.py` as `ladder-*.json`
arrays are reported separately in `event_logs`, with source fingerprints and
structural errors. They are not checkpoints and never establish completion,
including a successful `downgrade_scope`. Malformed events fail explicitly;
other arrays remain invalid checkpoint inputs. `--require-verified` also fails
when event logs are selected, since log structure cannot verify a task.

The report includes `observed_at`, schema/source SHA-256 fingerprints,
`reported_status`, `last_updated`, `schema_errors`, `state_errors`, per-artifact
observations, and `completion`. Dates and status remain as reported; aliases
such as `worker_done` are not silently converted to `done`.

| Observation | Meaning |
|---|---|
| `missing` | Referenced local file is absent in the selected checkout |
| `present_unverified` | File/directory exists, but no matching file-integrity evidence is available |
| `digest_verified` | Current regular-file bytes match the expected SHA-256 in this checkpoint |
| `digest_mismatch` | File changed or the recorded digest is incorrect |
| `unverified_external` | URI, not accessed or verified by this reader |
| `unverified_reference` | Opaque ID (for example a Canva ID), command, or pattern; not resolved, executed, or expanded |
| `unverified_other_environment` | Absolute/Windows/home/escaping path outside the selected checkout; not opened |
| `invalid_reference` / `invalid_evidence` / `unreadable` | Explicit input or local inspection failure |

| `completion` | Meaning |
|---|---|
| `invalid` | Schema mismatch, duplicate task ID, or inconsistent state/evidence metadata |
| `blocked` | Blocked/escalated status or a pending gate; never a completed task |
| `not_done` | Valid record still in progress |
| `unverified` | Reported done, but local artifact evidence is incomplete |
| `local_artifacts_verified` | Valid done, no gate/unresolved work, nonempty verification note and artifact list, every artifact digest verified |

**This checks local file integrity only.** A matching digest does not establish
design quality, reviewer approval, business completion, email delivery, or an
Instagram publication. Tool receipts and live checks stay with their existing
owners. Historical `verification` prose alone cannot establish artifact integrity.
The checkpoint writer is responsible for recording a digest only after checking
the intended final file; the reader does not create or refresh expected evidence.

Optional digest evidence uses the already extensible `execution_state` object;
the shared checkpoint schema is unchanged. Keys must exactly match entries in
`artifacts`. Each value is an object with `sha256` containing the actual 64-hex
digest. Record it from the reviewed file, for example with `sha256sum out/result.txt`.
After any file change, the old evidence no longer verifies the bytes.

Illustrative shape (replace the placeholder with the actual digest):

```json
{
  "execution_state": {
    "artifact_evidence": {
      "out/result.txt": {"sha256": "<actual SHA-256 from the reviewed file>"}
    }
  }
}
```

### Failures, compatibility and tests

- Exit `0`: selected records are structurally consistent with no definite local
  artifact errors. **This alone does not mean completion**; inspect `completion`.
- Exit `1`: invalid record/state/event log, definite artifact error, or `--require-verified`
  was requested and any task lacks verified local artifacts.
- Exit `2`: reader/schema configuration problem or no checkpoint files selected.

The stdlib schema interpreter covers the vocabulary used by the current schema:
type, required, properties, boolean additionalProperties, items, enum, minLength,
and maxItems, plus schema metadata. Unknown keywords or unsupported dialects
stop the audit explicitly. This is not a general-purpose JSON Schema engine.
Duplicate JSON keys and non-JSON constants are rejected.

The behavioral sensor uses temporary fixtures and validates the owned
`swc-codex-001.json`. Its success means the reader passed its tests, not that
every historical checkpoint conforms. Run the full audit separately and report
legacy violations and environmental absences without modifying others' records
or weakening the schema. Phase A does not make old audit violations a new
blanket check-all gate; that migration requires a separately scoped task.
