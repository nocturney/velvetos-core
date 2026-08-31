# VelvetOS

**VelvetOS** = ניהול עסק + סושיאל אוטונומי על Cursor.

| | |
|---|---|
| הריפו הזה | **VelvetOS — Velvet Factory** |
| ליבה | `packages/velvetos/` (מארחת מודולים; פיצול עתידי ל־`velvetos-core`) |
| מודולים | תמיד בדיסק תחת `modules/` — לא יעדים פעילים/כבויים |
| Presets | תבניות למופעי עתיד (יופי multi-IG, חוות דעת…) |
| מופעים חדשים | ריפואים נפרדים `VelvetOS — <Business Name>` ששואבים מהליבה |

## מבנה

| נתיב | תפקיד |
|---|---|
| `INSTANCE.json` | זהות המופע החי |
| `instance/velvet-factory.json` | עובדות VF + `modulesEnabled` |
| `modules/` | קטלוג יכולות מלא |
| `presets/` | הרכבים מומלצים לריפואים עתידיים |
| `REPOS.md` | ליבה מול מופעים |

## תאימות VF

צינור פנייה→…→איסוף, `@velvets_cloud`, וואטסאפ `050-2517000`, איסוף שדרות — ללא שינוי.

## CLI

```bash
python3 scripts/velvetos.py instance
python3 scripts/velvetos.py modules
python3 scripts/velvetos.py presets
python3 scripts/check-velvetos.py
```
