# vfgraft — Graft office graph

מפת [trailhq/Graft](https://github.com/trailhq/Graft) על משרד Velvet Factory.

Graft פותר את זה: כל סוכן מתחיל עיוור, חוקר מחדש, וזורק את התמונה בסוף הסשן. אצלנו זה כואב יותר — 273 מומחי Agency + עשרות פקים.

לא מתקינים את ה-CLI. מטמיעים את **הדפוס**: גרף Markdown שמור בגיט, שסוכן קורא לפני שהוא עושה grep למחסן.

## קבצים

| קובץ | תפקיד |
|---|---|
| [`MAP.md`](MAP.md) | מבט ראשון (כמו `graft map`) |
| [`graph/`](graph/) | צמתים + קישורים |
| [`graph.json`](graph.json) | רשימה למכונה |
| [`EMBED.md`](EMBED.md) | איך רצים |
| [`LOCK.md`](LOCK.md) | למה בלי npm |
| [`docs/GRAFT.md`](../../docs/GRAFT.md) | כתיבה |

## איך מפעילים

```
@vfgraft map
@vfgraft blast
@vfgraft inquiry
```

או פותחים `MAP.md` ועוקבים אחרי שני צמתים.

`python3 scripts/check-vfgraft.py` — צפי: `OK nodes=12 links sources packs`.
