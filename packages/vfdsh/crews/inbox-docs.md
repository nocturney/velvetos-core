# Crew: inbox documents

Source patterns: MinerU, dsh-attachment-formats, dsh-pdf, DSH-Office, dsh-cowork (bounded read).
Packs: `vfbooks`, `vfconvert`, `vfsales`.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Mail clerk | `vfbooks` | Read Gmail / a named PDF. Extract supplier, date, invoice id. | Send, reply, forward |
| Inquiry clerk | `vfconvert` | Pull material / qty / when / finish if written. | Guess the gap |
| Quote clerk | `vfsales` | Note requested items for a later draft. | Write a sale ₪ |
| Human | — | Confirms the extract. Sale shekels after head of desk. | — |

## Run

1. Open only the thread, label, or file the user named. Inbox: `nocturney@gmail.com`, read only.
2. Copy figures that are printed on the document. If a shekel amount is missing, write **אין במקור** — not `X ₪` unless the desk already uses that placeholder for a sale price.
3. Flag PII: do not paste full ID numbers or medical lines into the pack.
4. Missing job facts → one WhatsApp question for a human. Not a bot reply.
5. Stop. No Invoice4U replacement. No AutoQuote.

## Done when

A short extract exists with sources (subject + date, or filename). Unstated numbers stay blank.
