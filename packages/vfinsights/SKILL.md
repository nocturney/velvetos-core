# vfinsights — קריאה אחרי פרסום + תמונת מצב יומית

מושב: צמיחה. לא ממציאים מדד.

**מקור מועדף:** Instagram MCP קנוני (`adelaidasofia/instagram-mcp` · [`vfigos/CONNECT-IG.md`](../vfigos/CONNECT-IG.md)):

- `account_info` / `get_profile` — followers + media count.
- `get_account_insights` — reach / profile views / total interactions ומה ש־Graph מחזיר בפועל.
- `list_media` — permalink + thumbnail/media URL של פריטים אחרונים.
- `get_media_insights` — reach / views / interactions / saved / shares / likes / comments לפי סוג המדיה ומה ש־Meta תומכת בו.
- `get_audience_insights` — רק כשיש צורך והחשבון עומד בסף הפרטיות של Meta.

אם Meta לא מחזירה מדד → «אין ספירה» / unavailable. לא ממציאים.  
גיבוי: הדבקת בעלים.  
**Metricool** = אופציונלי/לגאסי בלבד — לא נדרש לתפעול ולא קנוני לאנליטיקס.

## Morning Brief V6

בכל בריף 07:00 מבצעים probe חי — לא מסתמכים על `LEARNINGS.md` כדי לתאר את מצב העמוד הנוכחי.

כרטיס `Instagram · מצב העמוד` כולל כשזמין:
- followers עכשיו.
- account reach/profile views/interactions עם תקופת המדידה ש־Meta החזירה.
- 2–3 פריטי מדיה אחרונים/מייצגים עם thumbnail אמיתי וקישור ל־permalink.
- לכל פריט: סוג, timestamp, reach/views/interactions/saves/shares רק אם הוחזרו.
- מסקנה אחת קצרה בלבד אם היא נתמכת במספרים. מדגם קטן מסומן ככזה; אין הסקת trend מתצפית יחידה.

`thumbnail_url`/`media_url` שה־MCP מחזיר מותר לשימוש כתמונת preview בתוך הבריף. לא משנים ממנו סטטוס פרסום; `list_media` חי הוא ראיה לפריט live קיים בלבד.

## חלון אחרי פרסום

חלון רגיל: 24 שעות אחרי `liveVerified`.  
מדדים מאומתים נכנסים ל־`packages/vfinsights/data/posts.csv` כשישים.  
`LEARNINGS.md` מתעדכן רק ממספרים שנמדדו בפועל.

## מומחה — Insights ingest

מודול: `expert-insights-ingest` · `experts/INSIGHTS-SNAPSHOT.md` · `templates/snapshot-ingest.md` · `@tracking-measurement-specialist`

קלט שבועי ל־`WEEKLY-REVENUE-PULSE.md` ול־Social Booster.

## כלי מדידה

`scripts/vf_insights_loop.py` — לופ מדידה→למידה סגור. פירוט: [`docs/AUTONOMY-TOOLS.md`](../../docs/AUTONOMY-TOOLS.md).

ייחוס הסתברותי: [`ATTRIBUTION.md`](ATTRIBUTION.md) — לא ממציאים המרה מוואטסאפ.
