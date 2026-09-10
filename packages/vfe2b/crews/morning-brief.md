# Crew: morning brief

Source patterns: Lindy, Cal.ai, Heymoon, CrewAI, AutoGen (human-in-the-loop).
Orchestrator overlay: Taskuary — triage inbox into **one** supervised run; then HQ sends the 07:00 brief.
Packs: `vfbriefux`, `vfseason`, `vfops`, `vfbooks`, `vfigos`, `vfcopy`.
Human-visible text authority: `constitution/VISIBLE_TEXT.md`, mode `owner-brief`.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Brief sender | `vfops` | Send the 07:00 brief via `send_message` + `htmlBody` תצוגה 3 only after `visible_text_gate: PASS`. | Read inbox for brief content. Blast list. Invent ₪. Customer WhatsApp. Plaintext-only brief |
| Calendar clerk | `vfseason` | Read `Asia/Jerusalem`. Put every planned IG post on Google Calendar (`CALENDAR-OPS.md`). Do not ask Christian for slots. | Create events outside the standing IG grid unless asked |
| Brief editor | `vfbriefux` + `vfcopy` | Shape the morning list, then run owner-brief reader-first + Humanizer on AI-authored prose. | Invent metrics. Rewrite literal IDs/hashes/source values. Apply Instagram CTA/voice to operations |
| Floor lead | `vfops` | Mark print-floor blockers from verified sources. | Assign printers from HQ |
| Human | — | Picks the next משמרת from the **אדם** bucket. | — |

## Run

1. **Skip inbox read for the brief** — incoming mail is not a work source right now. `search_threads` stays on the desk for named threads / `vfconvert` / `vfbooks`; do not use it to populate slots 01–07.
2. List today's calendar blocks.
3. Cross-check `vfseason` marks (holidays, drops). If the pack tree is empty, say so.
4. Fill brief slots from verified sources only: run `python3 scripts/vfops_loop.py brief --write` (pulls vfgrowth / vfcopy / vfsku scan / vfbooks / vfprod print-done / vfcost / research). Also pipeline board, orchestration 06:15, calendar. Output three buckets in Hebrew: **היום** / **אדם** / **אחר כך**. Name **one** job the human can hand to `@vfe2b run` (Taskuary).
   - Slot 02 = books integrity + material cost — not MakerWorld names.
   - Slot 03 = shelf + Sun/Wed scan + print.done cards.
   - Slot 07 = captions + PREFLIGHT path. Brief approval does **not** publish the feed.
5. Write the factual draft to `packages/vfops/BRIEF.md` (or the packet the brief UX names). Block `05` is `packages/vfops/data/research.md`.
6. **Visible Text Gate:** preserve literal source rows/IDs/numbers; route every AI-authored heading, summary, explanation or recommendation through `reader-first-he.md` → `.cursor/skills/vf-hebrew-copy/SKILL.md` in `owner-brief` mode → `ai-tells-he.md` + lint → factual validation. Public Instagram voice/CTA is not applied to this surface. No material rewrite after PASS without re-running the gate.
7. Only after `visible_text_gate: PASS`, render `packages/vfbriefux/MAIL.html` + `render_mail.py` and HQ **sends** the 07:00 brief to `nocturney@gmail.com` via Gmail `send_message` + `htmlBody` תצוגה 3. Failover: Drive `create_file` the same gated body + continue. Do not wait for Grok. Do not send plaintext as the live brief.

## Done when

A one-page brief exists, its human-authored/AI-authored prose has a real `visible_text_gate: PASS`, `אימות` cites Calendar and/or verified vfops sources (not inbox reads), and the brief mail was sent **or** the Drive failover file exists. A transport success does not substitute for the text gate.
