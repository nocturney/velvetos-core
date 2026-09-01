# Insights Snapshot — ingest מאומת

מודול: `expert-insights-ingest`.  
מושב: צמיחה + ראש צוות.

## מתי

- 24–48 שעות אחרי פרסום חשוב
- שבועי לפני `WEEKLY-REVENUE-PULSE`
- אחרי קמפיין / קרוסלה / ריל

## מקורות מותרים

1. צילום מסך / ייצוא IG Professional (בעלים מדביק)
2. Drive doc שהבעלים העלה
3. מספרים שהבעלים כתב במפורש בשיחה

**לא:** Treg · WebSearch למספרים · המצאה

## תהליך

1. בעלים ממלא `templates/snapshot-ingest.md` (או מדביק ב-Drive).
2. `@tracking-measurement-specialist` מעתיק ל־`sources/YYYY-MM-DD-ig-snapshot.md`.
3. `@analytics-reporter` מסכם — רק עובדות מהקובץ.
4. `@pipeline-analyst` מקשר ל־`ig_post_ref` בכרטיסי pipeline (אם יש פניות).
5. handoff ל־`@carousel-growth-engine` / `@growth-hacker` — מה לחזור עליו.

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
