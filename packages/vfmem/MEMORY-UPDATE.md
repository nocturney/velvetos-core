# עדכון זיכרון משותף (vfmem)

מודול: `office-learning`.  
הזיכרון המשותף = מה שכל הסוכנים יורשים מחר בלי לשאול שוב.

## שכבות

| שכבה | מיקום | מה נכנס |
|---|---|---|
| חוקים | `AGENTS.md`, `constitution/` | החלטות משרד, ANTI-PATTERNS |
| מפת משרד | `vfgraft/MAP.md`, `vfmem` routes | ניתוב job → pack → slug |
| זיכרון בעלים | `vfops/data/owner-memory.md` | העדפות, טון, עובדות חוזרות |
| זיכרון instance | `vfops/data/owner-memory-<instance-id>.md` | IG handle, SKU, טון לפי משרד frontend |
| משימה | `vfharness/state/*.json` | מה קרה ב-job ספציפי (L1 traces) |

## L1 / L2 / L3 (דפוס DeepTutor)

מקור השראה: [HKUDS/DeepTutor](https://github.com/HKUDS/DeepTutor) — זיכרון בשלוש שכבות. פירוט: `vfops/hq/MASTERY-MEMORY.md`.

| שכבה | אצלנו | כלל |
|---|---|---|
| L1 | checkpoint / תצפית אחרונה | עקבות משימה — לא שיחה שלמה |
| L2 | `owner-memory.md` | סיכום עמיד למחר — שורה אחת = עובדה אחת |
| L3 | `AGENTS.md` / פלייבוק / ADR | סינתזה לחוק — רק אחרי חזרתיות או אישור אדם |

Mastery gate לפני «למדנו / סיימנו»: אימות טרי (`verification-before-claim.md`), לא תחושה.

## מתי לכתוב

- סוף יום — `DAILY-RETRO.md`
- **רטרו ראשוני** — `INITIAL-RETRO.md` (פעם אחת או אחרי הפסקה ארוכה)
- אחרי משימה ארוכה (5+ tool calls) — checkpoint
- כשהבעלים אומר במפורש «תזכרו ש…»

## משמעת זיכרון (recall / save / close)

דפוס מ־[agent-memory-discipline](https://buildwithclaude.com/skill/agent-memory-discipline) (buildwithclaude, 2026-09-03). בלי MCP זיכרון חיצוני — הקבצים למעלה הם ה־backend.

### Recall לפני פעולה

לקרוא זיכרון **לפני** (לא אחרי):

- עבודה על פרויקט/job שכבר נגענו בו
- בחירת כלי, פק, או דפוס («איך עושים אצלנו»)
- כל ניסוח של הבעלים: «שוב», «כמו בפעם הקודמת», «כמו שסיכמנו»

לא לעשות recall לשאלת עובדה חד־פעמית שכבר מלאה בהודעה. שאילתה אחת ממוקדת; אם ריק — שאילתה רחבה אחת ואז ממשיכים בלי לולאה.

כלי: `python3 scripts/vfmem.py who "<job>"` · `owner-memory.md` · checkpoint של ה־task.

### Save אחרי החלטה

לכתוב כשקרה אחד מאלה:

- **החלטה** שתחזיק שבוע+ («אנחנו על pnpm», «אין Print מ־HQ»)
- **תיקון** מהבעלים (האות החזק ביותר)
- **כישלון** + למה נכשל
- העדפה או עובדת סביבה שהתגלתה בקושי (פורט, דגל, שירות שחייב לרוץ)

לא לשמור: תוכן קבצים שאפשר לקרוא שוב, מצב זמני, secrets, שיחה שלמה. **שורה אחת = עובדה אחת.**

### Close במקום delete

כשמשהו משתנה — הרשומה הישנה לא «טעות», היא **נסגרת** (תוקף עד תאריך). מחיקה מוחקת את ההסבר לקוד/נוהל ישן. סתירה בין שתי רשומות → מציגים את שתיהן עם תאריכים, לא בוחרים בשקט.

### Evidence ≠ Policy

תצפית אחת (evidence) לא הופכת לחוק שולחן (policy) בלי אישור אדם / ADR / חזרתיות מוכחת. אל תקדם observation ל־`AGENTS.md` לבד.

## Common Ground — שכבות ביטחון להנחות

דפוס מ־[Jeffallan/claude-skills Common Ground](https://github.com/Jeffallan/claude-skills/blob/main/docs/COMMON_GROUND.md) (mcpmarket fullstack-dev-skills-plugin, 2026-09-05). בלי `/common-ground` slash ו־בלי plugin Claude Code — הקבצים למעלה הם ה־backend.

כשסוכן מניח משהו על הסטודיו / הפרויקט, לסווג לפני שממשיכים:

| שכבה | דין | דוגמה אצלנו |
|---|---|---|
| **ESTABLISHED** | הנחה מאושרת — לא לערער בלי סתירה מפורשת | איסוף שדרות · וואטסאפ `050-2517000` · אין Print מ־HQ |
| **WORKING** | ברירת מחדל — לציין כשמסתמכים | Canva קודם ל־IG · 3DAI לקונספט לפני Blender מקומי |
| **OPEN** | לשאול לפני שממשיכים | ₪ חסר · Insights חסר · מודל בלי `vlicense` |

מפה לשכבות הזיכרון: ESTABLISHED → חוקים/`owner-memory` · WORKING → checkpoint / brief · OPEN → `decision_gate` או שאלה לראש צוות. לא קובץ `~/.claude/common-ground/` נפרד.

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
- התקנת MCP זיכרון hosted / binary במקום הקבצים האלה (context-memory, DeusData C binary, וכו׳)
