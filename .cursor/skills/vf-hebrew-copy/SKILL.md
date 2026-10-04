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

Policy registry reference: `policy_id: visible_text.finalization`.

Thin Cursor router → `packages/vfcopy`; no second writer/runtime.

1. Read `constitution/VISIBLE_TEXT.md`.
2. Read `packages/vfcopy/skills/velvet-hebrew-copy/SKILL.md` + `PIPELINE.md`.
3. Read task/domain truth first. Do not rewrite literal source quotes, IDs, hashes, URLs, code, raw logs or machine payloads.
4. Select the risk tier first: `DRAFT_INTERNAL`, `FINAL_INTERNAL`, `EXTERNAL_COMMITMENT`, or `PUBLIC_PUBLISH`. The surface constrains which tiers are legal.
5. Select the mode: `public-social`, `visual-microcopy`, `customer-message`, `sales-proposal`, `owner-brief`, `human-document`, `ui-microcopy`, or `desk`.
6. `DRAFT_INTERNAL`: truth/basic-safety only. Do not force reader-first/Humanizer/copy ceremony onto working internal text.
7. Routine `FINAL_INTERNAL`: truth + final clarity/surface QA. Add `reader-first-he.md` + `packages/vfcopy/hq/ai-tells-he.md` + copy/Humanizer only when sensitive or long (`>800` chars).
8. `EXTERNAL_COMMITMENT`: verified facts + reader-first + surface QA + exact body/hash binding; load only relevant customer/sales/cost/license truth.
9. `PUBLIC_PUBLISH`: full public chain — VOICE/PUBLIC_CTA/vfgrowth as applicable, vfcopy/Humanizer, exact text identity; visual copy also requires `NO_TEXT` comparison and Creative Director/Brand Guardian.
10. Draft/repair. Missing facts → `needs_input` / `חסר`, never creative completion.
11. Run `python3 scripts/vf_visible_text.py --surface <surface> --tier <tier> ...` on the actual candidate. Omit `--tier` only when the safe surface default is intended.
12. Return `visible_text_gate: PASS` only if the evidence required by that tier actually ran; otherwise `UNPROVEN`/`FAIL`.
13. Hand off to the relevant next surface. This skill does not publish/send, does not auto-DM, and does not invent ₪.

Explicit owner wording is a strong preference: validate it but do not rewrite its point back into generic marketing copy.
