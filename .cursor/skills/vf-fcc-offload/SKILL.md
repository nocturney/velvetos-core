---
name: vf-fcc-offload
description: Map Free Claude Code onto Velvet Factory HQ — Cursor thrift now, local Mac offload only after the lead seat. Never install fcc-server on a Cloud Agent.
---

# FCC offload

Use when the user asks about [free-claude-code](https://github.com/Alishahryar1/free-claude-code), FCC, Claude Code חינם, saving Cursor/Claude limits, or `@vffcc`.

## Packs and specialists

- Pack: `vffcc` (map) + `vfops` / `vfbiz` (decision)
- Mention: `@chief-of-staff` if the lead seat must approve a local install
- Do **not** mention warehouse coding agents

## What to do

1. Read `packages/vffcc/LOCK.md` and `docs/FCC-FIT.md`.
2. Default path: `packages/vffcc/playbooks/cursor-thrift.md` + `route.md`.
3. Local install playbook only after the lead seat says yes.
4. Never run `curl …/install.sh`, `fcc-server`, or write `*_API_KEY` into the repo.

## Output (Hebrew)

- האם זה חוסך את Cursor Cloud: לא
- מה כן חוסך עכשיו: שלושת כללי ה־thrift הרלוונטיים לשאלה
- אם רוצים מק: NIM → Groq → Gemini → OpenRouter, מפתחות ב־`~/.fcc/`
- CTA אם צריך אדם: וואטסאפ `050-2517000` — לא «שלחו DM»
