# velvetos — איך מטמיעים (Core)

## 1. זהות

- הריפו הזה = **VelvetOS Core** (backend)
- פרונט VF = `instances/velvet-factory/` → לפרסם ל־`nocturney/velvetos-velvet-factory`
- ראו `REPOS.md`

## 2. מודולים

הכל ב־`modules/`. מופע בוחר `modulesEnabled`.

## 3. מופע עסקי חדש

1. העתק מ־`instances/velvet-factory/` או בנה מ־`presets/<id>.json`
2. צור ריפו GitHub ריק `VelvetOS — <Business>` / `velvetos-<slug>`
3. `PUSH=1 ./scripts/publish-instance.sh <id> <owner/repo>`
4. במופע: `./scripts/attach-core.sh`

## 4. אחרי שינוי בליבה

```
python3 scripts/velvetos.py core
python3 scripts/check-velvetos.py
python3 scripts/check-all.py
```
