# VelvetOS

**VelvetOS Core** (this repo) = באקאנד — חוקים, מודולים, פקים, סנסורים.  
**VelvetOS — \<Business\>** = פרונט — משרד עסק אחד ששואב מהליבה.

| | |
|---|---|
| Core | `packages/velvetos/CORE.json` |
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

## CLI

```bash
python3 scripts/velvetos.py core
python3 scripts/velvetos.py modules
python3 scripts/velvetos.py instances
python3 scripts/check-velvetos.py
```
