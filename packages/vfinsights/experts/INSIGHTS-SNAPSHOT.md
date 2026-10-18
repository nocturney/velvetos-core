# Insights Snapshot — ingest מאומת

מודול: `expert-insights-ingest`.  
מושב: צמיחה + ראש צוות.

## מתי

- 24–48 שעות אחרי פרסום חשוב
- שבועי לפני `WEEKLY-REVENUE-PULSE`
- אחרי קמפיין / קרוסלה / ריל

## מקורות מותרים — לפי עדיפות

1. Instagram MCP קנוני ומאומת (`adelaidasofia/instagram-mcp`): `get_account_insights`, `get_media_insights`, `list_media`, ו־account/profile reads לפי מה ש־Meta מחזירה בפועל.
2. צילום מסך / ייצוא IG Professional שהבעלים מדביק — fallback כש־MCP חסום/לא מחזיר את המדד.
3. Drive doc שהבעלים העלה.
4. מספרים שהבעלים כתב במפורש בשיחה.

**לא:** Treg · WebSearch למספרי החשבון · המצאה. מדד חסר/לא נתמך = «אין ספירה».

## תהליך

1. נסה קודם read חי דרך Instagram MCP על החשבון/המדיה הרלוונטיים; שמור רק שדות שהספק החזיר בפועל.
2. אם ה־MCP חסום או שהמדד לא נתמך, עבור ל־owner paste / Drive snapshot בלי להמציא פערים.
3. `@tracking-measurement-specialist` שומר provenance ב־`sources/YYYY-MM-DD-ig-snapshot.md` או בקלט המדידה הקנוני.
4. `@analytics-reporter` מסכם — רק עובדות מהמקור המאומת.
5. `@pipeline-analyst` מקשר ל־`ig_post_ref` בכרטיסי pipeline (אם יש פניות).
6. handoff ל־`@carousel-growth-engine` / `@growth-hacker` — מה לחזור עליו.

## פלט

```markdown
## snapshot · YYYY-MM-DD
- posts_measured: N
- top_format: reel|carousel|post (אם יש מקור)
- verified_metrics: { post_ref: { reach, saves, … } }  # רק מה שהודבק
- gaps: אין ספירה ל…
- action_next_week: משפט אחד
```

## אסור

להמציא reach / engagement / saves / track names
