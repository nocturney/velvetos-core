---
name: vf-hebrew-copy
description: >-
  Draft or lint Velvet Factory Hebrew Instagram/desk copy in natural Israeli voice.
  Use for כיתוב, caption, reel copy, carousel copy, cover headline, overlay, first-frame hook,
  anti-AI Hebrew QA, velvet-hebrew-copy, needs_input, or when copy sounds like ChatGPT Hebrew.
  Routes into packages/vfcopy.
---

# vf-hebrew-copy

Thin Cursor router → pack skill.

1. Read `packages/vfcopy/skills/velvet-hebrew-copy/SKILL.md` + `PIPELINE.md`.
2. Read `packages/vfcopy/VOICE.md` + `voice/approved/` (never train on `voice/generated/`).
3. For hook/cover/overlay, read `packages/vfcopy/hq/reader-first-he.md` before drafting and include a `NO_TEXT` baseline.
4. Draft per format; missing facts → `needs_input`.
5. Lint/Humanizer pass: `packages/vfcopy/hq/ai-tells-he.md` + `python3 scripts/check-vfcopy.py lint --text '…'` (optional `--rewrite` for style only).
6. For visual microcopy, return `TEXT_WINS` only if the copy adds a specific point/payoff and beats the clean visual; otherwise return `NO_TEXT`.
7. Hand off to `#vfgrowth` / Creative Director / Brand Guardian / `#vfigos` — no publish, no auto-DM, no invented ₪.
