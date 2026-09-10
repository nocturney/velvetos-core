# Learnings — closed measurement loop

Measured 1 of 1 posts. 0 still have no real number (excluded from ranking, not guessed).

Source preference: Instagram MCP verified Insights → `scripts/vf_insights_ingest.py` → `data/posts.csv`.
Missing metric = אין ספירה / blank — never invent, never coerce unavailable → 0.
Explicit CSV `0` is preserved as measured zero (MCP returned 0); blank cell stays unknown.
The `source` column proves MCP origin when set to `instagram_mcp` (vs owner paste / blank).

## Caption/format style ranked by engagement rate

| style | posts | avg reach | avg engagement rate |
|---|---|---|---|
| תהליך-קצר | 1 | 187.0 | 0.0 |

**Recommendation:** insufficient evidence — no format/style winner yet (need ≥3 measured posts; have 1). Ranking table kept for transparency.
