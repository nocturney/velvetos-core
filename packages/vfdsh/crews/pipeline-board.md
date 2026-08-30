# Crew: pipeline board

Source patterns: dsh_workflow, DSH Taskboard, dsh-kanban, dsh-verification, dsh-tech-lead, dsh-ambiguity-handling, dsh-negative-ledger.
Packs: `vfops`, `vfprod`, `vfconvert`.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Board | `vfops` | Place each open job on פנייה / שיחה / הצעה / הדפסה / איסוף. | Skip a column |
| Gate | `vfconvert` | Ask when material / qty / when / finish is missing. | Guess |
| Floor | `vfprod` | Move to הדפסה only with a named bed or a human mark. | Assign printers from HQ |
| Reviewer | `vfops` | Accept «בוצע» only with evidence (mail subject, file, calendar). | Auto-complete |
| Human | — | Confirms the shift. | — |

## Run

1. List open items from mail (read), calendar (`Asia/Jerusalem`), and named pack notes. No invented queue hours.
2. Ambiguous job → options, then wait. Do not pick a material or a date.
3. Failed path (bad bed, missing file) stays on a negative line so the next run does not repeat it.
4. Agent may move a card to **סקירה** only. Human (or Grok on the floor) marks done.
5. Stop. No cron that runs the board overnight.

## Done when

A five-column list exists. Every «בוצע» has a citation. Pickup stays Sderot.
