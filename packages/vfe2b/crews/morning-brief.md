# Crew: morning brief

Source patterns: Lindy, Cal.ai, Heymoon, CrewAI, AutoGen (human-in-the-loop).
Packs: `vfbriefux`, `vfseason`, `vfops`, `vfbooks`, `vfigos`.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Inbox clerk | `vfops` | Read Gmail. Flag bills and job threads. | Send, reply, forward |
| Calendar clerk | `vfseason` | Read `Asia/Jerusalem`. Note clashes. | Create events unless asked |
| Brief editor | `vfbriefux` | Shape the morning list. | Invent metrics |
| Floor lead | `vfops` | Mark print-floor blockers from mail. | Assign printers (Grok / human) |
| Human | — | Picks the shift. | — |

## Run

1. List unread / last-24h mail that looks like: invoice, inquiry, printer, Instagram review. Quote subject + date. No body dump of secrets.
2. List today's calendar blocks.
3. Cross-check `vfseason` marks (holidays, drops). If the pack tree is empty, say so.
4. Output three buckets in Hebrew: **היום** / **אדם** / **אחר כך**.
5. Stop. Do not post. Do not send.

## Done when

A one-page brief exists and a human has seen the **אדם** bucket.
