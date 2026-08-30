# Crew: clip-factory

Source pattern: OpenMontage `pipeline_defs/clip-factory.yaml` (long source → ranked shorts, hook in 2–3s, clean in/out, platform mix).
Packs: `vfprod`, `vfgrowth`, `vfcopy`, `vfigos`.

## Roles

| Role | Pack | Does | Does not |
|---|---|---|---|
| Floor | `vfprod` | Find the named timelapse / bed clip. | Invent hours or a scene |
| Cutter | `vfgrowth` | Rank 3–5 self-contained cuts. | Upload |
| Copy | `vfcopy` | On-film text + caption stub. | Price on the frame |
| Scheduler | `vfigos` | Review the ranked list. | Send / boost |
| Human | — | Approves which cuts move. | — |

## Run

1. Drive `search_files` by the job / SKU / filename the user gave. No file → **חסר**. Stop.
2. Do not open personal, medical, or legal folders unless named.
3. Rank **3–5** candidates. Each card:

```
קליפ:
מקור: <filename the user named>
כניסה / יציאה:
הוק (2–3 שניות):
למה זה עומד לבד:
פורמט: ig_reel_cover 1080×1920
טקסט על הפריים:
כיתוב (טיוטה):
חסר:
```

4. Reject a cut that starts mid-sentence or needs private-client context.
5. Hand the approved cards to `vfcopy` then `vfigos`. HQ does not ffmpeg-export unless the lead seat later opens a render stack.

## Done when

A ranked list exists from a real source file. Missing proof stays **חסר**. Not sent from HQ.
