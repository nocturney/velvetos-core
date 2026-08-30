---
name: vf-morning-brief
description: Build the Velvet Factory morning brief from Calendar, Gmail reads, and vfops — never invent queue hours or send mail.
---

# Morning brief

Use when the user asks for בריף בוקר, morning brief, what is open today, or the lead-seat start.

## Packs and specialists

- Pack: `vfops` (+ `vfbriefux` for layout only)
- Mention: `@studio-operations` (and `@meeting-notes-specialist` if there is a transcript)
- Layout research: `@ux-architect` + Mobbin **only** when the user asks to change the brief format

## Tools

1. **Google Calendar** — `list_calendars` then `list_events` on `nocturney@gmail.com` for **today** in `Asia/Jerusalem`. Pickup windows and named holds only.
2. **Gmail** — `search_threads` with `in:inbox newer_than:1d` (and a tighter query if the user names a client). **Read only.** Do not send, reply, or forward.
3. **Drive** — skip unless the user names a job file or SKU.

## Output (Hebrew)

- 🔴 late / blocked
- 🟡 waiting for approval or payment
- 🟢 ready to print
- 🖨️ queue hours — only from slicer / snapshot. If missing: «אין ספירה»

One pipeline reminder: פנייה → שיחה → הצעה → הדפסה → איסוף. Pickup in Sderot only.

If constitution overlays exist (`packages/vfops/hq/BRIEF-SLOTS.md` or `packages/vfops/BRIEF.md`), fill those slots. Do not invent a sixth seat.
