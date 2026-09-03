# רטרו ראשוני — catch-up לפני שהרוטינה היומית הייתה קיימת

מודול: `office-learning`.  
**פעם אחת** (או אחרי הפסקה ארוכה). אחר כך — רק `DAILY-RETRO.md` בכל סוף יום.

## מתי

- הרוטינה היומית עדיין לא רצה (כמו עכשיו, 2026-09-01)
- חזרה מחופשה / מעבר workspace
- מיזוג מ־Core לפרונט `velvetos-velvet-factory` בפעם הראשונה

## מקורות (לא שיחות Cursor שלא בגיט)

| מקור | מה שואבים |
|---|---|
| `CHANGELOG.md` | החלטות והטמעות לפי תאריך |
| `packages/vfharness/state/*.json` | משימות רב־שלביות, `next_step`, שערים |
| `packages/vfops/data/research.md` | בלוק 05 בבריף |
| `AGENTS.md` ANTI-PATTERNS | מה לא לחזור עליו |
| `constitution/` | חוקי שליחה, צינור, ₪ |
| `packages/vfresearch/LINKS.json` | קישורי השראה רשומים |
| בקשות בעלים בשיחה נוכחית | העדפות שלא היו בגיט |

**לא** ממציאים שיחות שלא נשמרו. חסר מקור → «לא ידוע עד עכשיו».

## צעדים (ראש צוות)

1. קרא `packages/vfops/data/ARTIFACT-INDEX.md` — איפה כל תוצר יושב.
2. עבור checkpoints ב־`vfharness/state/` — סמן `done` / `running` / פתוח.
3. סכם לפי **חמשת המושבים** + ארבעת המומחים (`expert-*`).
4. כתוב ל־`packages/vfops/data/owner-memory.md` תחת `## רטרו ראשוני (catch-up)`.
5. עדכן בלוק 05 ב־`data/research.md` אם יש הטמעה חדשה לבריף.
6. סמן ב־checkpoint: `packages/vfharness/state/initial-retro-2026-09-01.json` → `done`.

## פלט

- `owner-memory.md` מלא מספיק לפתיחת משמרת מחר
- רשימת «פתוח» לראש צוות (לא ממציאים ₪)
- מחרתיים: רק `DAILY-RETRO.md`

## פרונט Velvet Factory

ריפו `velvetos-velvet-factory` שואב את אותם קבצים מ־`vendor/velvetos-core` אחרי `attach-core.sh`.  
אין מנגנון נפרד — **אותו זיכרון, אותם checkpoints**.
