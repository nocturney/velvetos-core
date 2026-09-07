# Crew: books and numbers

Source patterns: Julius, Vanna.AI, Wren, Powerdrill, TalktoData, AskYourDatabase.
Orchestrator overlay: kodo verify — the cited file must be opened before the figure is written.
Packs: `vfbooks`, `vfcost`, `vfinsights`.

Integrity playbook: `packages/vfbooks/INTEGRITY.md`. CLI: `python3 scripts/vfbooks.py brief` (slot 02).

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Ledger | `vfbooks` | Receivables / bills that are already written. | Invent balances |
| Cost | `vfcost` | Unit economics already in the pack. | Invent sale ₪ |
| Insights | `vfinsights` | Performance reads from cited sources. | Invent metrics |
| Verifier | same pack | Confirms the path exists and the number is on the page. | Fill a gap |
| Human | — | Confirms any number that will leave the room. | — |

## Run

1. Name the question.
2. Cite the exact file or line you will read. If Origin trees are empty, say **העץ לא הועתק** and stop or use only HQ text.
3. Open that file. Answer only with cited numbers. Missing → **אין במקור**.
4. Cross jobs vs Invoice4U marks per `INTEGRITY.md`. Missing invoice on אושר/ייצור/מוכן/נאסף → internal brief line only. Do not email the customer.
5. Invoice product stays Invoice4U. Do not switch the studio to another invoicer from this pack. `decision_gate` = sale ₪ for lead only.

## Done when

Every figure has a citation that was actually opened, or is marked missing. `אימות` names the file.
