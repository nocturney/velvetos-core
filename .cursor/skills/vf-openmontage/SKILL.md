---
name: vf-openmontage
---

# OpenMontage crews (`vfom`)

## VF_PUBLICATION_ROUTE_V1 - current publication scope

Run `scripts/vf_publication_evidence.py --phase production` before production and `--phase delivery` before review delivery, with the exact manifest/content ID. A file-path or static wiring pass is not creative approval. Preserve source pixels, purposeful editorial richness and independent source/reference/copy/brand/final review evidence.

Use when the user pastes a Reel they like, asks to cut a timelapse, or wants a reel plan with scene approval.

## Packs and specialists

- `vfom` + `@visual-storyteller` + `@instagram-curator`
- `vfgrowth` + `@content-creator`
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

## VF_VISUAL_STANDARD_GATE

Before public creative execution, load `packages/vfom/OWNER-APPROVED-GRID-STANDARD-2026-09-14.md`, `packages/vfom/VISUAL-OS.md` and `packages/vfom/VISUAL-DNA.json`. Bind SHA-256 `df41281b44e2c1ac99a1cb0c9f084ec926c30774f61468fc8988f59c5a136897` and require `visualStandard.gate=PASS`. Missing/mismatched authority is `visual_standard_unavailable`; generic visual fallback is forbidden.
