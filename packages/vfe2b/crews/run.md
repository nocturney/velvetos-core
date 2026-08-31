# Crew: run (Orca + orchestrator desk)

Source pattern: [stablyai/orca](https://github.com/stablyai/orca) — isolate a job, name who owns it, end in one of three states.
Orchestrator overlay (2026-08-31): [andyrewlee/awesome-agent-orchestrators](https://github.com/andyrewlee/awesome-agent-orchestrators) — pulse, independent verify, artifact on disk, bounded loop. See `packages/vfe2b/ORCHESTRATORS.md`.
DeerFlow overlay (2026-08-31): [bytedance/deer-flow](https://github.com/bytedance/deer-flow) — session goal, sub-agent bounds, skill gates, verification receipts. Patterns only. See `packages/vfe2b/DEER-FLOW-PATTERNS.md`.
Do **not** install Orca, DeerFlow, amux, OpenClaw, or a second orchestrator. Cursor is the office.
Packs: `vfops` plus whichever crew this משמרת wraps (`vfconvert`, `vfsales`, `vfcost`, `vfcopy`, `vfcovers`, `vfigos`, `vfprod`, `vfresearch`, `vfbooks`).

## Map

| Outside | אצלנו |
|---|---|
| Orca Run | משמרת |
| Orca Task | כרטיס עבודה (פנייה / בריף / כיסוי / מספר) |
| Orca `worker_done` | טיוטה או פתק מוכן — ואם השליחה היא עבודת HQ, כלי כבר ירה |
| Orca `escalation` | חסר מקור / מדידה / רישיון / ספירת תור |
| Orca `decision_gate` | ₪ לראש צוות בלבד |
| herdr working / blocked / idle | `דופק` |
| kodo independent verify | `אימות` לפני `worker_done` |
| tutti / Crewplane artifact | `ארטיפקט` — נתיב על הדיסק |
| Fusion plan-review-execute | לולאת `vfharness` על צוות קיים אחד |
| NEEDLE state machine | מצב אחד. אין ערוץ צד |
| Taskuary inbox → run | בריף ממיין, ואז צוות אחד |
| fractal / MartinLoop bounds | 2 ניסיונות · checkpoint = קבלה |
| Claudexor quota rotate | מכסת Grok → כלי HQ באותו תור |
| DeerFlow `/goal` | `מטרה` — תנאי סיום אחד; נמחק לפני `worker_done` |
| DeerFlow sub-agents | Cursor Task — רק מקביל/התמחות; לא על ₪/שליחה/רישיון |
| DeerFlow tool receipts | `אימות` מציין receipt (message_id, design URL, sensor) |

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Coordinator | `vfops` | Names the job folder. Picks one existing crew. Emits one outcome. | Invent ₪. Install an ADE |
| Worker | existing crew | Does that crew's Run steps inside the named folder | Touch a second job |
| Verifier | `vfharness` | Names the sensor or field check in `אימות` | LLM-as-judge for ₪ |
| Human | WhatsApp / lead | Answers escalation. Approves ₪. Customer close | — |

## Isolation

One job = one folder. Search Drive / Gmail / slicer **by the job name the user gave**. Do not mix client A files into client B's card.

## Fan-out

Allowed only on `vfcopy` / `vfcovers`: at most **three** variants, then a human picks. Never fan-out a sale ₪, a send, or a license call.

Sub-agent delegation (DeerFlow pattern, Cursor Task): use only when parallel latency, a specialist read, or context isolation has clear net benefit. One interdependent chain stays in the lead session. Never delegate because the task is merely large or multi-step.

## Handoff vs supervise

- **Supervise:** HQ stays on the card until one of the three outcomes. Example: inquiry chain until draft, missing field, or Gmail `reply`.
- **Handoff:** ownership leaves HQ. Example: customer WhatsApp (`050-2517000`), printer on the floor, or lead ₪. After handoff, do not keep «checking if it sent» as if HQ still owns a human channel.

Gmail and Instagram **send via tools** (`constitution/SEND.md`) stay **supervise** until the tool fires or the failover packet is written. That is not a Grok handoff.

«תעביר לוואטסאפ» / «תדפיס» = handoff. «תפקח» / «תחכה» / «תרכז» / «תשלח מג׳ימייל» = supervise.

## Provenance

If Gmail / Calendar / Drive / slicer / snapshot was not actually read, write **חסר** or **אין במקור**. Do not describe the run as closed. Same rule as Orca: do not call external work orchestrated.

## Circuit breaker

Three misses in a row on the same needed fact (queue hours, ₪, license, measurement) → stop. Outcome is `escalation` or `decision_gate`. Do not guess a fourth time. Fresh retry re-reads the source (ralphex). Do not fill the gap.

## Verify before done (kodo + DeerFlow receipts)

`worker_done` is illegal without `אימות` that names:

- a computational sensor that passed (`python3 scripts/check-….py`), or
- a named field that was actually read (subject, file path, calendar block), or
- a **tool receipt** for sends and external artifacts (`Gmail message_id=…`, `Canva design_id=…`, `#נשלח-מ-HQ` / `#ממתין-ל-כלי-IG`), or
- **חסר** — then the state cannot be `worker_done`.

## Session goal (DeerFlow `/goal`)

At run start, write one line `מטרה:` — the completion condition for this job. Examples: «Gmail reply sent in thread X», «Canva+Drive+Gmail failover packet on disk». Sale ₪ is never a goal; use `decision_gate`.

Rules:

1. User or lead overrides the goal on new input — no hidden auto-continuation loops.
2. Two attempts on the same blocker → `escalation` (same circuit breaker as missing facts).
3. `worker_done` requires both `מטרה` satisfied **and** `אימות` with a named receipt or sensor.

## Run

1. Name the job in one Hebrew line. If the user did not name a job, stop and ask — do not open a personal Drive folder.
2. Pick **one** existing crew: morning-brief / research / inquiry / content / books-data. Do not spawn a second coding agent or orchestrator.
3. **Plan preview (OMA embed):** before heavy work, write `planned_steps` (3–8 lines) to `packages/vfharness/state/<task-id>.json` — goal, not a dynamic DAG. See `packages/vfharness/playbooks/oma-patterns.md`.
4. Keep every read and note inside that job name. Write the artifact to a path on disk.
5. Run that crew's steps. Missing required source → do not fill the gap.
6. Verify. Then emit **exactly one** outcome card (below). Mirror `outcome`, `pulse`, and `verification` into the checkpoint. Optional audit copy: `packages/vfharness/templates/run-receipt.md`.
7. **Durable gate:** sale ₪ or missing human field → checkpoint `status: blocked` + `gate` — not `worker_done`. Resume next session from the same file.
8. Then stop.

## Outcome card

```
משמרת: <job name>
צוות: <morning-brief | research | inquiry | content | books-data>
מושב: <lead | studio | growth | ops | production>
מטרה: <one-line completion condition or «אין»>
מצב: worker_done | escalation | decision_gate
דופק: working | blocked | idle
אימות: <sensor | field check | tool receipt | חסר>
ארטיפקט: <path or «אין»>
מה נעשה: <one or two lines, cited>
חסר: <field or «אין»>
הבא: <who — HQ tool send | human WhatsApp | lead ₪ | none>
```

`worker_done` — a reviewable draft exists **and** `אימות` is not חסר. If this job was a Gmail/IG send, the tool already fired or the Canva+Drive+Gmail failover is on disk (`#נשלח-מ-HQ` / `#ממתין-ל-כלי-IG`).
`escalation` — a named field is **חסר**. One WhatsApp ask, drafted, not sent (customer chat stays human).
`decision_gate` — sale ₪ waits for head of desk. Not a «wait for Grok to send» gate.

## Grok quota failover

If Grok Bot weekly quota is empty: keep producing **and sending** via HQ tools (`vfigos/SEND.md`, Gmail `send_message`). Tag `#נשלח-מ-HQ`. If the IG feed itself still needs a publish MCP → also `#ממתין-ל-כלי-IG`. `decision_gate` only for ₪. See `packages/vfharness/playbooks/grok-failover.md` + `constitution/SEND.md`.

## Done when

The card has exactly one `מצב`, plus `דופק` + `אימות` + `ארטיפקט`. No invented ₪ or Insights. No second orchestrator. No claim that the IG feed posted if no publish tool fired.
