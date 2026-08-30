# vfgraft — איך מטמיעים

Graft בונה הבנה **פעם אחת** וכותב אותה כקבצי Markdown מקושרים. סוכן קורא צומת במקום לחקור את הריפו מחדש כל ריצה.

אצלנו אותו דפוס, בלי ה-CLI: מפת משרד ב-`packages/vfgraft/`. לא `@nanonets/graft`. לא MCP. לא מפתח ספק.

## למה לא ה-npm

1. Graft tree-sitter **מדלג על Markdown**. זה כמעט כל HQ.
2. `--deep` דורש מפתח. אין חשבון מודל שני.
3. הגרף שלהם gitignore — לא משותף בין Cloud Agents.
4. `vfe2b` כבר נועל סוכן-קידוד שני. Cursor הוא המשרד.

## מה כן (מ-Graft)

| Graft | אצלנו |
|---|---|
| `graft map` | [`MAP.md`](MAP.md) |
| `graft ask` | טבלת Ask ב-MAP → 2–3 צמתים |
| markdown nodes + `[[wikilinks]]` | [`graph/`](graph/) |
| typed verbs | `part_of` `depends_on` `uses` `produces` `validates` `configures` |
| `graft blast` | [`graph/blast.md`](graph/blast.md) |
| Notes survive regen | בלוק Notes בכל צומת |
| Sources + freshness | נתיבים אמיתיים; `check-vfgraft.py` בודק שהם קיימים |

## הרצה

1. קרא [`MAP.md`](MAP.md).
2. פתח רק את הצמתים של העבודה (בריף / פנייה / תוכן / blast).
3. לך למקור שכתוב בצומת. אל תמציא ₪ או Insights.
4. עצור לפני שליחה. Grok או אדם שולחים.

## בדיקה

```bash
python3 scripts/check-vfgraft.py
```

אין UI חי. העקביות היא מול `graph.json`, המניפסט, והנתיבים.
