# עדכון זיכרון משותף (vfmem)

מודול: `office-learning`.  
הזיכרון המשותף = מה שכל הסוכנים יורשים מחר בלי לשאול שוב.

## שכבות

| שכבה | מיקום | מה נכנס |
|---|---|---|
| חוקים | `AGENTS.md`, `constitution/` | החלטות משרד, ANTI-PATTERNS |
| מפת משרד | `vfgraft/MAP.md`, `vfmem` routes | ניתוב job → pack → slug |
| זיכרון בעלים | `vfops/data/owner-memory.md` | העדפות, טון, עובדות חוזרות |
| משימה | `vfharness/state/*.json` | מה קרה ב-job ספציפי |

## מתי לכתוב

- סוף יום — `DAILY-RETRO.md`
- **רטרו ראשוני** — `INITIAL-RETRO.md` (פעם אחת או אחרי הפסקה ארוכה)
- אחרי משימה ארוכה (5+ tool calls) — checkpoint
- כשהבעלים אומר במפורש «תזכרו ש…»

## פורמט שורה ב־owner-memory.md

```markdown
### YYYY-MM-DD
- **מושב:** growth | studio | lead | …
- **למדנו:** משפט אחד — עובדה או העדפה
- **מחר:** פעולה אחת (אופציונלי)
- **מקור:** שיחה / מייל / רצפה (לא המצאה)
```

## מתי לעדכן routes (catalog.json)

רק אם job חדש חוזר 3+ פעמים בשבוע:

1. הוסף route ב־`packages/vfmem/catalog.json`
2. עדכן שורה ב־`velvet-factory-desk.mdc` אם צריך
3. הרץ `python3 scripts/check-vfmem.py`

## מתי לעדכן vfgraft

שינוי חוק / כלי / pack חדש → node ב־`graph.json` + `MAP.md` (2–3 nodes, לא מגילה).

## בדיקה

```bash
python3 scripts/vfmem.py who "<job>"
python3 scripts/vfmem.py architecture
```

## אסור

- secrets בגיט
- ₪ / Insights מומצאים
- העתקת שיחה שלמה — רק תמצית
