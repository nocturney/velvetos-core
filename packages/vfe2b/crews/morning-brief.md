# Crew: morning brief

Source patterns: Lindy, Cal.ai, Heymoon, CrewAI, AutoGen (human-in-the-loop).
Orchestrator overlay: Taskuary — triage inbox into **one** supervised run; then HQ sends the 07:00 brief.
Packs: `vfbriefux`, `vfseason`, `vfops`, `vfbooks`, `vfigos`.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Inbox clerk | `vfops` | Read Gmail. Flag bills and job threads. Send the 07:00 brief via `send_message` when the page is ready. | Blast list. Invent ₪. Customer WhatsApp |
| Calendar clerk | `vfseason` | Read `Asia/Jerusalem`. Note clashes. | Create events unless asked |
| Brief editor | `vfbriefux` | Shape the morning list. | Invent metrics |
| Floor lead | `vfops` | Mark print-floor blockers from mail. | Assign printers from HQ |
| Human | — | Picks the next משמרת from the **אדם** bucket. | — |

## Run

1. List unread / last-24h mail that looks like: invoice, inquiry, printer, Instagram review. Quote subject + date. No body dump of secrets.
2. List today's calendar blocks.
3. Cross-check `vfseason` marks (holidays, drops). If the pack tree is empty, say so.
4. Output three buckets in Hebrew: **היום** / **אדם** / **אחר כך**. Name **one** job the human can hand to `@vfe2b run` (Taskuary). Do not drain the whole inbox unattended.
5. Write the brief to `packages/vfops/BRIEF.md` (or the packet the brief UX names).
6. HQ **sends** the 07:00 brief to `nocturney@gmail.com` via Gmail `send_message` (`constitution/SEND.md`). Failover: Drive `create_file` the same body + continue. Do not wait for Grok.

## Done when

A one-page brief exists on disk, `אימות` cites Calendar and/or Gmail subjects actually read, and the brief mail was sent **or** the Drive failover file exists.
