---
name: vf-morning-brief
description: Build the Velvet Factory morning brief from Calendar and vfops — not from Gmail inbox reads. Send the 07:00 brief via Gmail when ready. Never invent queue hours.
---

# Morning brief

Use when the user asks for בריף בוקר, morning brief, what is open today, or the lead-seat start.

## Packs and specialists

- Pack: `vfops` (+ `vfbriefux` for layout only)
- Mention: `@studio-operations` (and `@meeting-notes-specialist` if there is a transcript)
- Layout research: `@ux-architect` + Mobbin **only** when the user asks to change the brief format

## Tools

1. **Google Calendar** — `list_calendars` then `list_events` on `nocturney@gmail.com` for **today** in `Asia/Jerusalem`. Pickup windows and named holds only.
2. **Gmail — send only for the brief** — render `vfbriefux/MAIL.html` and `send_message` the office brief (`htmlBody` תצוגה 3) to `nocturney@gmail.com`. Do not `reply` / `forward` / send to a customer.
3. **Gmail — inbox read: skip for the brief** — `search_threads` / `in:inbox newer_than:1d` stay available on the desk for `vfconvert`, `vfbooks`, and named threads. **Do not call them to populate the 07:00 brief** — incoming mail is not a work source right now. If the user names a thread, read that thread only.
4. **Drive** — skip unless the user names a job file or SKU.

## Output (Hebrew)

- 🔴 late / blocked
- 🟡 waiting for approval or payment
- 🟢 ready to print
- 🖨️ queue hours — only from slicer / snapshot. If missing: «אין ספירה»

One pipeline reminder: פנייה → שיחה → הצעה → הדפסה → איסוף. Pickup in Sderot only.  
Tone: agency-grade (`constitution/STUDIO.md` רף סוכנות). Christian reads and sits calmly — no half-finished slots, no «מתי לפרסם?». Slots 06/07 never invent bad news or «רמה נמוכה»; agency gaps stay internal **פער** lines.

Before filling slots, run `python3 scripts/vfops_loop.py brief --write` so תפעול gets growth/copy/sku/office blocks without pasting from random docs.

Slot **01** may include one-click yes/no/defer from `packages/vfops/hq/GATES.json` (`vfops_loop.py gate`). A click is a human gate — not WhatsApp send, not Print, not a sale ₪.

Slot **02** pulls `packages/vfbooks/data/orders.json` + Invoice4U snapshot from **disk**. Do not scrape `in:inbox` to fill the 07:00 brief. Empty files = «אין ספירה».

Slot **03** also pastes `python3 scripts/vfprod.py brief` (fleet + maintenance) and `python3 scripts/vfsku.py scan`.

If constitution overlays exist (`packages/vfops/hq/BRIEF-SLOTS.md` or `packages/vfops/BRIEF.md`), fill those slots. Block `02` may paste `python3 scripts/vfcost.py brief` (material cost only — no invented sale ₪). Block `05` is **real CLI runs from last 24h** (`vfops_loop.py` → `packages/vfops/data/cli-runs.jsonl`) or exactly `אין חדש במשרד` — no catalog paste from `research.md`. Unused daily/`on-content` packs become a **פער** line. `research.md` stays the 06:15 orchestra note only. **Block `05a`:** read the latest block from `packages/vfops/data/owner-memory.md` (retro / owner prefs) — one short paragraph in the brief, not the full file. Do not invent a sixth seat. Live mail uses `packages/vfbriefux/MAIL.md` — not plaintext.

## HTML draft (optional)

Production mail: `render_mail.py` + `MAIL.html` (תצוגה 3). Reference/wireframe: `packages/vfbriefux/hq/brief-email.html` (effective-html). Pipeline/slot companion diagrams: `render_mail.py --diagram pipeline|slots` + `vfbriefux/hq/DIAGRAM-MAKER.md` (not inside Gmail body). During Grok failover, HQ sends `htmlBody` to `nocturney@gmail.com` per `MAIL.md`.

## Harness

Read `AGENTS.md` if this is a new session. Do not invent queue hours to pass the brief. If Calendar read fails twice, escalate with `packages/vfharness/templates/escalation.md`. If Gmail **send** fails twice, use Drive failover for the brief body. Long brief work: optional checkpoint in `packages/vfharness/state/`.
