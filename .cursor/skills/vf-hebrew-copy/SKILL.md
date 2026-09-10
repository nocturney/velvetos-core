---
name: vf-hebrew-copy
description: >-
  Route any Hebrew AI-authored human-visible prose/microcopy through Velvet Factory's canonical
  copy quality layer. Use for owner-facing briefs/reports, customer Gmail/WhatsApp/IG replies,
  quotes/proposals, captions, Reel/Story/Carousel copy, cover headline, overlay, first-frame text,
  documents, UI microcopy, anti-AI Hebrew QA, needs_input, or when text sounds like ChatGPT Hebrew.
  Routes into packages/vfcopy and constitution/VISIBLE_TEXT.md.
---

# vf-hebrew-copy

Thin Cursor router → `packages/vfcopy`; no second writer/runtime.

1. Read `constitution/VISIBLE_TEXT.md`.
2. Read `packages/vfcopy/skills/velvet-hebrew-copy/SKILL.md` + `PIPELINE.md`.
3. Read task/domain truth first. Do not rewrite literal source quotes, IDs, hashes, URLs, code, raw logs or machine payloads.
4. Read `packages/vfcopy/hq/reader-first-he.md` before drafting human-visible prose.
5. Select the correct mode: `public-social`, `visual-microcopy`, `customer-message`, `sales-proposal`, `owner-brief`, `human-document`, `ui-microcopy`, or `desk`.
6. Add only the relevant channel/domain tools: public social → VOICE/PUBLIC_CTA/vfgrowth; customer/sales → vfconvert/vfsales/vfcost/vlicense as applicable; visual → Creative Director/Brand Guardian + `NO_TEXT`; marketing/long-form → vfmskill copywriting/copy-editing when applicable.
7. Draft. Missing facts → `needs_input` / `חסר`, never creative completion.
8. Humanizer pass: `packages/vfcopy/hq/ai-tells-he.md` + `python3 scripts/check-vfcopy.py lint --text '…'` (optional `--rewrite` for style only).
9. Prefer the surface-aware executable for the actual candidate: `python3 scripts/vf_visible_text.py --surface <surface> ...`; public caption lint remains compatible with `check-vfcopy.py lint`.
10. Run factual/constraint validation after style. Humanizer must not soften or alter a real blocker/number/status.
11. Return `visible_text_gate: PASS` only if the relevant stages actually ran; otherwise `UNPROVEN`/`FAIL`.
12. For visual microcopy / cover headline: 3–5 candidates + `NO_TEXT`; `TEXT_WINS` only if copy adds a specific point/payoff and beats the clean visual.
13. Hand off to the relevant next surface. This skill does not publish/send, does not auto-DM, and does not invent ₪.

Explicit owner wording is a strong preference: validate it but do not rewrite its point back into generic marketing copy.
