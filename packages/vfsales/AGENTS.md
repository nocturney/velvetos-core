# vfsales — local sales/conversion guide

Scope: inquiry, proposal/quote preparation, conversion workflow and customer-facing commercial followup.

- Use `SKILL.md` plus verified offering/price/customer facts only.
- Never invent sale price, discount, quantity, deadline, stock, shipping or customer commitment.
- Price/spend/commitment actions remain protected by their canonical policies; a draft or CRM state never grants authority.
- Customer WhatsApp send remains human-reserved where the active Instance says so.
- Human-visible proposal/message text also follows `constitution/VISIBLE_TEXT.md`.
- Quantity/customer type are job attributes unless current offering authority says otherwise.

Verification: `python3 scripts/check-vfsales.py` when present; offering shape via `python3 scripts/check-vf-offering.py`.
Policy routing reference: `policy_id: project.request.preflight` is router-only; sales drafts/state cannot authorize the destination external effect.
