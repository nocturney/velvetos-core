# vfinsights — קריאה אחרי פרסום

מושב: צמיחה. לא ממציאים מדד.

**מקור מועדף:** Instagram MCP קנוני (`adelaidasofia/instagram-mcp` · [`vfigos/CONNECT-IG.md`](../vfigos/CONNECT-IG.md)):

- `get_account_insights`
- `get_media_insights`
- `get_audience_insights`

אם Meta לא מחזירה מדד → «אין ספירה» / unavailable. לא ממציאים.  
גיבוי: הדבקת בעלים.  
**Metricool** = אופציונלי/לגאסי בלבד — לא נדרש לתפעול ולא קנוני לאנליטיקס.

חלון רגיל: 24 שעות אחרי `liveVerified`.  
מדדים מאומתים נכנסים ל־`packages/vfinsights/data/posts.csv` כשישים.  
`LEARNINGS.md` מתעדכן רק ממספרים שנמדדו בפועל.

## מומחה — Insights ingest

מודול: `expert-insights-ingest` · `experts/INSIGHTS-SNAPSHOT.md` · `templates/snapshot-ingest.md` · `@tracking-measurement-specialist`

קלט שבועי ל־`WEEKLY-REVENUE-PULSE.md` ול־Social Booster.

## כלי מדידה

`scripts/vf_insights_loop.py` — לופ מדידה→למידה סגור. פירוט: [`docs/AUTONOMY-TOOLS.md`](../../docs/AUTONOMY-TOOLS.md).

ייחוס הסתברותי: [`ATTRIBUTION.md`](ATTRIBUTION.md) — לא ממציאים המרה מוואטסאפ.
