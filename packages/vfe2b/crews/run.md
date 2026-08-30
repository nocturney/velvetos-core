# Crew: run (Orca desk)

Source pattern: [stablyai/orca](https://github.com/stablyai/orca) — isolate a job, name who owns it, end in one of three states.
Do **not** install Orca. Cursor is the office. This crew is an overlay on the five existing crews.
Packs: `vfops` plus whichever crew this משמרת wraps (`vfconvert`, `vfsales`, `vfcost`, `vfcopy`, `vfcovers`, `vfigos`, `vfprod`, `vfresearch`, `vfbooks`).

## Map

| Orca | אצלנו |
|---|---|
| Run | משמרת |
| Task | כרטיס עבודה (פנייה / בריף / כיסוי / מספר) |
| Dispatch | מושב + צוות קיים |
| `worker_done` | טיוטה או פתק מוכן לסקירה |
| `escalation` | חסר מקור / מדידה / רישיון / ספירת תור |
| `decision_gate` | ₪ לראש צוות, או שליחה ל-Grok |

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Coordinator | `vfops` | Names the job folder. Picks one existing crew. Emits one outcome. | Send. Invent ₪. Install an ADE |
| Worker | existing crew | Does that crew's Run steps inside the named folder | Touch a second job |
| Human | WhatsApp / lead / Grok | Answers escalation. Approves ₪. Sends | — |

## Isolation

One job = one folder. Search Drive / Gmail / slicer **by the job name the user gave**. Do not mix client A files into client B's card.

## Fan-out

Allowed only on `vfcopy` / `vfcovers`: at most **three** variants, then a human picks. Never fan-out a sale ₪, a send, or a license call.

## Handoff vs supervise

- **Supervise:** HQ stays on the card until one of the three outcomes. Example: inquiry chain until draft or missing field.
- **Handoff:** ownership leaves HQ. Example: approved Instagram draft → Grok Bot. After handoff, do not keep «checking if it sent» as if HQ still owns it.

«תעביר ל-Grok» / «תשלח» = handoff. «תפקח» / «תחכה» / «תרכז» = supervise.

## Provenance

If Gmail / Calendar / Drive / slicer / snapshot was not actually read, write **חסר** or **אין במקור**. Do not describe the run as closed. Same rule as Orca: do not call external work orchestrated.

## Circuit breaker

Three misses in a row on the same needed fact (queue hours, ₪, license, measurement) → stop. Outcome is `escalation` or `decision_gate`. Do not guess a fourth time.

## Run

1. Name the job in one Hebrew line. If the user did not name a job, stop and ask — do not open a personal Drive folder.
2. Pick **one** existing crew: morning-brief / research / inquiry / content / books-data. Do not spawn a second coding agent.
3. Keep every read and note inside that job name.
4. Run that crew's steps. Missing required source → do not fill the gap.
5. Emit **exactly one** outcome card (below). Then stop.

## Outcome card

```
משמרת: <job name>
צוות: <morning-brief | research | inquiry | content | books-data>
מושב: <lead | studio | growth | ops | production>
מצב: worker_done | escalation | decision_gate
מה נעשה: <one or two lines, cited>
חסר: <field or «אין»>
הבא: <who — human WhatsApp | lead ₪ | Grok send | none>
```

`worker_done` — a reviewable draft or note exists. Send status is not sent from HQ.
`escalation` — a named field is **חסר**. One WhatsApp ask, drafted, not sent.
`decision_gate` — sale ₪ waits for head of desk, or live send waits for Grok.

## Done when

The card has exactly one `מצב`. No invented ₪ or Insights. No Orca binary. No send from HQ.
