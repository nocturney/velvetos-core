# AGENTS.md — VelvetOS harness (active tenant: Velvet Factory)

PRODUCT: VelvetOS
PROJECT: velvet-factory-headquarters-os
ACTIVE_TENANT: velvet-factory
LANGUAGE: Hebrew product copy; Hebrew+English office docs
STUDIO: 3D-print · Sderot · pickup only · WhatsApp `050-2517000` · IG `@velvets_cloud`
FORMULA: Agent = Model + Harness

This file is the **guide**. When it conflicts with a conversation, this file wins.

VelvetOS is the universal business + autonomous social desk. **Velvet Factory** is the active tenant (`packages/velvetos/ACTIVE.json`). Tenant facts live in `packages/velvetos/tenants/<id>.json`. Do not switch ACTIVE without the lead seat. Example tenants under `_examples/` stay drafts.

BUILD: (no app binary — the catalog is the product)
TEST: python3 scripts/check-all.py
LINT: python3 scripts/check-hq-overlay.py && python3 scripts/check-vf-desk.py && python3 scripts/check-velvetos.py

Read next: `packages/velvetos/KERNEL.md`, `constitution/CONSTITUTION.md`, `.cursor/vf-desk.json`, `packages/vfharness/EMBED.md`.

## RULES

- HQ **sends Gmail and Instagram via tools** (`constitution/SEND.md`). Do not wait for Christian or Grok Bot to press Send/Publish. Grok Bot is optional backup.
- Gmail: `send_message` / `reply` / `forward` are **allowed** for office mail and named inquiry threads. No blast list. No invented ₪. Office 07:00 brief is תצוגה 3 `htmlBody` (`vfbriefux/MAIL.html`).
- Instagram `@velvets_cloud`: send via a connected publish tool; if none, failover **same turn** to Canva + Drive `create_file` + Gmail (`vfigos/SEND.md`). Do not idle. Do not claim the feed posted if it did not.
- Never invent ₪ prices or Insights. Write `X ₪` / «אין ספירה» when the source is missing.
- One pipeline only: פנייה → שיחה → הצעה → הדפסה → איסוף. No national shipping from HQ.
- CTA is WhatsApp `050-2517000` / איסוף שדרות. Not «שלחו DM». Customer WhatsApp stays human (no WhatsApp MCP).
- Do not create a new pack for an idea. Map onto an existing pack the same day. New business vertical → tenant profile on `velvetos`, not a parallel pack tree.
- Do not activate `tenants/_examples/` without the lead seat. Placeholders (`@EXAMPLE_…`, `חסר`) are not live facts.
- Tool failover: if a tool has no access or fails, move its task to the backup tool **immediately**. Never end a job with empty hands. Failover ≠ inventing ₪ / Insights / blocked bodies. Playbook: `constitution/ORCHESTRA.md`.
- Treg is **not relevant**. Do not login, `call`, or route failover through Treg. Live web = `WebSearch` / `WebFetch` / orchestra.
- Drive **creates** office docs/sheets when needed (`create_file`). Search-by-job still applies. No personal/medical/legal folders.
- Grok Bot quota failover: HQ **keeps producing and sending** via HQ tools. Queue tags: `#נשלח-מ-HQ` when a tool sent; `#ממתין-ל-כלי-IG` if the feed itself is still waiting on a publish MCP; `#פרסום-חי-דחוף` + `LIVE-PACKET` for urgent feed work (HQ still sends via tools). Do not sit on `#מוכן-ל-Grok` as the only path. No boost, no auto-DM, no Print from HQ. Playbook: `packages/vfharness/playbooks/grok-failover.md` · `docs/GROK-FAILOVER.md` · `constitution/SEND.md`.
- Do not invent Origin slugs. Keep `unknown` / `origin-slug-unknown`. HQ overlay is the office. Playbook: `docs/ORIGIN-SLUGS.md`.
- Public marketing website / price widget from HQ stays locked. An **internal office command surface** (owner/lead view over packs + `vfops/hq/capabilities.json`) is allowed as a view — not a sixth seat, not a second runtime. ADR: `docs/OFFICE-OS-EMBED-he.md`.
- After every catalog, pack, or rule change, run `python3 scripts/check-all.py`.
- Do not claim success if a computational sensor failed. Retry once, then escalate.
- Close a multi-step task with a checkpoint under `packages/vfharness/state/` so the next session can resume.
- No secrets in git. Do not open personal, medical, or legal Drive folders unless the user names them.
- Warehouse specialists stay off the desk unless the user asks for that `@slug`.

## ANTI-PATTERNS (dated; each traces to an observed failure)

