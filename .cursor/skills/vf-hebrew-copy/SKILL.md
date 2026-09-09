---
name: vf-hebrew-copy
description: >-
  Draft or lint Velvet Factory Hebrew Instagram/desk copy in natural Israeli voice.
  Use for כיתוב, caption, reel copy, carousel copy, anti-AI Hebrew QA, velvet-hebrew-copy,
  needs_input, or when copy sounds like ChatGPT Hebrew. Routes into packages/vfcopy.
---

# vf-hebrew-copy

Thin Cursor router → pack skill.

1. Read `packages/vfcopy/skills/velvet-hebrew-copy/SKILL.md` + `PIPELINE.md`.
2. Read `packages/vfcopy/VOICE.md` + `voice/approved/` (never train on `voice/generated/`).
3. Draft per format; missing facts → `needs_input`.
4. Lint: `python3 scripts/check-vfcopy.py lint --text '…'` (optional `--rewrite` for style only).
5. Hand off to `#vfgrowth` / `#vfigos` — no publish, no auto-DM, no invented ₪.
