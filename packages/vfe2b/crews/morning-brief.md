# Crew: morning brief

Source patterns: Lindy, Cal.ai, Heymoon, CrewAI, AutoGen (human-in-the-loop).
Orchestrator overlay: Taskuary - triage inbox into **one** supervised run; then HQ sends the canonical 09:00 Asia/Jerusalem brief.
Packs: `vfbriefux`, `vfseason`, `vfops`, `vfbooks`, `vfigos`, `vfcopy`.
Human-visible text authority: `constitution/VISIBLE_TEXT.md`, mode `owner-brief`.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Brief sender | `vfops` | Send the 09:00 Asia/Jerusalem Morning Green brief through the canonical owner Gmail workflow only after `visible_text_gate: PASS`. | Read inbox for brief content. Blast list. Invent ₪. Customer WhatsApp. Plaintext-only brief |
| Calendar clerk | `vfseason` | Read `Asia/Jerusalem`. Mirror every live Publisher schedule to the dedicated Google Calendar `אינסטגרם` (`CALENDAR-OPS.md`). Publisher remains source of truth; do not ask Christian for slots. | Create events outside the standing IG grid unless asked |
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
7. Only after `visible_text_gate: PASS`, project the same factual brief through `packages/vfbriefux/build_morning_green.py`, render `packages/vfbriefux/MORNING-GREEN.html` with `render_morning_green.py`, and send through the canonical owner Gmail request/workflow. Decorative imagery is CID-bound; future Instagram cards use the read-only Cloudflare Publisher snapshot and `מתוזמן` requires live Publisher `scheduled_at` evidence plus a fresh cron heartbeat. `MAIL.html` + `render_mail.py` remain legacy/other-owner-surface renderers, not the canonical Morning Brief route. Fail closed on production Gmail failure; do not send plaintext or a lower-quality plugin fallback.

## Done when

A one-page brief exists, its human-authored/AI-authored prose has a real `visible_text_gate: PASS`, `אימות` cites Calendar and/or verified vfops sources (not inbox reads), and the brief mail was sent **or** the Drive failover file exists. A transport success does not substitute for the text gate.
