# who / search

מקור: `search_graph` + `semantic_query`.  
אצלנו: איזה פק / `@slug` / כלי לעבודה, בלי לשפוך את המחסן.

## מתי

«מי מטפל ב…», «איזה פק», פנייה חדשה, בריף, כריכה, חשבונית.

## הרצה

```bash
python3 scripts/vfmem.py who "בריף בוקר"
python3 scripts/vfmem.py who inquiry
python3 scripts/vfmem.py search vfcost
```

## מה עושים עם התוצאה

1. קוראים את שורת ה־desk route.
2. מזכירים רק את ה־`@slug` הזה.
3. פותחים את הפק ואת הכלי שכתובים שם.
4. לא מפעילים מחסן (Godot / GIS / בריאות / סין) אלא אם המשתמש ביקש את ה־slug.

## אסור

₪ מומצא, Insights מומצא, שליחת ג׳ימייל או אינסטגרם.
