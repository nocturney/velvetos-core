# Crew: inquiry to order

Source patterns: Claygent, Kadoa, Docket AI. AskToSell is questions-only — never a closer.
Orchestrator overlay: 5dive / humanlayer / paperclip — escalate to a human; approval gate on ₪.
Packs: `vfconvert`, `vfsales`, `vfcost`, `vfcopy`, `vfprod`.
Human-visible text authority: `constitution/VISIBLE_TEXT.md`.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Intake | `vfconvert` | Extract material, qty, when, finish. | Guess missing fields |
| Researcher | `vfsales` | Public facts about the requester if useful. | Invent a customer |
| Cost clerk | `vfcost` | Unit notes from existing cost pack only. | Sale ₪ |
| Copy | `vfcopy` | Draft + run `customer-message`/`sales-proposal` Visible Text Gate. | Send WhatsApp; fake PASS |
| Mail | Gmail | `reply` on a **named** inquiry thread only after `visible_text_gate: PASS`. | Blast. Auto-DM |
| Floor | `vfprod` | Note bed / job constraints if already known. | Auto-assign a printer |
| Human | WhatsApp | Asks the customer. Approves ₪; sends gated draft. | — |

## Run

0. **Dedup** (Huginn pattern): before reply or a new block-02 row, run `vfconvert/hq/DEDUP.md`. Duplicate → `worker_done` «כפילות — לא נשלח שוב».
1. Quote the four fields. Any blank → one customer question, drafted, not sent (customer WhatsApp stays human `050-2517000`).
2. Do not scrape a person into existence. If the only source is the thread, say so.
3. If a slice / STL / reprint is mentioned, hand to `vfprod` / `vfsku` as a note, not a price.
4. Sale shekels: stop. Head of desk only (`decision_gate`).
5. Before any customer-readable body leaves the office, run: real thread/card → reader-first → relevant `vfconvert`/`vfsales`/`vfcost`/`vlicense` → `.cursor/skills/vf-hebrew-copy/SKILL.md` → `ai-tells-he.md` + lint → factual validation. Private thread does not inherit public IG CTA automatically.
6. If the inquiry is a **named Gmail thread**, all required facts are present and `visible_text_gate: PASS`: HQ `reply` via tool (`constitution/SEND.md`). WhatsApp remains human-send, but the text handed to the human must have the same PASS.

## Done when

The path is `inquiry → missing-fields or human-price or gated HQ Gmail reply / gated WhatsApp draft`. Never `inquiry → quote ₪`. Never a Telegram/CRM bot. Never `PASS` by declaration.
