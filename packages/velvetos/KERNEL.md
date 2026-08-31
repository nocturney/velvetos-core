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

## מטאפורה

| Core | Instance |
|---|---|
| Backend / OS kernel | Frontend / business office |
| Shared capabilities | Identity, channels, tool binds, enabled modules |

## כלל ברזל

1. הריפו הזה הוא **Core** — לא משרד עסק יחיד.
2. משרד VF החי עובר ל־`instances/velvet-factory/` → ריפו `velvetos-velvet-factory`.
3. מודולים תמיד בליבה; preset ≠ סביבה חיה.
4. לא ₪ / Insights מומצאים; לא אוטו־DM / בוסט.
