# Crew: morning brief

Source patterns: Lindy, Cal.ai, Heymoon, CrewAI, AutoGen (human-in-the-loop).
Orchestrator overlay: Taskuary — triage inbox into **one** supervised run; then HQ sends the 07:00 brief.
Packs: `vfbriefux`, `vfseason`, `vfops`, `vfbooks`, `vfigos`.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Brief sender | `vfops` | Send the 07:00 brief via `send_message` + `htmlBody` תצוגה 3 (`vfbriefux/MAIL.html`) when the page is ready. | Read inbox for brief content. Blast list. Invent ₪. Customer WhatsApp. Plaintext-only brief |
| Calendar clerk | `vfseason` | Read `Asia/Jerusalem`. Note clashes. | Create events unless asked |
| Brief editor | `vfbriefux` | Shape the morning list. | Invent metrics |
| Floor lead | `vfops` | Mark print-floor blockers from mail. | Assign printers from HQ |
| Human | — | Picks the next משמרת from the **אדם** bucket. | — |

## Run

1. **Skip inbox read for the brief** — incoming mail is not a work source right now. `search_threads` stays on the desk for named threads / `vfconvert` / `vfbooks`; do not use it to populate slots 01–07.
2. List today's calendar blocks.
3. Cross-check `vfseason` marks (holidays, drops). If the pack tree is empty, say so.
4. Fill brief slots from verified sources only: pipeline board, `data/research.md`, orchestration 06:15, calendar. Output three buckets in Hebrew: **היום** / **אדם** / **אחר כך**. Name **one** job the human can hand to `@vfe2b run` (Taskuary).
5. Write the brief to `packages/vfops/BRIEF.md` (or the packet the brief UX names). Block `05` is `packages/vfops/data/research.md`.
6. HQ **sends** the 07:00 brief to `nocturney@gmail.com` via Gmail `send_message` + `htmlBody` תצוגה 3 (`packages/vfbriefux/MAIL.html` + `render_mail.py`). Failover: Drive `create_file` the same body + continue. Do not wait for Grok. Do not send plaintext as the live brief.

## Done when

A one-page brief exists on disk, `אימות` cites Calendar and/or verified vfops sources (not inbox reads), and the brief mail was sent **or** the Drive failover file exists.
