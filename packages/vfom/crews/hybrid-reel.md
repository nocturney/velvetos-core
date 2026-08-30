# Crew: hybrid-reel

Source pattern: OpenMontage `pipeline_defs/hybrid.yaml` (source-led footage + support layers; support must not eclipse source truth).
Packs: `vfprod`, `vfcanva`, `vfcovers`, `vfcopy`, `vfigos`.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Anchor | `vfprod` | Name the real bed clip / still. | Generate a fake print |
| Support | `vfcanva` `vfcovers` | Hook text, reel cover, safe zone. | ₪ or Insights on the art |
| Script | `vfcopy` | Source-led vs support-led beats. | «שלחו DM» |
| Gate | `vfigos` | Review the mix. | Publish |
| Human | — | Approves overlay density. | — |

## Run

1. Anchor medium first. Typical VF mix: timelapse → de-support / finish → hero still. Missing a beat → **חסר**, keep the pack partial.
2. Mark every beat `מקור` or `תמיכה`. Support is short Hebrew on-film text or a Canva cover. Not an AI product shot.
3. Overlay rule from hybrid: source stays visually primary. Do not cover the print with a paragraph.
4. CTA on the last beat only: WhatsApp `050-2517000` / איסוף שדרות.
5. Sizes from `packages/vfcanva/FORMATS.json`. Story chrome: keep hook out of the top 250px / bottom 350px.
6. Canva if MCP is connected. If `Canva לא מחובר`, follow `packages/vfcanva/CONNECT.md` or `studio/render.py`. Superdesign only as that fallback.

## Done when

A beat list + cover brief exists. Source files are named or marked חסר. Not sent from HQ.
