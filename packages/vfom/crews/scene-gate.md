# Crew: scene-gate

Source pattern: OpenMontage Backlot contact sheet + `human_approval_default: true` on idea / script / scene_plan / assets / publish.
Packs: `vfigos`, `vfgrowth`, `vfcovers`.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Board | `vfgrowth` | One row per scene. | Mark complete without approval |
| Cover | `vfcovers` | Poster / first-frame note. | Invent a still |
| Review | `vfigos` | Hold the booked slot. | Send |
| Human | — | Approves or sends back. | — |

## Run

1. Build a contact sheet. No Backlot process, no `python -m backlot`.

```
סצנה:
ביט:
מקור / חסר:
טיפול (מקור / תמיכה):
טקסט על הפריים:
אישור אדם: מחכה / כן / לא
```

2. A gated stage is **not** «מוכן ל-Grok» until every row is `כן` or explicitly dropped.
3. Publish-shaped work stays a `vfigos` review. HQ does not run a publish-director.
4. If the user asked for a paid insert, write **אין במקור** for cost unless the lead seat named a figure. Do not convert dollars to ₪.

## Done when

The sheet is filled and a human signed the scenes that remain. Slot `#משובץ` does not move.
