---
name: vf-inquiry-chain
description: Run a Velvet Factory inquiry through convert → prod → cost → sales draft. Gmail is read-only; HQ does not send.
---

# Inquiry chain

Use when there is a new פנייה, Instagram/WhatsApp/Gmail inquiry, or "quote this job".

## Chain (existing packs only)

1. `vfconvert` + `@email-intelligence-engineer` + `@discovery-coach` — structured brief (size, use, pickup window, license).
2. `vfprod` + `@studio-producer` — print feasibility. No national shipping.
3. `vfcost` + `@pricing-analyst` — cost factors from slicer / snapshot / an amount Christian stated. Else `X ₪`.
4. `vfsales` + `vfcopy` + `@sales-engineer` + `@content-creator` — quote **draft**. One CTA. Spoken Hebrew. No empty price promise. Optional frameworks: `vfmskill` `offers` / `sales-enablement` / `customer-research`. ₪ still only after the lead seat.
5. Stop. A human sends on WhatsApp + Invoice4U.

## Gmail

- If the user points at a thread: `get_thread`.
- If they ask to find it: `search_threads` with the client name or subject they gave.
- Never `send_message`, `reply`, or `forward`.
- `create_draft` only when the user explicitly asks for a Gmail draft (WhatsApp is the default close).

## Drive

Search by the job or filename the user gives. Do not open personal or medical folders.

## Forbidden

Invented ₪, Instagram send, auto-DM, boost, copying an Israeli brand file, opening B2B logos/QR/napkins without the lead seat.
