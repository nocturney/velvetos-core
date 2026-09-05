# strategic-compact embed · 2026-09-05

מושב: מחקר (`@research-synthesist`) → ראש צוות (`@workflow-architect` / vfharness)  
מקור: https://mcpmarket.com/tools/skills/strategic-context-compaction-1787987503518  
כינוי: strategic-compact / Strategic Context Compaction (Claude Code skill)

## תקציר (מה שקראנו)

סקיל ל-Claude Code שמציע `/compact` ידני בגבולות שלב (מחקר→תכנון→ביצוע→בדיקה), עם hooks על Edit/Write — במקום auto-compaction באמצע עבודה. טבלת החלטה: לדחוס במעברי שלב / אחרי דיבוג / אחרי גישה שנכשלה; **לא** באמצע ביצוע.

## פסיקה

`embed` של **טבלת גבול שלב בלבד** על `vfharness` (`context-thrift.md` + שורת Compaction ב-`EMBED.md`).  
**לא** התקנת הסקיל. **לא** `npx skills`. **לא** PreToolUse hooks. **לא** פקודת `/compact` — אצלנו דחיסה = עדכון checkpoint והמשך מ-(P, Σ, O).

## מה הוטמע

| קובץ | שינוי |
|---|---|
| `vfharness/playbooks/context-thrift.md` | § phase-boundary + טבלת מעברי שלב + איך דוחסים בלי `/compact` |
| `vfharness/EMBED.md` | Compaction מציין מתי / מתי לא + קישור לטבלה |
| `vfharness/playbooks/skillstate.md` | cross-ref phase-boundary |
| `vfe2b/DEER-FLOW-PATTERNS.md` | שורת Context compaction מעודכנת |
| `scripts/check-vfharness.py` | מחטי phase-boundary |
| `vfresearch/LINKS.json` | רישום strategic-compact |

## מה דולג

| מה | למה |
|---|---|
| התקנת הסקיל / Claude Code hooks | Cloud Agent ≠ Claude Code; `npx skills` אסור |
| ספירת Edit/Write כטריגר | אצלנו גבול שלב לוגי + checkpoint, לא מונה כלים |
| פקודת `/compact` | DeerFlow/SKILLSTATE כבר מגדירים סיכום ל-Σ על הדיסק |

## קשר לדפוסים קיימים

- `context-thrift.md` — CCR על פלט כלים + עכשיו phase-boundary
- `skillstate.md` — Σ על הדיסק, לא replay
- DeerFlow `/compact` embed — אותה משפחה; הטבלה מוסיפה *מתי*

## בלוק 05

השראה יומית — הוטמע phase-boundary compaction ב־`vfharness` (בלי התקנת strategic-compact)
