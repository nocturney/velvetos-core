# Crew: hybrid-reel

Source pattern: OpenMontage `pipeline_defs/hybrid.yaml` (source-led footage + support layers; support must not eclipse source truth).

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Anchor | `vfprod` | Name the real bed clip / still. | Generate a fake print |
| Script | `vfcopy` | Source-led vs support-led beats. | WhatsApp public CTA · «שלחו DM» / auto-DM |
| Gate | `vfigos` | Review the mix. | Publish |
| Human | — | Approves overlay density. | — |

## Trigger from Print-Done

When production hands a filled `packages/vfprod/PRINT-DONE.md` card (event `print.done`):

1. Require `mediaPath` / Drive id on the card. Missing → **חסר**. Stop.
2. Prefer material / minutes / grams from the card only — never invent specs for on-film text.
3. After beat list + caption + cover brief exist, emit `content.draft_ready` (preflight still required before schedule).
4. Do not publish from this crew.

## Run

1. Anchor medium first. Typical VF mix: timelapse → de-support / finish → hero still. Missing a beat → **חסר**, keep the pack partial.
3. Overlay rule from hybrid: source stays visually primary. Do not cover the print with a paragraph.
4. CTA on the last beat only: Instagram message (`PUBLIC_CURRENT_CTA`) · איסוף שדרות. Not WhatsApp / `050-2517000` on public frames.

## Done when

A beat list + cover brief exists. Source files are named or marked חסר. Not sent from HQ.
