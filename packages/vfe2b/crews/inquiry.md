# Crew: inquiry to order

Source patterns: Claygent, Kadoa, Docket AI. AskToSell is questions-only — never a closer.
Orchestrator overlay: 5dive / humanlayer / paperclip — escalate to a human; approval gate on ₪.
Packs: `vfconvert`, `vfsales`, `vfcost`, `vfcopy`, `vfprod`.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Intake | `vfconvert` | Extract material, qty, when, finish. | Guess missing fields |
| Researcher | `vfsales` | Public facts about the requester if useful. | Invent a customer |
| Cost clerk | `vfcost` | Unit notes from existing cost pack only. | Sale ₪ |
| Copy | `vfcopy` | Draft the WhatsApp ask-back. | Send WhatsApp |
| Mail | Gmail | `reply` on a **named** inquiry thread when the draft is ready (no invented ₪). | Blast. Auto-DM |
| Floor | `vfprod` | Note bed / job constraints if already known. | Auto-assign a printer |
| Human | WhatsApp | Asks the customer. Approves ₪. | — |

## Run

1. Quote the four fields. Any blank → one WhatsApp question, drafted, not sent (customer chat stays human `050-2517000`).
2. Do not scrape a person into existence. If the only source is the thread, say so.
3. If a slice / STL / reprint is mentioned, hand to `vfprod` / `vfsku` as a note, not a price.
4. Sale shekels: stop. Head of desk only (`decision_gate`).
5. If the inquiry is a **named Gmail thread** and the draft is ready (no missing ₪): HQ `reply` via tool (`constitution/SEND.md`).

## Done when

The path is `inquiry → missing-fields or human-price or HQ Gmail reply`. Never `inquiry → quote ₪`. Never a Telegram/CRM bot.
