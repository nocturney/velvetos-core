# AGENTS.md — VelvetOS — Velvet Factory (frontend instance)

PRODUCT: VelvetOS
ROLE: instance (frontend office)
INSTANCE: VelvetOS — Velvet Factory
CORE: vendor/velvetos-core → nocturney/velvetos-core
FORMULA: Agent = Model + Harness (from Core)

This file is the **guide for this business office**. Core laws still win for send / ₪ / Insights.

## RULES (instance)

- Pull packs and modules from **VelvetOS Core** (`vendor/velvetos-core`). Do not duplicate the pack tree.
- Studio facts: `constitution/STUDIO.md` + `instance/velvet-factory.json`.
- HQ sends Gmail and Instagram via tools (`vendor/velvetos-core/constitution/SEND.md`).
- Christian surface: decisions / hard blockers / live publish needing him only. Preflight (`vfgrowth/PREFLIGHT.md`) fail-closes schedule. Never «רמה נמוכה» upward.
- Never invent ₪ or Insights. **PUBLIC_CURRENT_CTA** = Instagram message / איסוף שדרות — not bare «שלחו DM», not WhatsApp phone in public copy. BUSINESS_CONTACT_RECORD WhatsApp `050-2517000` stays in desk only.
- Pipeline: פנייה → שיחה → הצעה → הדפסה → איסוף.
- After catalog edits in core: run core `python3 scripts/check-all.py` from the core checkout / vendor.

## MEMORY (from Core)

Shared owner memory lives in Core, not duplicated in the frontend repo:

- `vendor/velvetos-core/packages/vfops/data/owner-memory.md`
- `vendor/velvetos-core/packages/vfops/data/ARTIFACT-INDEX.md` — how outputs aggregate
- Checkpoints: `vendor/velvetos-core/packages/vfharness/state/`

Morning brief reads block `05a` from owner-memory after `attach-core.sh`.

Revenue loop: `vendor/velvetos-core/.cursor/skills/vf-revenue-loop/SKILL.md` · weekly `WEEKLY-REVENUE-PULSE.md`.

## ATTACH CORE

```bash
./scripts/attach-core.sh
```

**Cloud Agent:** `.cursor/environment.json` runs `install` → attach-core on every boot. No manual step.

## MODULES

Enabled set is in `instance/velvet-factory.json` → `modulesEnabled` (preset `maker-print`).

## COLD-START VISUAL STANDARD — mandatory

For any Velvet Factory content/image/Canva/feed/cover/carousel/Story/Reel visual task, load `vendor/velvetos-core/packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `VISUAL-OS.md` and `VISUAL-DNA.json` before creative work. Canonical Canva asset: `MAHVJjCCKQA`; artifact SHA-256: `707edde3f4d43cffea090bf90ed2418c160db2f8d90d104e4920b44697a014c0`. A fresh conversation must inherit this without relying on chat history. Missing or mismatched binding stops the creative branch as `visual_standard_unavailable`; generic/default creative fallback is forbidden. Real product source media remains Product Truth.

## Publication-prep execution gate

For Velvet Factory requests that mean prepare/treat/edit content for a potential publication, `packages/vfom/PUBLICATION-PREP-EXECUTION.md` is mandatory. This is an execution task: when usable images and an editing capability exist, selection/caption/planning alone is incomplete. Produce at least one real edited visual artifact, preserve Product Truth, run exact-final visual QA, and only then package copy for owner review. If visual execution is unavailable, fail closed as `visual_execution_unavailable`; never claim ready from raw photos plus copy. Resolve public CTA from current authority; never hardcode the business WhatsApp number into public content from memory.

## Brand asset + public CTA lock

`packages/vfom/BRAND-ASSET-LOCK.md` is mandatory for Velvet Factory public creative. Never ask a generative image model to invent/render a Velvet Factory logo, wordmark or logo-like brand lockup. If an exact owner-approved logo asset is not available to the job, use no logo. If it is available, composite that exact asset deterministically after generation/editing. Base generative prompts must explicitly say `NO LOGO · NO WORDMARK · NO PHONE NUMBER · NO WHATSAPP · NO CONTACT BAR`. Public CTA must resolve from `constitution/PUBLIC_CTA.md`; `050-2517000` is forbidden in public creative/caption unless the owner explicitly requests that exact public use in the current task.

