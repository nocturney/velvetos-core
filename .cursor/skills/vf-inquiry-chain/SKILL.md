---
name: vf-inquiry-chain
description: Run a Velvet Factory inquiry through convert → prod → cost → sales draft. Every customer-visible draft passes the Visible Text Gate before Gmail send or WhatsApp handoff. HQ sends Gmail via tools when ready.
---

# Inquiry chain

Use when there is a new פנייה, Instagram/WhatsApp/Gmail inquiry, or "quote this job".

Authority for anything the customer will read: `constitution/VISIBLE_TEXT.md` + `.cursor/skills/vf-hebrew-copy/SKILL.md`.

## Chain (existing packs only)

1. `vfconvert` + `@email-intelligence-engineer` + `@discovery-coach` — structured brief (size, use, pickup window, license when relevant). First reply follows `vfsales/SLA.md` (no ₪). New client → `office/clients/INTAKE-TEMPLATE.md` then private Client Record (never commit PII to public git).
2. `vfprod` + `@studio-producer` — print feasibility. No national shipping.
3. `vfcost` + `@pricing-analyst` — material line via `python3 scripts/vfcost.py material --grams <slicer> --ils-per-kg <verified>` (missing grams = refuse). Other cost factors from slicer / snapshot / an amount Christian stated. Else `X ₪`. Never a sale price from this pack.
4. `vfsales` + `vfcopy` + `@sales-engineer` + `@content-creator` — quote/customer **draft** (`QUOTE.md` + optional `vf_quote_ladder.py`). One clear next action. No empty price promise. Missing fact stays `X ₪` / `חסר` / question.
5. **Visible Text Gate — mandatory before customer surface:** mode `customer-message` or `sales-proposal`: reader-first → relevant sales/domain tools → `velvet-hebrew-copy` → Humanizer/AI-tells + lint → factual validation. `vfmskill` copywriting/copy-editing is added for persuasive/long-form proposal copy when relevant. Do not use PUBLIC_CURRENT_CTA automatically in a private thread.
6. Only after `visible_text_gate: PASS`: HQ may send a named Gmail reply/quote via tool. Customer WhatsApp close stays human `050-2517000` + Invoice4U; the draft handed to the human must have passed the same text gate.

After each pack step: verify missing fields stay marked חסר. Do not invent ₪ to close the chain. Same sensor-class failure twice → escalate (`packages/vfharness/templates/escalation.md`). Guide: `AGENTS.md`.

## Gmail

- If the user points at a thread: `get_thread`.
- If they ask to find it: `search_threads` with the client name or subject they gave.
- Draft first from the actual thread/card.
- `send_message` / `reply` / `forward` only after customer-visible body is `visible_text_gate: PASS` (no blast, no invented ₪).
- `create_draft` if the thread still needs a human amount; a Gmail draft is not approval to send.

## WhatsApp

- HQ may search/draft only; `send=false` remains locked.
- The customer-visible `text` field must pass `customer-message` Visible Text Gate before it is offered for paste/send by the human.
- Do not “humanize” job IDs, verified price, due date or quoted customer wording.

## Drive

Search by the job or filename the user gives. `create_file` an office doc when the job needs one. Human-facing prose in that doc passes `human-document` Visible Text Gate before it is called final. Do not open personal or medical folders.

## Forbidden

Invented ₪, `visible_text_gate: PASS` by declaration, auto-DM, boost, copying an Israeli brand file, opening a B2B line without the lead seat. Instagram send goes through `vfigos/SEND.md`.
