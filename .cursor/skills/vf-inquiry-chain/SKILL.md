---
name: vf-inquiry-chain
description: Run a Velvet Factory inquiry through convert → prod → cost → sales draft. HQ sends the Gmail via tools when the draft is ready (constitution/SEND.md).
---

# Inquiry chain

Use when there is a new פנייה, Instagram/WhatsApp/Gmail inquiry, or "quote this job".

## Chain (existing packs only)

1. `vfconvert` + `@email-intelligence-engineer` + `@discovery-coach` — structured brief (size, use, pickup window, license).
2. `vfprod` + `@studio-producer` — print feasibility. No national shipping.
3. `vfcost` + `@pricing-analyst` — cost factors from slicer / snapshot / an amount Christian stated. Else `X ₪`.
4. `vfsales` + `vfcopy` + `@sales-engineer` + `@content-creator` — quote **draft**. One CTA. Spoken Hebrew. No empty price promise. Optional frameworks: `vfmskill` `offers` / `sales-enablement` / `customer-research`. ₪ still only after the lead seat.
5. HQ **sends the Gmail quote via tool** (no invented ₪). Customer WhatsApp close stays human `050-2517000` + Invoice4U.

After each pack step: verify missing fields stay marked חסר. Do not invent ₪ to close the chain. Same sensor-class failure twice → escalate (`packages/vfharness/templates/escalation.md`). Guide: `AGENTS.md`.

## Gmail

- If the user points at a thread: `get_thread`.
- If they ask to find it: `search_threads` with the client name or subject they gave.
- `send_message` / `reply` / `forward` when the draft is ready (no blast, no invented ₪).
- `create_draft` first if the thread still needs a human amount; then send.

## Drive

Search by the job or filename the user gives. **`create_file`** an office doc when the job needs one. Do not open personal or medical folders.

## Forbidden

Invented ₪, auto-DM, boost, copying an Israeli brand file, opening B2B logos/QR/napkins without the lead seat. Instagram send goes through `vfigos/SEND.md`.
