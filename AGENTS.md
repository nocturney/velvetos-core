# AGENTS.md — Velvet Factory HQ harness

PROJECT: velvet-factory-headquarters-os
LANGUAGE: Hebrew product copy; Hebrew+English office docs
STUDIO: 3D-print · Sderot · pickup only · WhatsApp `050-2517000` · IG `@velvets_cloud`
FORMULA: Agent = Model + Harness

This file is the **guide**. When it conflicts with a conversation, this file wins.

BUILD: (no app binary — the catalog is the product)
TEST: python3 scripts/check-all.py
LINT: python3 scripts/check-hq-overlay.py && python3 scripts/check-vf-desk.py

Read next: `constitution/CONSTITUTION.md`, `.cursor/vf-desk.json`, `packages/vfharness/EMBED.md`.

## RULES

- Never send Instagram, Gmail, WhatsApp, or DMs from this HQ. Live send stays on Grok Bot.
- Never call Gmail `send_message`, `reply`, or `forward`. Draft only if the user explicitly asks.
- Never invent ₪ prices or Insights. Write `X ₪` / «אין ספירה» when the source is missing.
- One pipeline only: פנייה → שיחה → הצעה → הדפסה → איסוף. No national shipping from HQ.
- CTA is WhatsApp `050-2517000` / איסוף שדרות. Not «שלחו DM».
- Do not create a new pack for an idea. Map onto an existing pack the same day.
- After every catalog, pack, or rule change, run `python3 scripts/check-all.py`.
- Do not claim success if a computational sensor failed. Retry once, then escalate.
- Close a multi-step task with a checkpoint under `packages/vfharness/state/` so the next session can resume.
- No secrets in git. Do not open personal, medical, or legal Drive folders unless the user names them.
- Warehouse specialists stay off the desk unless the user asks for that `@slug`.

## ANTI-PATTERNS (dated; each traces to an observed failure)

- 2026-08-30 — Invented sale ₪ or Insights to fill a gap. Sensor: `scripts/check-hq-overlay.py`.
- 2026-08-30 — Instagram / Gmail send from HQ. Sensor: desk rule + `scripts/check-vf-desk.py`.
- 2026-08-30 — New pack per ChatGPT/Gemini “agent”. Embed in place. Map: `packages/chatgpt-embed-map.json`.
- 2026-08-30 — Inspiration/share links left stale. Weekly pass: `packages/vfresearch/WEEKLY.md` + `LINKS.json`. Sensor: `scripts/check-vfresearch.py`.
- 2026-08-30 — Invented Instagram track names or “#1 trending audio” without Treg/owner source. Playbook: `packages/vfresearch/MUSIC.md`. Sensor: `scripts/check-vfresearch.py`.
- 2026-08-30 — Invented a Perplexity / Cloudflare-blocked body. Write «אין גוף» and skip.
- 2026-08-30 — Second agent runtime (CrewAI, AutoGPT, BabyAGI). Cursor is the office. See `packages/vfe2b/LOCK.md`.
- 2026-08-30 — National shipping or a sixth seat invented beside the five-seat desk.

## SENSORS (run after changes)

| Script | Catches |
|---|---|
| `scripts/check-all.py` | Full suite |
| `scripts/check-hq-overlay.py` | Invented ₪, missing overlays |
| `scripts/check-vf-desk.py` | Desk slugs / packs / no-send |
| `scripts/check-vfharness.py` | Six layers present and wired |
| `scripts/check-vfe2b.py` | Awesome-agents desk |
| `scripts/check-vfmakers.py` | Maker-skills desk |
| `scripts/check-vfagents.py` | 500-list playbooks |
| `scripts/check-vf-canva.py` | Canva Instagram desk |
| `scripts/check-vfresearch.py` | Weekly inspiration-links registry (`LINKS.json` + `WEEKLY.md`) + IG music playbook (`MUSIC.md`) |

Computational sensors first. Do not add an LLM-as-judge for ILS, send, or pack names.

## LOOP BOUNDS

- Max retries per step: 2 (then escalate)
- Max tool-call thrash: stop after the same sensor fails three times
- Stopping condition: return the best artifact + unresolved issues. Do not hide a failed sensor behind fluent Hebrew.
- Escalation packet: `packages/vfharness/templates/escalation.md`

## PERMISSIONS (harness, not the model)

ALLOW read: `packages/**`, `constitution/**`, `docs/**`, `.cursor/**`, Gmail search/get, Calendar list, Drive search-by-job
ALLOW write: `packages/**`, `constitution/**`, `docs/**`, `AGENTS.md`, `CHANGELOG.md`
ALLOW execute: `python3 scripts/check-*.py`
ASK before: `git push`, Calendar create, Gmail `create_draft`, Treg `call` (say catalog price first)
DENY: Gmail `send_message` / `reply` / `forward`, Instagram send / boost / auto-DM, `rm -rf`, DROP TABLE, inventing ₪

## MEMORY

- Guides (`AGENTS.md`, constitution, pack `SKILL.md`) = what should happen.
- Checkpoints (`packages/vfharness/state/<task-id>.json`) = what happened in this task.
- Office map (`vfgraft`) = how HQ is wired. Office query (`vfmem`) = who handles a job. Neither replaces a task checkpoint.
- Do not rely on chat memory for a rule that must hold every run. Promote it here.

## HARNESS PACK

Layer map and embed path: `packages/vfharness/`. Activate with `@vfharness`.
