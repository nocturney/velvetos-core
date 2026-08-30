# Crew: floor vision

Source patterns: Modlens, DSH Vision Toolkit, PictureReader, pbr-render, phone-lens (input only).
Packs: `vfprod`, `vfcovers`, `vlicense`.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Eye | `vfprod` | Read a named photo / slice screenshot. Quote what is visible. | Invent a bed or a floor scene |
| Model clerk | `vfprod` | Note STL/GLB facts from the file or slicer log. | Promise a printer |
| License | `vlicense` | Gate a reprint if the file is a named IP / customer STL. | Skip the gate |
| Cover scout | `vfcovers` | Mark whether the photo is usable as proof (real, not staged). | Draw a fake studio |
| Human | — | Decides print / hold / pickup. | — |

## Run

1. Require a path, Drive hit, or WhatsApp screenshot the user named. If none — stop: «חסר צילום».
2. List visible facts only: color, layer lines, warp, bed adhesion, text on the part. Missing → «לא נראה בתמונה».
3. If a model file is named, write format + any slicer hours that already exist. No guessed queue hours.
4. Cross `vlicense` before a reprint of a customer or brand file.
5. Output Hebrew: **נראה** / **לא נראה** / **אדם**. Do not assign a printer.

## Done when

A human has the visible-facts list and a yes/no on print. No live camera daemon.
