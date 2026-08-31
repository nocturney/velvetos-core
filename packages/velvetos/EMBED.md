# velvetos — איך מטמיעים

ליבה + מודולים מוכנים מראש. מופע = עסק אחד לריפו.

## 1. זהות

- מוצר: **VelvetOS**
- הריפו הזה: **VelvetOS — Velvet Factory** (`INSTANCE.json`)
- ליבה מארחת זמנית כאן (`hostsCore: true`) עד פיצול `velvetos-core` — ראו `REPOS.md`

## 2. מודולים

הכל תחת `modules/` + `catalog.json`. המופע בוחר תת־קבוצה ב־`modulesEnabled`.  
Preset (`presets/`) = תבנית למופע חדש — לא יעד פעיל/כבוי בריפו הזה.

## 3. מופע עסקי חדש

1. ריפו חדש בשם `VelvetOS — <Business Name>` (או `velvetos-<slug>`).
2. Vendor / subtree של הליבה.
3. העתק preset רלוונטי → `instance/<id>.json` עם עובדות אמיתיות בלבד.
4. אל תפתח tenant שני ליד VF בריפו הזה.

## 4. אחרי שינוי

```
python3 scripts/velvetos.py instance
python3 scripts/velvetos.py modules
python3 scripts/check-velvetos.py
python3 scripts/check-all.py
```