- 2026-08-31 — New business vertical as a parallel pack tree or flipped ACTIVE to an `_examples/` tenant with placeholder handles. Use `packages/velvetos` tenant profiles; keep `velvet-factory` active until lead seat fills real facts. Sensor: `scripts/check-velvetos.py`.
- 2026-08-31 — Invented Origin slug or idled because Origin list was HQ-only. Keep `unknown`. HQ overlay is the office. Playbook: `docs/ORIGIN-SLUGS.md`. Sensor: `scripts/check-origin-slugs.py`.
- 2026-08-31 — Treated «לא אתר מ־HQ» as blocking an **internal** owner console. Public marketing site stays locked; internal command surface is allowed (`docs/OFFICE-OS-EMBED-he.md`). Sensor: `scripts/check-hq-overlay.py` + desk laws.
- 2026-08-30 — Invented sale ₪ or Insights to fill a gap. Sensor: `scripts/check-hq-overlay.py`.
- 2026-08-31 — Installed a second orchestrator (amux, Orca ADE, OpenClaw, Ralph unattended, swarm) instead of embedding onto `vfe2b/crews/run.md`. Sensor: `scripts/check-vfe2b.py`.
- 2026-08-31 — Waited for Christian or Grok Bot to send Gmail/Instagram while tools were available. Sensor: `scripts/check-vf-desk.py` + `constitution/SEND.md`.
- 2026-08-31 — Left office brief unsent during Grok outage (asked owner to click Send). Failover must send the self-brief like Grok (`htmlBody` תצוגה 3). Sensor: `check-vfharness.py` + `grok-outage-tools.md`.
- 2026-08-30 — Instagram / Gmail send from HQ **without a tool / claiming Publish**. Superseded 31.8: HQ **does** send via tools. Still forbid auto-DM, boost, invented publish. Sensor: desk rule + `scripts/check-vf-desk.py`.
- 2026-08-30 — New pack per ChatGPT/Gemini “agent”. Embed in place. Map: `packages/chatgpt-embed-map.json`.
- 2026-08-30 — Inspiration/share links left stale. Weekly pass: `packages/vfresearch/WEEKLY.md` + `LINKS.json`. Sensor: `scripts/check-vfresearch.py`.
- 2026-08-30 — Invented Instagram track names or “#1 trending audio” without Treg/owner source. Playbook: `packages/vfresearch/MUSIC.md`. Sensor: `scripts/check-vfresearch.py`.
- 2026-08-30 — Invented a Perplexity / Cloudflare-blocked body. Write «אין גוף» and skip.
- 2026-08-30 — Stayed idle when a tool was down (waited for owner / skipped all desks). Failover immediately per `constitution/ORCHESTRA.md`. Sensor: `scripts/check-vfresearch.py`.
- 2026-08-30 — Went idle or claimed «אין תוצרים» when Grok Bot weekly quota ran out. Produce **and send via HQ tools**. Do not claim the IG feed posted if no publish tool fired. Sensor: `scripts/check-vfharness.py`. Playbook: `docs/GROK-FAILOVER.md` + `constitution/SEND.md`.
- 2026-08-30 — Second agent runtime (CrewAI, AutoGPT, BabyAGI). Cursor is the office. See `packages/vfe2b/LOCK.md`.
- 2026-08-30 — National shipping or a sixth seat invented beside the five-seat desk.

## SENSORS (run after changes)

| Script | Catches |
|---|---|
| `scripts/check-all.py` | Full suite |
| `scripts/check-hq-overlay.py` | Invented ₪, missing overlays |
| `scripts/check-vf-desk.py` | Desk slugs / packs / HQ-send-via-tools |
| `scripts/check-vfharness.py` | Six layers + Grok-quota failover (HQ sends via tools) |
| `scripts/check-vfe2b.py` | Awesome-agents desk |
| `scripts/check-vfmakers.py` | Maker-skills desk |
| `scripts/check-vfagents.py` | 500-list playbooks |
| `scripts/check-vf-canva.py` | Canva Instagram desk |
| `scripts/check-vfresearch.py` | Weekly inspiration-links + IG music + orchestra failover law |
| `scripts/check-vfmcp.py` | Grok/GPT/Gemini/Perplexity tool-gap map + desk web/image + Canva ready |
| `scripts/check-origin-slugs.py` | Unknown Origin slugs allowed; invented `tmp-…` slugs forbidden |
| `scripts/check-velvetos.py` | VelvetOS kernel + tenants; VF active-tenant compat; examples stay drafts |

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
ASK before: `git push`, Calendar create
ALLOW send: Gmail `send_message` / `reply` / `forward`; Instagram via connected tool or Canva+Drive+Gmail failover (`constitution/SEND.md`)
ALLOW write: Drive `create_file` for office docs (no personal/medical/legal folders)
DENY: auto-DM, boost without lead seat, Treg `call`, `rm -rf`, DROP TABLE, inventing ₪ / Insights / Origin slugs, claiming IG posted without a publish tool

## MEMORY

- Guides (`AGENTS.md`, constitution, pack `SKILL.md`) = what should happen.
- Checkpoints (`packages/vfharness/state/<task-id>.json`) = what happened in this task.
- Office map (`vfgraft`) = how HQ is wired. Office query (`vfmem`) = who handles a job. Neither replaces a task checkpoint.
- Do not rely on chat memory for a rule that must hold every run. Promote it here.

## HARNESS PACK

Layer map and embed path: `packages/vfharness/`. Activate with `@vfharness`.  
VelvetOS kernel + tenants: `packages/velvetos/`. Docs: `docs/VELVETOS.md`.
