---
name: vf-openmontage
description: Plan a Velvet Factory reel from OpenMontage production patterns — reference reel, timelapse clip cards, hybrid floor+Canva, scene gate, self-review. Review only; Grok sends.
---

# OpenMontage crews (`vfom`)

Use when the user pastes a Reel they like, asks to cut a timelapse, or wants a reel plan with scene approval.

## Packs and specialists

- `vfom` + `@visual-storyteller` + `@instagram-curator`
- `vfgrowth` + `@content-creator`
- `vfcanva` for stills / reel cover (read `vf-canva-instagram`)
- `vfigos` — **review and schedule only**

## Pick one crew

| Ask | File |
|---|---|
| ריל שאוהבים / «כמו הסרטון הזה» | `packages/vfom/crews/reference-plan.md` |
| טיימלאפס ארוך → כמה רילס | `packages/vfom/crews/clip-factory.md` |
| גלם + כיתוב + כריכה | `packages/vfom/crews/hybrid-reel.md` |
| אחרי הדפסה תקינה / print.done | `packages/vfprod/PRINT-DONE.md` → then `hybrid-reel.md` / `clip-factory.md` |
| אשר סצנות לפני שיבוץ | `packages/vfom/crews/scene-gate.md` |
| בדוק לפני מסירה | `packages/vfom/crews/self-review.md` |

Read the crew. Fill its template. Do not run `make setup` from OpenMontage.

## Laws

- Floor proof first. No file → **חסר**. Stop.
- CTA: WhatsApp `050-2517000` / איסוף שדרות. Not «שלחו DM».
- No invented ₪, Insights, or bed footage.
- No Veo/Kling/Remotion from HQ unless the lead seat opened that spend.
- Hand the approved draft to `vfigos`. HQ sends via tools (`constitution/SEND.md`); Grok is optional backup.

## Velvet Factory Visual Standard Gate — mandatory (`VF_VISUAL_STANDARD_GATE`)

Before any Velvet Factory concept, image selection/edit, Canva operation, cover, carousel, Story still, Reel cover, feed/grid plan, render or publish handoff, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`. Verify Canva asset `MAHVL7PKpvE` and artifact SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897`. Record a PASS binding in the job/manifest/preflight before creative work continues.

This gate is **fail-closed**: if the standard is unavailable, mismatched or unverified, stop the creative branch as `visual_standard_unavailable`; never fall back to a generic 3D-print, stock, template, Canva-default or model-default aesthetic. Real source product media remains Product Truth and outranks style; preserve product identity/geometry/material/color and apply the approved reference to composition, surroundings, light, crop, typography and finish.
