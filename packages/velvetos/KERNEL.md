# VelvetOS Core — ליבה (backend)

**VelvetOS Core** = באקאנד המערכת: חוקים, 5 מושבים, פקים, מודולים, סנסורים, presets.  
כל עסק = **פרונט** נפרד (`VelvetOS — <Business Name>`) ששואב מהליבה את מה שרלוונטי.

## ארכיטקטורה

```
VelvetOS Core (this repo)              Instance repos (frontends)
─────────────────────────              ─────────────────────────
modules/*  (always loaded)      →      VelvetOS — Velvet Factory
packs vf*                       →      VelvetOS — <Nails/Tattoos>
laws · harness · sensors        →      VelvetOS — <Psychiatrist>
presets (blueprints)
instances/*/ (scaffold to publish)
```

שלוש שכבות SoC (לא runtime שני): **Edge** (אופציונלי/host) · **Kernel** (הריפו הזה) · **Office/HQ** (desk + frontend).  
פירוט: `LAYERS.md` · ADR: `ADR-THREE-LAYERS.md` · אירועים: `schema/events.catalog.json`.

## מטאפורה

| Core | Instance |
|---|---|
| Backend / OS kernel (Kernel layer) | Frontend / business office (Office layer) |
| Shared capabilities + event contracts | Identity, channels, tool binds, enabled modules |

**לא:** Core ≠ nervous-system runtime / IoT daemon. Edge = host/רצפה כשקיים מקור אמיתי.

## כלל ברזל

1. הריפו הזה הוא **Core** — לא משרד עסק יחיד.
2. משרד VF החי עובר ל־`instances/velvet-factory/` → ריפו `velvetos-velvet-factory`.
3. מודולים תמיד בליבה; preset ≠ סביבה חיה.
4. לא ₪ / Insights מומצאים; לא אוטו־DM / בוסט.
