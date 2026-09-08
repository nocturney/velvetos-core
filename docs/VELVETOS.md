# VelvetOS

**VelvetOS Core** (this repo) = באקאנד — חוקים, מודולים, פקים, סנסורים, חוזי אירועים (**Kernel**).  
**VelvetOS — \<Business\>** = פרונט — משרד עסק אחד ששואב מהליבה (**Office**).  
**Edge** = אופציונלי (host/רצפה) — לא שם הריפו. ADR: `packages/velvetos/ADR-THREE-LAYERS.md` · `LAYERS.md`.

| | |
|---|---|
| Core | `packages/velvetos/CORE.json` |
| Layers | `packages/velvetos/LAYERS.md` |
| Events | `packages/velvetos/schema/events.catalog.json` |
| Modules | `packages/velvetos/modules/` (תמיד טעונים) |
| Presets | תבניות לפרונט (יופי multi-IG, חוות דעת…) |
| VF frontend scaffold | `instances/velvet-factory/` |
| Publish | `scripts/publish-instance.sh` |
| Repos | `packages/velvetos/REPOS.md` |

## למה באקאנד/פרונט

הליבה לא משרתת HTTP — היא ליבת Cursor-OS משותפת. כל עסק מקבל workspace משלו (פרונט) עם זהות, ערוצים, ו־`modulesEnabled`, ומצמיד את הליבה ב־`vendor/velvetos-core`.

## VF

1. צור ריפו ריק `nocturney/velvetos-velvet-factory` ב־GitHub  
2. `PUSH=1 ./scripts/publish-instance.sh velvet-factory nocturney/velvetos-velvet-factory`  
3. במופע: `./scripts/attach-core.sh`  
4. פתח את ריפו המופע ב־Cursor לניהול היומי  

Failover מנהל משרד (כש־ChatGPT אינו זמין): [`docs/FAILOVER.md`](FAILOVER.md). 

## CLI

```bash
python3 scripts/velvetos.py core
python3 scripts/velvetos.py modules
python3 scripts/velvetos.py instances
python3 scripts/check-velvetos.py
```
