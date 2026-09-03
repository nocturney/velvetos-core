# Agent architecture audit — HQ map

Pattern source: [agent-architecture-audit](https://buildwithclaude.com/skill/agent-architecture-audit) via [buildwithclaude](https://buildwithclaude.com/) (reviewed 2026-09-03).  
Maintained upstream in `affaan-m/ecc`. **Pattern only** — do not install ECC / Claude Code plugins from HQ.

Use when: a seat «נהיה גרוע», tools are skipped, memory leaks old topics, or send claims do not match tool results.  
Do not use for: ordinary code review, inventing ₪ / Insights, or installing a second runtime.

## HQ layer map (12 → ours)

| # | Upstream layer | VelvetOS / VF map | Sensor / check |
|---|---|---|---|
| 1 | System prompt | `AGENTS.md` + desk laws + constitution | `check-vf-desk.py` |
| 2 | Session history | chat turn only — not durable | do not treat as policy |
| 3 | Long-term memory | `vfops/data/owner-memory.md` + `vfmem` | `MEMORY-UPDATE.md` |
| 4 | Distillation | brief / research one-liners re-entering as facts | require source path |
| 5 | Active recall | `vfmem.py who` + `vfgraft/MAP.md` before warehouse | thrift playbook |
| 6 | Tool selection | desk route table + MCP namespaces | `check-vfmcp.py` |
| 7 | Tool execution | real MCP call vs claimed send | `constitution/SEND.md` |
| 8 | Tool interpretation | failover without inventing body | `ORCHESTRA.md` |
| 9 | Answer shaping | Hebrew office copy; CTA WhatsApp / איסוף | desk CTA law |
| 10 | Platform rendering | Gmail `htmlBody` / Canva / Drive | תצוגה 3 brief |
| 11 | Hidden repair loops | second orchestrator / swarm / auto-fix | `vfe2b/LOCK.md` |
| 12 | Persistence | `vfharness/state/*.json` vs stale cache | checkpoint schema |

## Failure modes we already forbid

| Mode | HQ rule |
|---|---|
| Tool discipline failure («שלחתי» בלי כלי) | HQ sends via tools only; no invented Publish |
| Memory pollution (₪ / Insights as facts) | write `X ₪` / «אין ספירה» |
| Hidden second runtime | Cursor is the office; no CrewAI/Orca install |
| Wrapper regression after new pack idea | map onto existing pack same day |

## Diagnostic questions (run in order)

1. Can the seat answer without the required tool and still sound done? → code/sensor gate, not more prompt text.
2. Did old owner-memory or a closed decision re-enter as current policy? → close entry, do not delete (`MEMORY-UPDATE.md`).
3. Is the same fact in `AGENTS.md` AND owner-memory AND checkpoint? → keep one source of truth; cite it.
4. Did a failover invent a blocked body? → write «אין גוף» and continue.
5. Does internal log show send while user-facing claim says feed posted without publish tool? → fix claim; tag `#ממתין-ל-כלי-IG` if needed.

## Fix order (code-first)

1. Enforce with sensors / `check-*.py` — not another paragraph in a prompt.
2. Remove or name any hidden repair path (second agent runtime).
3. Tighten memory admission: user corrections > agent assertions.
4. Keep checkpoints as evidence; do not promote one observation to desk law without lead seat.

## Output

Severity-ranked findings + which HQ layer + file evidence. No invented metrics. Escalate with `packages/vfharness/templates/escalation.md` if the same sensor fails three times.

## Related

- `packages/vfharness/playbooks/full-output-enforcement.md`
- `packages/vfharness/playbooks/context-thrift.md`
- `packages/vfresearch/sources/2026-09-03-buildwithclaude.md`
