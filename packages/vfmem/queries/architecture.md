# architecture / schema

מקור: `get_architecture` + `get_graph_schema` ב־[codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp).  
אצלנו: מפה אחת של המשרד, לא AST של קוד.

## מתי

סוכן חדש, בריף בוקר, או לפני שקוראים הרבה פקים.

## הרצה

```bash
python3 scripts/vfmem.py architecture
python3 scripts/vfmem.py schema
```

`--json` אם צריך פלט למכונה.

## מה יוצא

מושבים, פקים, כלי שולחן, צינור, פקים בלי מושב (מחקר / HQ-native), מספר חוקים.

## אסור

- לקרוא 273 כללי Agency אחרי המפה
- להמציא מושב שישי בשביל `vfmem`
- להפעיל UI על פורט 9749
