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

If constitution overlays exist (`packages/vfops/hq/BRIEF-SLOTS.md` or `packages/vfops/BRIEF.md`), fill those slots. Block `05` is always `packages/vfops/data/research.md` (empty state is exactly `אין חדש במשרד`). **Block `05a`:** read the latest block from `packages/vfops/data/owner-memory.md` (retro / owner prefs) — one short paragraph in the brief, not the full file. Do not invent a sixth seat. Live mail uses `packages/vfbriefux/MAIL.md` — not plaintext.

## HTML draft (optional)

Production mail: `render_mail.py` + `MAIL.html` (תצוגה 3). Reference/wireframe: `packages/vfbriefux/hq/brief-email.html` (effective-html). Pipeline/slot companion diagrams: `render_mail.py --diagram pipeline|slots` + `vfbriefux/hq/DIAGRAM-MAKER.md` (not inside Gmail body). During Grok failover, HQ sends `htmlBody` to `nocturney@gmail.com` per `MAIL.md`.

## Harness

Read `AGENTS.md` if this is a new session. Do not invent queue hours to pass the brief. If Calendar read fails twice, escalate with `packages/vfharness/templates/escalation.md`. If Gmail **send** fails twice, use Drive failover for the brief body. Long brief work: optional checkpoint in `packages/vfharness/state/`.
